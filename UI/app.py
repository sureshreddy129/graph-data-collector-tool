from tkinter import *
from tkinter import ttk, messagebox

from DB.db_manager import DBManager
from API.graph_client import GraphClient
from API.teams_client import TeamsClient
from API.token_manager import TokenManager
from UI.progress import ProgressManager
from core.executor import DataFetchExecutor
from utils.logger import ToolLogger
import json
from utils.path_helper import resource_path

config_path = resource_path("config/db_connection.json")

with open(config_path) as f:
    config = json.load(f)

PLATFORMS = config["Platforms"]
print(PLATFORMS)

#PLATFORMS = ["UK", "Connels","US", "AU","CallTower_US"]


class GraphDataCollectorApp:

    def __init__(self):
        self.log = ToolLogger()
        self.log.info("Application started")
        self.window = Tk()
        self.window.withdraw()

        messagebox.showinfo(
            "VPN Required",
            "Please ensure you are connected to Tollring VPN before using this application.\n\n"
            "The application will not work without VPN access."
        )

        self.window.deiconify()
        self.window.title("Graph Data Collector")
        self.window.config(padx=40, pady=30)
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Managers
        self.db = DBManager()
        self.tokens = TokenManager()
        self.progress = ProgressManager(self.window)

        # Grid
        self.window.grid_columnconfigure(0, minsize=180)
        self.window.grid_columnconfigure(1, minsize=350)

        self._build_platform_ui()

    # -------------------------------------------------
    # UI startup
    # -------------------------------------------------
    def run(self):
        self.cancel_requested = False
        self.window.mainloop()

    def _build_platform_ui(self):
        Label(self.window, text="Select Platform:")\
            .grid(row=0, column=0, sticky="e", pady=5)

        self.platform_var = StringVar()
        ttk.Combobox(
            self.window,
            textvariable=self.platform_var,
            values=PLATFORMS,
            state="readonly",
            width=30
        ).grid(row=0, column=1, sticky="w")

        Button(
            self.window,
            text="Connect to DB",
            command=self.connect_db
        ).grid(row=1, column=1, sticky="w", pady=10)

    # -------------------------------------------------
    # DB + Tenant flow
    # -------------------------------------------------
    def connect_db(self):
        platform = self.platform_var.get()
        if not platform:
            messagebox.showwarning("Input Required", "Please select a platform")
            return

        try:
            self.db.connect(platform)
            messagebox.showinfo("Success", f"Database connected ({platform})")
            self.log.info(f"Connected to platform database: {platform}")
            self._build_customer_ui()
        except Exception as e:
            messagebox.showerror("DB Connection Failed", str(e))

    def _build_customer_ui(self):
        self.customer_entry = Entry(self.window, width=45)
        self.customer_entry.grid(row=2, column=1, sticky="w", pady=5)
        self.customer_entry.bind("<Return>", lambda e: self.search_customer())

        Label(self.window, text="Enter Customer Name:")\
            .grid(row=2, column=0, sticky="e", pady=5)

        Button(
            self.window,
            text="Search Customer",
            command=self.search_customer
        ).grid(row=3, column=1, sticky="w", pady=5)

        self._build_results_table()

    def _build_results_table(self):
        self.tree = ttk.Treeview(
            self.window,
            columns=("TenantId", "TenantName", "CustomerName", "TenantGUID"),
            show="headings",
            height=8
        )

        # Headings
        self.tree.heading("TenantId", text="Tenant ID")
        self.tree.heading("TenantName", text="Tenant Name")
        self.tree.heading("CustomerName", text="Customer Name")
        self.tree.heading("TenantGUID", text="Tenant GUID")

        # Column widths (RESTORED)
        self.tree.column("TenantId", width=90, anchor="center")
        self.tree.column("TenantName", width=160)
        self.tree.column("CustomerName", width=180)
        self.tree.column("TenantGUID", width=300)

        self.tree.bind("<<TreeviewSelect>>", self.on_tenant_select)

        self.tree.grid(
            row=4,
            column=0,
            columnspan=2,
            sticky="nsew",
            pady=10
        )

        # Scrollbar (RESTORED)
        scrollbar = ttk.Scrollbar(
            self.window,
            orient="vertical",
            command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=4, column=2, sticky="ns")

    def search_customer(self):
        name = self.customer_entry.get().strip()
        self.log.info(f"Searching customer: {name}")
        if not name:
            return

        try:
            rows = self.db.search_customer(name)
            self.tree.delete(*self.tree.get_children())
            self.log.info(f"{len(rows)} tenants found for search: {name}")
            for r in rows:
                print(r)
                self.tree.insert("", END, values=(r.TenantId, r.TenantName, r.CustomerName, r.TenantGuid))

        except Exception as e:
            messagebox.showerror("Query Error", str(e))

    def on_tenant_select(self, _):
        Button(
            self.window,
            text="Proceed with Selected Tenant",
            command=self.proceed_with_tenant
        ).grid(row=5, column=1, sticky="w", pady=10)

    def proceed_with_tenant(self):
        selected = self.tree.selection()
        if not selected:
            return

        (
            self.tenant_id,
            self.tenant_name,
            self.customer_name,
            self.tenant_guid
        ) = self.tree.item(selected[0], "values")
        self.log.info(
            f"Tenant selected | "
            f"TenantID={self.tenant_id} | "
            f"TenantName={self.tenant_name} | "
            f"Customer={self.customer_name}"
        )

        if not messagebox.askyesno("Confirm Tenant", self.tenant_name):
            return

        self.fetch_refresh_token()

    # -------------------------------------------------
    # Token + Executor setup
    # -------------------------------------------------
    def fetch_refresh_token(self):
        try:
            self.refresh_tokens = self.db.get_refresh_tokens(self.tenant_id)
            self.log.info(
                f"{len(self.refresh_tokens)} refresh tokens fetched for tenant {self.tenant_name}"
            )
            if not self.refresh_tokens:
                self.log.warning(
                    f"No active refresh tokens found for tenant {self.tenant_name}"
                )
                raise RuntimeError("No active refresh tokens found")

            messagebox.showinfo(
                "Token Retrieved",
                f"{len(self.refresh_tokens)} refresh token(s) retrieved successfully.\n"
                "Proceeding to access token generation."
            )

            token, expiry = self.tokens.generate_app_token(
                self.tenant_guid,
                self.refresh_tokens[0]
            )

            messagebox.showinfo(
                "Access Token Generated",
                f"Access token generated successfully.\n\n"
                f"Token expiry time:\n{expiry}\n\n"
                "You can now fetch Graph data."
            )
            self.log.info(
                f"Access token generated successfully | "
                f"Expiry UTC: {expiry}"
            )

            self._load_graph_apis()
            self._build_api_ui()
            self._init_clients_and_executor()

        except Exception as e:
            self.log.error(f"Access token generation failed: {str(e)}")
            messagebox.showerror("Token Error", str(e))


    def _load_graph_apis(self):
        # graph_apis_path = resource_path("config/graph_apis.json")
        # with open(graph_apis_path) as f:
        #     self.graph_apis = json.load(f)
        try:
            path = resource_path("Config/graph_apis.json")
            print("Loading graph APIs from:", path)

            with open(path, "r", encoding="utf-8") as f:
                self.graph_apis = json.load(f)

            print(self.graph_apis.keys())

        except Exception as e:
            messagebox.showerror(
                "Config Error",
                f"Failed to load graph_apis.json\n{e}"
            )
            self.graph_apis = {}

    def _init_clients_and_executor(self):
        self.graph_client = GraphClient(
            token_manager=self.tokens,
            graph_apis=self.graph_apis,
            tenant_name=self.tenant_name,
            progress_cb=self.thread_safe_progress,
            logger =self.log
        )

        self.teams_client = TeamsClient(
            token_manager=self.tokens,
            tenant_name=self.tenant_name,
            progress_cb=self.thread_safe_progress,
            logger=self.log
        )

        self.executor = DataFetchExecutor(
            window=self.window,
            progress_manager=self.progress,
            graph_client=self.graph_client,
            teams_client=self.teams_client,
            token_manager=self.tokens,
            graph_apis=self.graph_apis,
            logger=self.log
        )

    # -------------------------------------------------
    # API selection + execution
    # -------------------------------------------------
    def _build_api_ui(self):
        self.api_vars = {}

        Label(self.window, text="Select data to fetch:") \
            .grid(row=9, column=0, sticky="ne", pady=5)

        # ---- Scrollable container (RESTORED) ----
        container = Frame(self.window)
        container.grid(row=9, column=1, sticky="nsew")

        canvas = Canvas(container, width=350, height=200)
        scrollbar = Scrollbar(container, orient="vertical", command=canvas.yview)

        self.api_frame = Frame(canvas)

        self.api_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.api_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # ---- API checkboxes (unchanged logic) ----
        for api_name in self.graph_apis.keys():
            var = BooleanVar()
            chk = Checkbutton(self.api_frame, text=api_name, variable=var)
            chk.pack(anchor="w")
            self.api_vars[api_name] = var

        Button(
            self.window,
            text="Fetch Selected Data",
            command=self.fetch_selected_data
        ).grid(row=10, column=1, sticky="w", pady=10)
        Button(
            self.window,
            text="Cancel",
            command=self.cancel_execution,
            bg="#ff4d4d"
        ).grid(row=10, column=1, sticky="e", padx=10)

    def cancel_execution(self):
        if self.executor:
            self.executor.cancel()
            self.progress.update("Cancelling operation...")

    def fetch_selected_data(self):
        if self.tokens.is_token_expired():
            choice = messagebox.askyesno(
                "Token Expired",
                "Access token has expired.\n\nDo you want to generate a new token?"
            )

            if not choice:
                return

            try:
                token, expiry = self.tokens.generate_app_token(
                    self.tenant_guid,
                    self.refresh_tokens[0]
                )

                messagebox.showinfo(
                    "Token Refreshed",
                    f"New access token generated.\n\nExpires at:\n{expiry}"
                )
            except Exception as e:
                messagebox.showerror("Token Error", str(e))
                return

        selected = [k for k, v in self.api_vars.items() if v.get()]
        if not selected:
            return

        self.progress.start("Starting data fetch…")
        self.log.info(
            f"Execution started for APIs: {', '.join(selected)}"
        )
        self.executor.run(
            selected,
            self.api_vars,
            self.refresh_tokens,
            self.prompt_for_inputs,
            self.on_fetch_complete,
            self.on_fetch_error
        )

    def on_fetch_complete(self):
        self.progress.stop("Data fetched successfully.")

        choice = messagebox.askyesno(
            "Completed",
            "Data fetched successfully.\n\nDo you want to continue?"
        )

        if not choice:
            self.cleanup_and_exit()

    def on_fetch_error(self, error):
        self.progress.stop()
        messagebox.showerror("Error", str(error))

    # -------------------------------------------------
    # Helpers
    # -------------------------------------------------
    def prompt_for_inputs(self, api_name):
        api = self.graph_apis[api_name]
        inputs = api.get("inputs", [])

        # No inputs required → proceed
        if not inputs:

            return {}

        while True:
            dialog = Toplevel(self.window)
            dialog.title(f"{api_name} Parameters")
            dialog.grab_set()

            entries = {}
            result = {"status": None, "data": None}

            for i, field in enumerate(inputs):
                Label(dialog, text=field["label"]) \
                    .grid(row=i, column=0, padx=10, pady=5, sticky="e")

                ent = Entry(dialog, width=40)  # ✅ restored width
                ent.grid(row=i, column=1, padx=10, pady=5)
                entries[field["name"]] = ent

            def submit():
                data = {}
                for key, ent in entries.items():
                    val = ent.get().strip()
                    if not val:
                        messagebox.showwarning(
                            "Input Required",
                            f"{key} is required"
                        )
                        return
                    data[key] = val

                result["status"] = "ok"
                result["data"] = data
                dialog.destroy()

            def on_close():
                dialog.destroy()
                result["status"] = "cancel"

            Button(
                dialog,
                text="Continue",
                command=submit
            ).grid(row=len(inputs), column=1, pady=10, sticky="e")

            dialog.protocol("WM_DELETE_WINDOW", on_close)
            self.window.wait_window(dialog)

            # ---------- Decision handling ----------
            if result["status"] == "ok":
                return result["data"]

            # User clicked ❌
            choice = messagebox.askyesno(
                "Cancelled",
                f"{api_name} input was cancelled.\n\n"
                "Do you want to continue with this API?"
            )

            if choice:
                continue  # 🔁 reopen input dialog
            else:
                # ❌ Skip this API completely
                self.api_vars[api_name].set(False)
                return None

    def thread_safe_progress(self, message, delay=0.0):
        self.window.after(0, lambda: self.progress.update(message, delay))

    def on_closing(self):
        self.db.close()
        self.window.destroy()

    def cleanup_and_exit(self):
        self.on_closing()

    def cancel_execution(self):

        if not self.executor:
            return

        if self.executor.cancel_requested:
            self.log.warning("User requested cancellation")
            return  # already cancelling

        self.executor.cancel()
        self.progress.update("Cancelling operation...")