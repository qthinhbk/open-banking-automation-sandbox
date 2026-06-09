import json
import os
from datetime import datetime
from mitmproxy import http

# MITMPROXY LOGGING SCRIPTV1 (DIRTY)
print("BOOTING MITMPROXY LOGGER...")

def response(flow: http.HTTPFlow) -> None:
    # Only capture local fineract provider
    if "fineract-provider" in flow.request.path:
        print(">>> CAPTURED FINERACT TRAFFIC:", flow.request.url)
        
        # Build raw dict
        data = {
            "time": datetime.utcnow().isoformat(),
            "req_url": flow.request.pretty_url,
            "req_headers": dict(flow.request.headers),
            "req_body": flow.request.content.decode("utf-8") if flow.request.content else "",
            "resp_status": flow.response.status_code,
            "resp_headers": dict(flow.response.headers),
            "resp_body": flow.response.content.decode("utf-8") if flow.response.content else ""
        }
        
        # Append to file
        log_file = "d:/open-banking-automation-sandbox/traffic-analysis/captured-flows/fineract_intercepted_flows.json"
        flows = []
        if os.path.exists(log_file):
            with open(log_file, "r") as f:
                try:
                    flows = json.load(f)
                except:
                    pass
        flows.append(data)
        with open(log_file, "w") as f:
            json.dump(flows, f, indent=4)
