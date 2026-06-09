import base64
from mitmproxy import http

class FineractAuthExtractor:
    def load(self, loader):
        print("[AUTH EXTRACTOR] Addon loaded. Extracting token/basic auth headers...")

    def request(self, flow: http.HTTPFlow) -> None:
        req = flow.request
        
        # Look for Fineract tenant header
        tenant_id = req.headers.get("Fineract-Platform-TenantId", None)
        if tenant_id:
            print(f"[AUTH EXTRACTOR] Detected Tenant Header: Fineract-Platform-TenantId: {tenant_id}")
            
        # Check authorization headers
        auth_header = req.headers.get("Authorization", None)
        if auth_header:
            print(f"[AUTH EXTRACTOR] Authorization header found: {auth_header[:20]}...")
            
            # Analyze Basic Authentication
            if auth_header.lower().startswith("basic "):
                try:
                    encoded_creds = auth_header[6:].strip()
                    decoded_bytes = base64.b64decode(encoded_creds)
                    decoded_str = decoded_bytes.decode("utf-8")
                    username, _ = decoded_str.split(":", 1)
                    # For safety, we only print the username, NEVER the password
                    print(f"[AUTH EXTRACTOR] Basic Auth user identified: '{username}' (Password is hidden)")
                except Exception as e:
                    print(f"[AUTH EXTRACTOR] Failed to decode Basic Auth header: {e}")
            
            # Analyze Bearer Token
            elif auth_header.lower().startswith("bearer "):
                token = auth_header[7:].strip()
                # Print token length or signature prefix
                prefix = token[:10] if len(token) > 10 else token
                print(f"[AUTH EXTRACTOR] Bearer Auth token detected. Length: {len(token)}, prefix: '{prefix}...'")

addons = [
    FineractAuthExtractor()
]
