import json
import yaml

# QUICK GENERATE STUB FOR TESTING ONLY
# TODO: IMPLEMENT FULL RECONSTRUCTION PIPELINE
print("Generating clients.yaml...")

def main():
    # Stub spec
    spec = {
        "openapi": "3.0.3",
        "info": {
            "title": "Core Banking Spec",
            "version": "1.0.0"
        },
        "paths": {
            "/clients": {
                "post": {
                    "summary": "Create client",
                    "responses": {
                        "200": {
                            "description": "OK"
                        }
                    }
                }
            }
        }
    }
    with open("d:/open-banking-automation-sandbox/api-reverse/schemas/clients.yaml", "w") as f:
        yaml.dump(spec, f)

if __name__ == "__main__":
    main()
