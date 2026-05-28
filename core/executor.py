import threading


class DataFetchExecutor:
    def __init__(
        self,
        window,
        progress_manager,
        graph_client,
        teams_client,
        token_manager,
        graph_apis,
        logger
    ):
        self.log = logger
        self.window = window
        self.progress = progress_manager
        self.graph = graph_client
        self.teams = teams_client
        self.tokens = token_manager
        self.graph_apis = graph_apis
        self.cancel_requested = False

    # --------------------------------------------------
    # Public API – called from UI
    # --------------------------------------------------
    def run(
        self,
        selected_apis,
        api_vars,
        refresh_tokens,
        input_provider,
        on_complete,
        on_error
    ):
        self.cancel_requested = False
        worker = threading.Thread(
            target=self._worker,
            daemon=True,
            args=(
                selected_apis,
                api_vars,
                refresh_tokens,
                input_provider,
                on_complete,
                on_error
            )
        )
        worker.start()

    # --------------------------------------------------
    # Worker thread (NO Tk calls directly)
    # --------------------------------------------------
    def _worker(
            self,
            selected_apis,
            api_vars,
            refresh_tokens,
            input_provider,
            on_complete,
            on_error
    ):
        self.log.info("Execution started")
        cancelled = False

        try:
            if self.tokens.is_token_expired():
                raise RuntimeError("Access token expired")

            any_api_fetched = False

            for api_name in selected_apis:
                self.log.info(f"Processing API: {api_name}")

                # ---------- GLOBAL CANCEL CHECK ----------
                if self.cancel_requested:
                    self.log.warning("Execution cancelled by user")
                    cancelled = True

                    # clear remaining selected APIs
                    for name, var in api_vars.items():
                        if var.get():
                            self._ui_clear_checkbox(api_vars, name)

                    break

                api = self.graph_apis.get(api_name, {})

                # ---------- Teams PowerShell ----------
                if api.get("type") == "teams_powershell":

                    self._ui_progress(
                        "Preparing Teams data fetch…", delay=0.1
                    )

                    self.teams.fetch_queues_and_aa_with_fallback(
                        refresh_tokens,
                        self
                    )

                    if self.cancel_requested:
                        self.log.warning("Execution cancelled by user")
                        cancelled = True

                        # clear remaining selected APIs
                        for name, var in api_vars.items():
                            if var.get():
                                self._ui_clear_checkbox(api_vars, name)

                        break

                    self._ui_clear_checkbox(api_vars, api_name)
                    any_api_fetched = True
                    continue
                if api.get("type") == "teams_powershell_ddi":
                    self._ui_progress(
                        "Fetching Teams DDI numbers...",
                        delay=0.1
                    )

                    self.teams.fetch_ddis()

                    self._ui_clear_checkbox(api_vars, api_name)

                    any_api_fetched = True
                    continue
                # ---------- Graph API ----------
                user_inputs = self._ui_call_and_wait(
                    input_provider,
                    api_name
                )

                if user_inputs is None:
                    self._ui_clear_checkbox(api_vars, api_name)
                    continue

                self._ui_progress(f"Fetching {api_name}…")

                self.graph.call_api(api_name, user_inputs, self)

                if self.cancel_requested:
                    self.log.warning("Execution cancelled by user")
                    cancelled = True

                    # clear remaining selected APIs
                    for name, var in api_vars.items():
                        if var.get():
                            self._ui_clear_checkbox(api_vars, name)

                    break

                self._ui_clear_checkbox(api_vars, api_name)
                any_api_fetched = True

            # ---------- FINAL STATE HANDLING ----------

            if cancelled:
                self.log.warning("Execution cancelled by user")
                from tkinter import messagebox

                self._ui_callback(
                    lambda: self._handle_cancel()
                )

            elif any_api_fetched:
                self.log.info("Execution completed successfully")
                self._ui_callback(on_complete)

        except Exception as e:
            self.log.error(str(e))
            self._ui_callback(on_error, e)

        finally:
            self._ui_callback(self.progress.stop)

    # --------------------------------------------------
    # UI-safe helpers
    # --------------------------------------------------
    def _ui_progress(self, message, delay=0.0):
        self.window.after(
            0,
            lambda: self.progress.update(message, delay)
        )

    def _ui_clear_checkbox(self, api_vars, api_name):
        self.window.after(
            0,
            lambda: api_vars[api_name].set(False)
        )

    def _ui_callback(self, fn, *args):
        self.window.after(0, lambda: fn(*args))

    def cancel(self):
        self.cancel_requested = True

    def _handle_cancel(self):
        from tkinter import messagebox

        choice = messagebox.askyesno(
            "Cancelled",
            "Operation cancelled by user.\n\nDo you want to continue?"
        )

        if not choice:
            # delegate closing to UI safely
            self._ui_callback(self._request_app_close)
        else:
            # user wants to continue → do nothing
            pass

    def _request_app_close(self):
        try:
            self.window.quit()
        except:
            pass

    def _ui_call_and_wait(self, func, *args):
        import queue

        q = queue.Queue()

        def wrapper():
            result = func(*args)
            q.put(result)

        self.window.after(0, wrapper)
        return q.get()