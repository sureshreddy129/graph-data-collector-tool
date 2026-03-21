import os
import json
import requests
from datetime import datetime, timezone, timedelta

class GraphClient:
    def __init__(self, token_manager, graph_apis, tenant_name, progress_cb=None, logger =None):
        """
        token_manager : TokenManager instance
        graph_apis    : loaded graph_apis.json
        tenant_name   : used for output folder
        progress_cb   : optional callback for progress messages
        """
        self.tokens = token_manager
        self.graph_apis = graph_apis
        self.tenant_name = tenant_name
        self.progress_cb = progress_cb
        self.log = logger
    # --------------------------------------------------
    # Main API executor
    # --------------------------------------------------
    def call_api(self, api_name, inputs, executor):

        api = self.graph_apis[api_name]
        if self.log:
            self.log.info(f"Calling Graph API: {api_name}")
        headers = {
            "Authorization": f"Bearer {self.tokens.access_token}",
            "Content-Type": "application/json"
        }

        method = api.get("method", "GET").upper()
        url = api["endpoint"]

        # Replace path parameters
        for key, val in inputs.items():
            url = url.replace(f"{{{key}}}", val)

        all_data = []

        # -------------------------------
        # Build filter string (date range)
        # -------------------------------
        filter_str = None
        if "start_date" in inputs and "end_date" in inputs:
            safe_utc = datetime.now(timezone.utc) - timedelta(hours=4)

            user_end = datetime.fromisoformat(
                inputs["end_date"].replace("Z", "")
            ).replace(tzinfo=timezone.utc)

            if user_end > safe_utc:
                user_end = safe_utc
                if self.progress_cb:
                    self.progress_cb(
                        "Adjusting end time due to Graph ingestion delay..."
                    )
            end_iso = user_end.strftime("%Y-%m-%dT%H:%M:%SZ")
            filter_str = (
                f"startDateTime ge {inputs['start_date']} "
                f"and startDateTime lt {end_iso}"
               # f"and startDateTime lt {inputs['end_date']}Z"
            )
            self.log.info(f"Calling Graph API: {api_name} from {inputs['start_date']} to {end_iso}")


        # -------------------------------
        # Initial API call
        # -------------------------------
        if method == "POST":
            payload = {}
            if api.get("body_type") == "filter" and filter_str:
                payload["filter"] = filter_str



            resp = requests.post(url, headers=headers, json=payload)

        else:  # GET
            if "(" in url:
                self.log.info(f"Calling Graph API: {api_name} from {inputs['from']} to {inputs['to']}")
                resp = requests.get(url, headers=headers)
            else:
                # params = {}
                # if filter_str:
                #     params["$filter"] = filter_str
                if filter_str:
                    url = f"{url}?$filter={filter_str}"
                resp = requests.get(url, headers=headers)

        resp.raise_for_status()
        data = resp.json()

        # -------------------------------
        # Handle response shape
        # -------------------------------
        if "value" in data:
            all_data.extend(data["value"])
            next_link = data.get("@odata.nextLink")
        else:
            all_data.append(data)
            next_link = None

        # -------------------------------
        # Pagination
        # -------------------------------
        page = 1
        while next_link:
            self.log.info(f"{api_name} page {page} fetched")
            if executor.cancel_requested:
                if self.progress_cb:
                    self.progress_cb("Cancelling API fetch...")
                return
            if self.progress_cb:
                self.progress_cb(f"Fetching page {page} of {api_name}...")

            resp = requests.get(next_link, headers=headers)
            resp.raise_for_status()
            data = resp.json()

            all_data.extend(data.get("value", []))
            next_link = data.get("@odata.nextLink")
            page += 1

        # -------------------------------
        # Save output
        # -------------------------------
        self.save_data(api["filename"], all_data)

    # --------------------------------------------------
    # Save API output
    # --------------------------------------------------
    def save_data(self, filename, data):
        folder = os.path.join("output", self.tenant_name)
        os.makedirs(folder, exist_ok=True)

        path = os.path.join(folder, filename)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        self.log.info(f"{filename} saved ({len(data)} records)")
        print(f"Saved {filename} ({len(data)} records)")
