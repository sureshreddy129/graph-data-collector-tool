import os
import subprocess

import sys
from utils.path_helper import resource_path


class TeamsClient:
    def __init__(self, token_manager, tenant_name, progress_cb=None, logger=None):
        """
        token_manager : TokenManager instance
        tenant_name   : used for output folder
        progress_cb   : optional callback for UI progress updates
        """

        self.tokens = token_manager
        self.tenant_name = tenant_name
        self.progress_cb = progress_cb
        self.log = logger

    # --------------------------------------------------
    # Fetch Teams Call Queues & Auto Attendants
    # --------------------------------------------------
    def fetch_queues_and_aa_with_fallback(self, refresh_tokens, executor):
        last_permission_error = None
        self.executor = executor
        for idx, refresh_token in enumerate(refresh_tokens, start=1):
            if self.log:
                self.log.info(f"Trying Teams fetch using refresh token {idx}")

            if self.executor.cancel_requested:
                if self.progress_cb:
                    self.progress_cb("Operation cancelled by user.")
                return

            if not refresh_token:
                if self.progress_cb:
                    self.progress_cb(f"Skipping empty refresh token ({idx})")
                continue

            self.progress_cb(
                f"Trying Teams access using user token {idx} of {len(refresh_tokens)}…",
                delay = 0.45
            )

            # Switch refresh token
            self.tokens.set_refresh_token(refresh_token)

            # ---- Get delegated tokens ----
            if self.progress_cb:
                self.progress_cb("Getting Graph token…")
            if self.executor.cancel_requested:

                return
            graph_token = self.tokens.get_graph_token_from_refresh()

            if self.progress_cb:
                self.progress_cb("Getting Teams token…")

            if self.executor.cancel_requested:

                return
            teams_token = self.tokens.get_teams_token_from_refresh()

            if self.progress_cb:
                self.progress_cb("Connecting to Microsoft Teams…")

            output_dir = os.path.join("output", self.tenant_name)
            os.makedirs(output_dir, exist_ok=True)
            ps_script = resource_path("powershell/fetch_teams_queues_aa.ps1")
            cmd = [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy", "Bypass",
                "-File",ps_script ,
                "-GraphToken", graph_token,
                "-TeamsToken", teams_token,
                "-OutputPath", output_dir
            ]

            # 🔥 Capture output — THIS IS THE FIX
            if self.executor.cancel_requested:

                if self.progress_cb:
                    self.progress_cb("Cancelling Teams fetch...")
                return
            creation_flags = 0
            startupinfo = None

            # Hide PowerShell window in Windows
            if sys.platform == "win32":
                creation_flags = subprocess.CREATE_NO_WINDOW
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            if self.progress_cb:
                self.progress_cb("Fetching Auto Attendants and Call Queues…")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                creationflags=creation_flags,
                startupinfo=startupinfo
            )

            if self.log:
                self.log.info(result.stdout)

            if result.returncode != 0:
                if self.log:
                    self.log.error(result.stderr)
                raise RuntimeError("Teams PowerShell execution failed")
            if self.executor.cancel_requested:
                self.log.warning("Execution cancelled by user")
                return

            combined_output = (result.stdout or "") + (result.stderr or "")

            # ---- Detect permission failure explicitly ----
            if "Access Denied" in combined_output or "Forbidden" in combined_output:
                last_permission_error = combined_output
                self.log.warning("Teams permission denied — trying next token")
                self.progress_cb(
                    "User lacks Teams permissions, trying next available user…",
                    delay = 0.45
                )

                continue  # 🔁 TRY NEXT REFRESH TOKEN

            # ---- Validate actual data presence ----
            queues_file = os.path.join(output_dir, "CallQueues.json")
            aa_file = os.path.join(output_dir, "AutoAttendants.json")

            if not os.path.exists(queues_file) or not os.path.exists(aa_file):
                if self.progress_cb:
                    self.progress_cb(
                        "No Teams data produced, trying next user…"
                    )
                continue

            # ✅ SUCCESS – real data fetched
            if self.progress_cb:
                self.log.info("Teams queues & auto attendants fetched")
                self.progress_cb("Teams Call Queues & Auto Attendants fetched successfully.")

            return  # 🚀 EXIT LOOP ONLY ON REAL SUCCESS

        # ❌ ALL USERS FAILED
        raise PermissionError(
            "Unable to fetch Teams Call Queues & Auto Attendants.\n\n"
            "None of the active users have required Teams permissions.\n\n"
            "Required role:\n"
            "• Teams Communications Administrator\n"
            "• Teams Administrator"
        )

