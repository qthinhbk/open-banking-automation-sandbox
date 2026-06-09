import json
import os
from datetime import datetime
from mitmproxy import http

class FineractTrafficLogger:
    def __init__(self):
        self.log_dir = "d:/open-banking-automation-sandbox/traffic-analysis/captured-flows"
        os.makedirs(self.log_dir, exist_ok=True)
        self.log_file = os.path.join(self.log_dir, "fineract_intercepted_flows.json")
        self.flows = []

    def load(self, loader):
        print("[FINERACT LOGGER] Addon loaded successfully. Intercepting Core Banking API calls...")

    def response(self, flow: http.HTTPFlow) -> None:
        req = flow.request
        resp = flow.response

        # Filter: only log Fineract API calls
        if "/fineract-provider/api/v1" not in req.path:
            return

        # Parse request body
        req_body = ""
        if req.content:
            try:
                req_body = json.loads(req.content.decode("utf-8", errors="ignore"))
            except Exception:
                req_body = req.content.decode("utf-8", errors="ignore")

        # Parse response body
        resp_body = ""
        if resp.content:
            try:
                resp_body = json.loads(resp.content.decode("utf-8", errors="ignore"))
            except Exception:
                resp_body = resp.content.decode("utf-8", errors="ignore")

        # Redact credentials/authorizations
        def sanitize(payload):
            if isinstance(payload, dict):
                sanitized = {}
                for k, v in payload.items():
                    if k in ["password", "newPassword", "currentPassword", "pin", "verificationCode"]:
                        sanitized[k] = "[REDACTED_SENSITIVE_DATA]"
                    else:
                        sanitized[k] = sanitize(v)
                return sanitized
            elif isinstance(payload, list):
                return [sanitize(item) for item in payload]
            return payload

        # Keep tenant and redact Authorization header values for safety
        req_headers = {}
        for k, v in req.headers.items():
            if k.lower() == "authorization":
                req_headers[k] = "Basic [REDACTED_CREDENTIALS]"
            else:
                req_headers[k] = v

        flow_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "request": {
                "method": req.method,
                "url": req.pretty_url,
                "path": req.path,
                "headers": req_headers,
                "query": dict(req.query),
                "body": sanitize(req_body)
            },
            "response": {
                "status_code": resp.status_code,
                "headers": dict(resp.headers),
                "body": sanitize(resp_body)
            }
        }

        self.flows.append(flow_data)

        try:
            with open(self.log_file, "w") as f:
                json.dump(self.flows, f, indent=2)
            print(f"[FINERACT LOGGER] Logged Fineract API: {req.method} {req.path} -> {resp.status_code}")
        except Exception as e:
            print(f"[FINERACT LOGGER] Failed to write flow log: {e}")

addons = [
    FineractTrafficLogger()
]
