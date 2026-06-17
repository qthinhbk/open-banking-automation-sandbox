import json
import yaml
import os
import re
import requests

FLOWS_FILE = "d:/open-banking-automation-sandbox/traffic-analysis/captured-flows/traffic.json"
SCHEMAS_DIR = "d:/open-banking-automation-sandbox/api-reverse/schemas"
FINERACT_URL = "http://127.0.0.1:8080/fineract-provider/api/v1"
AUTH = ("mifos", "password")
HEADERS = {"Fineract-Platform-TenantId": "default"}

def load_schemas():
    schemas = {}
    for filename in ["clients.yaml", "transactions.yaml", "loans.yaml"]:
        path = os.path.join(SCHEMAS_DIR, filename)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                schemas[filename] = yaml.safe_load(f)
    return schemas

def validate(data, schema, path=""):
    if not schema:
        return []

    errors = []
    
    if "oneOf" in schema:
        sub_errors = []
        for idx, sub_schema in enumerate(schema["oneOf"]):
            errs = validate(data, sub_schema, f"{path}[oneOf:{idx}]")
            if not errs:
                return []
            sub_errors.append(errs)
        errors.append(f"Field {path} does not match any of the oneOf schemas. Sub-errors: {sub_errors}")
        return errors

    schema_type = schema.get("type")
    
    if schema_type == "object":
        if not isinstance(data, dict):
            return [f"Field {path} expected object, got {type(data).__name__}"]
        
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        
        for req_field in required:
            if req_field not in data:
                errors.append(f"Missing required field: {path}.{req_field}" if path else f"Missing required field: {req_field}")
                
        for k, v in data.items():
            if k in properties:
                sub_path = f"{path}.{k}" if path else k
                errors.extend(validate(v, properties[k], sub_path))
                
    elif schema_type == "array":
        if not isinstance(data, list):
            return [f"Field {path} expected array, got {type(data).__name__}"]
        items_schema = schema.get("items")
        if items_schema:
            for idx, item in enumerate(data):
                errors.extend(validate(item, items_schema, f"{path}[{idx}]"))
                
    elif schema_type == "integer":
        if not isinstance(data, int) or isinstance(data, bool):
            return [f"Field {path} expected integer, got {type(data).__name__} (value: {data})"]
            
    elif schema_type == "number":
        if not isinstance(data, (int, float)) or isinstance(data, bool):
            return [f"Field {path} expected number, got {type(data).__name__} (value: {data})"]
            
    elif schema_type == "boolean":
        if not isinstance(data, bool):
            return [f"Field {path} expected boolean, got {type(data).__name__} (value: {data})"]
            
    elif schema_type == "string":
        if not isinstance(data, str):
            return [f"Field {path} expected string, got {type(data).__name__} (value: {data})"]
            
    return errors

def clean_path(uri):
    path = uri.replace("/fineract-provider/api/v1", "")
    if "?" in path:
        path = path.split("?")[0]
    path = re.sub(r"/clients/\d+", "/clients/{clientId}", path)
    path = re.sub(r"/savingsaccounts/\d+/transactions", "/savingsaccounts/{accountId}/transactions", path)
    path = re.sub(r"/savingsaccounts/\d+", "/savingsaccounts/{accountId}", path)
    path = re.sub(r"/loans/\d+", "/loans/{loanId}", path)
    return path

def match_route(schemas, path, method):
    method = method.lower()
    for filename, spec in schemas.items():
        spec_paths = spec.get("paths", {})
        if path in spec_paths:
            if method in spec_paths[path]:
                return spec_paths[path][method], filename
    return None, None

def test_static(schemas):
    print("\n--- Running static conformance tests ---")
    if not os.path.exists(FLOWS_FILE):
        print(f"Error: flows file not found: {FLOWS_FILE}")
        return

    with open(FLOWS_FILE, "r", encoding="utf-8") as f:
        flows = json.load(f)

    total = 0
    passed = 0

    for entry in flows:
        packet_no = entry.get("packet_number")
        uri = entry.get("uri", "")
        method = entry.get("method", "POST" if entry.get("type") == "request" else "GET")
        type_ = entry.get("type")
        body = entry.get("body")
        status_code = entry.get("status_code")

        if not body:
            continue

        norm_path = clean_path(uri)
        op_spec, spec_file = match_route(schemas, norm_path, method)

        if not op_spec:
            continue

        total += 1
        print(f"Packet #{packet_no}: {method} {uri} -> {norm_path} ({spec_file})")

        errors = []
        if type_ == "request":
            req_body_spec = op_spec.get("requestBody", {}).get("content", {}).get("application/json", {}).get("schema")
            if req_body_spec:
                errors = validate(body, req_body_spec, "requestBody")
        elif type_ == "response":
            resp_spec = op_spec.get("responses", {}).get(str(status_code), {}).get("content", {}).get("application/json", {}).get("schema")
            if resp_spec:
                errors = validate(body, resp_spec, "responseBody")

        if not errors:
            print("  Result: OK")
            passed += 1
        else:
            print("  Result: FAIL")
            for err in errors:
                print(f"    - {err}")
        print("-" * 50)

    print(f"Static conformance check summary: {passed}/{total} passed")

def test_live(schemas):
    print("\n--- Running live API contract tests ---")
    client_id = 6
    savings_id = 6
    
    try:
        r = requests.get(f"{FINERACT_URL}/clients", auth=AUTH, headers=HEADERS)
        if r.status_code == 200:
            clients = r.json().get("pageItems", [])
            if clients:
                client_id = clients[0].get("id", client_id)
        
        r = requests.get(f"{FINERACT_URL}/savingsaccounts", auth=AUTH, headers=HEADERS)
        if r.status_code == 200:
            accounts = r.json()
            if isinstance(accounts, list) and accounts:
                savings_id = accounts[0].get("id", savings_id)
            elif isinstance(accounts, dict) and "pageItems" in accounts:
                page_items = accounts.get("pageItems", [])
                if page_items:
                    savings_id = page_items[0].get("id", savings_id)
    except Exception as e:
        print(f"Warning: Connection failed. Using fallback IDs ({client_id}, {savings_id}). Error: {e}")

    live_tests = [
        {"file": "transactions.yaml", "path": "/savingsaccounts/{accountId}", "method": "GET", "replacements": {"{accountId}": savings_id}, "params": {"associations": "transactions"}},
        {"file": "clients.yaml", "path": "/clients", "method": "GET", "replacements": {}, "params": {}}
    ]

    for test in live_tests:
        spec_file = test["file"]
        spec_path = test["path"]
        method = test["method"]
        replacements = test["replacements"]
        params = test["params"]

        spec = schemas.get(spec_file)
        if not spec:
            continue

        op_spec = spec.get("paths", {}).get(spec_path, {}).get(method.lower())
        if not op_spec:
            continue

        actual_path = spec_path
        for k, v in replacements.items():
            actual_path = actual_path.replace(k, str(v))
        
        url = f"{FINERACT_URL}{actual_path}"
        print(f"Live API call: {method} {url} with params {params}")

        try:
            r = requests.get(url, auth=AUTH, headers=HEADERS, params=params)
            print(f"  HTTP Code: {r.status_code}")
            
            if r.status_code == 200:
                body = r.json()
                resp_spec = op_spec.get("responses", {}).get("200", {}).get("content", {}).get("application/json", {}).get("schema")
                if resp_spec:
                    errors = validate(body, resp_spec, "responseBody")
                    if not errors:
                        print("  Contract validation: OK")
                    else:
                        print("  Contract validation: FAIL")
                        for err in errors:
                            print(f"    - {err}")
                else:
                    print("  Warning: No 200 response schema defined in spec.")
            else:
                print(f"  Error: API call failed with status: {r.status_code}")
        except Exception as e:
            print(f"  Connection error: {e}")
        print("-" * 50)

def main():
    schemas = load_schemas()
    if not schemas:
        print(f"Error: No schemas loaded from {SCHEMAS_DIR}")
        return

    test_static(schemas)
    test_live(schemas)

if __name__ == "__main__":
    main()
