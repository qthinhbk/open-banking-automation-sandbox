# Core Banking API Analysis & Automation (Apache Fineract)

This document outlines the technical approach, network capture methods, and automation workflows implemented in this sandbox.

---

## 1. Environment Setup

To perform integration testing and contract verification safely, we deploy a local instance of the open-source **Apache Fineract** Core Banking System.

```
[Client Automation]  --->  [Fineract Server (Port 8080)]
                                 |
                          Captured by TShark
```

### Docker compose configuration (`target-server/docker-compose.yml`)
Fineract runs backed by a PostgreSQL database container. During initial container startup, migrations are run to initialize the core database schemas (`fineract_tenants` and `fineract_default`).
*   **Database (`db`)**: Runs `postgres:15-alpine` and mounts `init.sql` to set up initial databases.
*   **Core Banking (`fineract`)**: Runs `apache/fineract:latest` with SSL disabled locally (`FINERACT_SERVER_SSL_ENABLED=false`) to simplify local capture.

---

## 2. Traffic Analysis & Interception

Redirection and packet capture are performed to analyze Fineract's core banking workflows.

### 2.1 Packet Capture (TShark)

On Windows, local loopback traffic can be intercepted via Npcap. The default loopback interface index (e.g. `9` or `\Device\NPF_Loopback`) is targeted.
*   **Capture Script (`traffic-analysis/wireshark/capture.py`)**: Runs tshark in the background filtering for port `8080`, triggers `automation/seed.py` to populate accounts, then stops capture.
*   **Packet Parser (`traffic-analysis/wireshark/parse.py`)**: Extracts HTTP payloads from the PCAP file. If the HTTP body is present as hex under `http.file_data`, the script decodes the hex bytes into text/JSON.

#### Capture Commands:
To manually capture traffic on the loopback adapter:
```bash
tshark -i 9 -f "tcp port 8080" -w traffic.pcap
```

To view HTTP request methods and URIs:
```bash
tshark -r traffic.pcap -Y "http.request" -T fields -e http.request.method -e http.request.uri
```

---

## 3. OpenAPI Schema Reconstruction

By analyzing the JSON payloads extracted from the network traffic, we reconstruct the OpenAPI 3.0 specifications under `api-reverse/schemas/`:
*   **`clients.yaml`**: Documents client registration and search (`POST /clients`).
*   **`transactions.yaml`**: Details savings account details and transactions (`GET /savingsaccounts/{accountId}`, `POST /savingsaccounts/{accountId}/transactions`, and `POST /accounttransfers`).
*   **`loans.yaml`**: Reconstructed based on Fineract Java controllers and official Swagger specifications (for complete module reference).

The generator script `api-reverse/generate.py` translates Python types from parsed traffic logs into OpenAPI schema fields.

---

## 4. Contract Verification

To detect schema drift and validate the generated specs:
*   **Static verification**: `api-reverse/verify.py` reads the JSON transaction flows and verifies that each request/response conforms to the corresponding schema file.
*   **Live contract tests**: `api-reverse/verify.py` queries a running local Fineract instance and validates live response bodies against the OpenAPI schemas.

---

## 5. Workflow Automation

Based on the reverse-engineered contracts, we build programmatic clients (`automation/client.py`) and scripts to automate standard operations:
1.  **Client creation**: Submits details to register a client profile.
2.  **Savings account setup**: Submits and approves a savings account linked to the client.
3.  **Fund transfers**: Executes internal double-entry ledger transfers between savings accounts.
