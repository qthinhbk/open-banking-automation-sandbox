# Open Banking Automation Sandbox (Apache Fineract)

A local laboratory demonstrating core banking API contract analysis, traffic capture, target virtualization, and workflow automation scenarios based on Apache Fineract.

## 🌟 Project Overview

This repository showcases the methodology for reverse engineering and automating Core Banking REST APIs. It deploys a local Apache Fineract target instance inside Docker and provides tools to capture traffic, reconstruct OpenAPI schemas, and automate account management scenarios.

### Technical Stack
* **Target Core Banking**: Apache Fineract, PostgreSQL
* **Traffic Analysis**: TShark, Mitmproxy (Python logging and auth extraction scripts)
* **API Automation**: Python `requests` library
* **Schema Reconstruction**: OpenAPI 3.0 Specification (split by module)
* **Instrumentation Reference**: Frida (SSL pinning bypass helper)

---

## 📁 Repository Structure

```
open-banking-automation-sandbox/
├── target-server/
│   ├── docker-compose.yml        # Fineract + PostgreSQL configuration
│   └── init.sql                  # PostgreSQL database initializer script
├── traffic-analysis/
│   ├── mitmproxy-scripts/        # Intercept Fineract API calls
│   │   ├── logger.py             # Log + parse requests/responses
│   │   └── auth_extractor.py     # Decode auth header credentials
│   ├── captured-flows/           # Sanitized sample Fineract API flows
│   │   ├── traffic.pcap          # Captured raw packets
│   │   └── traffic.json          # Decoded HTTP transactions
│   ├── ssl-pinning-bypass/
│   │   └── bypass.js             # Android SSL pinning hook blueprint
│   ├── burp-suite/
│   │   └── burp_config.json      # Pre-configured Burp target scope & listeners
│   └── wireshark/
│       ├── capture.py            # Orchestrates tshark capture while seeding
│       ├── parse.py              # Parses PCAP packets into JSON flows
│       └── capture_filters.txt   # Capture & display filters for bank auditing
├── api-reverse/
│   ├── generate.py               # Generates OpenAPI specs from traffic.json
│   ├── verify.py                 # Contract validation (static & live)
│   ├── schemas/                  # Reconstructed OpenAPI specs
│   │   ├── clients.yaml          # Client onboarding endpoints
│   │   ├── loans.yaml            # Loan accounts endpoints
│   │   └── transactions.yaml     # Transfers & savings transactions
│   └── postman-collections/
│       └── mock_bank.postman_collection.json
├── automation/
│   ├── client.py                 # Python client library
│   ├── seed.py                   # Client and savings account seeding script
│   └── scenarios/                # Replayed transaction workflows
│       ├── create_client.py      # Onboards a client
│       ├── open_savings.py       # Opens a savings account
│       └── transfer_funds.py     # Executes a double-entry ledger transfer
└── docs/
    └── methodology.md            # Detailed RE process documentation
```

---

## 🚀 Getting Started

### 1. Installation
Clone this repository and install the Python dependencies:
```bash
pip install -r requirements.txt
```

### 2. Deploy target-server (Apache Fineract)
Deploy the local core banking instance and its database. In your terminal:
```bash
cd target-server
docker compose up -d
```
Fineract will execute migrations upon first boot, which takes 60–90 seconds. Monitor logs:
```bash
docker compose logs -f fineract
```

### 3. Capture & Parse Traffic
To capture network traffic during database seeding:
```bash
# Start loopback capture and run seeding script
python traffic-analysis/wireshark/capture.py

# Parse the generated PCAP file into structured JSON
python traffic-analysis/wireshark/parse.py
```

### 4. Generate & Verify OpenAPI Schemas
Generate OpenAPI specifications from the captured JSON:
```bash
# Reconstruct specifications
python api-reverse/generate.py

# Validate specs against captured traffic and live server
python api-reverse/verify.py
```

### 5. Run Scenario Automation
Execute individual automated scenarios against the staging API:
```bash
# Onboard a new client
python automation/scenarios/create_client.py

# Submit savings account application
python automation/scenarios/open_savings.py

# Transfer funds between accounts
python automation/scenarios/transfer_funds.py

# Run the client class test
python automation/client.py
```

---

## 📂 Reconstructed OpenAPI Specifications

The reconstructed OpenAPI 3.0 specifications are split by business module in `api-reverse/schemas/`:
* **`clients.yaml`**: Reconstructed from live loopback HTTP traffic.
* **`transactions.yaml`**: Reconstructed from live loopback HTTP traffic (covers savings accounts, transactions, and internal fund transfers).
* **`loans.yaml`**: Reconstructed based on Fineract developer swagger models and Java source controllers, not from captured traffic (as loans were not part of the active seeding scenario).

---

## 📖 Methodology
For details regarding **Frida instrumentation**, **SSL bypass logic**, **ADB WiFi configurations**, and **WSL2 proxy redirection**, read the [Methodology Documentation](docs/methodology.md).