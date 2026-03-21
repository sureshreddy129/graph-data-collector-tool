import json
import requests
from datetime import datetime, timedelta, timezone
from tkinter import messagebox
from utils.path_helper import resource_path

class TokenManager:
    def __init__(self):
        self.client_id = None
        self.client_secret = None
        self.tenant_guid = None
        self.refresh_token = None

        self.token_url = None
        self.access_token = None
        self.token_expiry = None

    # --------------------------------------------------
    # Load client credentials (from existing config)
    # --------------------------------------------------
    def load_client_secrets(self):
        client_secret_path = resource_path("config/client_secrets.json")
        with open(client_secret_path) as f:
            cfg = json.load(f)

        self.client_id = cfg["client_id"]
        self.client_secret = cfg["client_secret"]

    def set_refresh_token(self, refresh_token):
        self.refresh_token = refresh_token

    # --------------------------------------------------
    # Generate APP (client_credentials) Graph token
    # (this is what your current UI uses first)
    # --------------------------------------------------
    def generate_app_token(self, tenant_guid, refresh_token):
        self.tenant_guid = tenant_guid
        self.refresh_token = refresh_token

        self.load_client_secrets()

        self.token_url = (
            f"https://login.microsoftonline.com/"
            f"{self.tenant_guid}/oauth2/v2.0/token"
        )

        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials",
            "refresh_token": self.refresh_token,
            "scope": "https://graph.microsoft.com/.default"
        }

        response = requests.post(self.token_url, data=data)
        response.raise_for_status()

        token_data = response.json()
        self.access_token = token_data["access_token"]

        expires_in = int(token_data.get("expires_in", 3600))
        self.token_expiry = (
            datetime.now(timezone.utc)
            + timedelta(seconds=expires_in - 60)
        )

        return self.access_token, self.token_expiry

    # --------------------------------------------------
    # Check token expiry
    # --------------------------------------------------
    def is_token_expired(self):
        if not self.access_token or not self.token_expiry:
            return True

        return datetime.now(timezone.utc) >= self.token_expiry

    # --------------------------------------------------
    # Ask user & refresh token (UI-driven)
    # --------------------------------------------------
    def ask_and_refresh_token(self):
        choice = messagebox.askyesno(
            "Token Expired",
            "Access token has expired.\n\nDo you want to generate a new token?"
        )

        if not choice:
            return False

        try:
            self.generate_app_token(self.tenant_guid, self.refresh_token)
            messagebox.showinfo("Success", "New access token generated.")
            return True
        except Exception as e:
            messagebox.showerror("Token Error", str(e))
            return False

    # --------------------------------------------------
    # Delegated Graph token (refresh_token flow)
    # --------------------------------------------------
    def get_graph_token_from_refresh(self):
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "scope": "https://graph.microsoft.com/.default offline_access"
        }

        response = requests.post(self.token_url, data=data)
        response.raise_for_status()

        return response.json()["access_token"]

    # --------------------------------------------------
    # Delegated Teams token (refresh_token flow)
    # --------------------------------------------------
    def get_teams_token_from_refresh(self):
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "scope": (
                "48ac35b8-9aa8-4d74-927d-1f4a14a0b239/.default "
                "offline_access"
            )
        }

        response = requests.post(self.token_url, data=data)
        response.raise_for_status()

        return response.json()["access_token"]
