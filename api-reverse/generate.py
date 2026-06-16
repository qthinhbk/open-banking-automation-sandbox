import json
import yaml
import os

FLOWS_FILE = "d:/open-banking-automation-sandbox/traffic-analysis/captured-flows/traffic.json"
SCHEMAS_DIR = "d:/open-banking-automation-sandbox/api-reverse/schemas"

def map_type(val):
    if isinstance(val, bool):
        return {"type": "boolean"}
    elif isinstance(val, int):
        return {"type": "integer"}
    elif isinstance(val, float):
        return {"type": "number"}
    elif isinstance(val, list):
        item_schema = map_type(val[0]) if len(val) > 0 else {"type": "string"}
        return {"type": "array", "items": item_schema}
    elif isinstance(val, dict):
        properties = {k: map_type(v) for k, v in val.items()}
        return {"type": "object", "properties": properties}
    else:
        return {"type": "string"}

def to_schema(payload):
    if not payload or not isinstance(payload, dict):
        return {"type": "object", "properties": {}}
    
    properties = {}
    required_fields = []
    for k, v in payload.items():
        properties[k] = map_type(v)
        if not isinstance(v, (dict, list)):
            properties[k]["example"] = v
        elif isinstance(v, list) and len(v) > 0 and not isinstance(v[0], (dict, list)):
            properties[k]["example"] = v
        required_fields.append(k)
        
    return {
        "type": "object",
        "required": required_fields,
        "properties": properties
    }

def main():
    if not os.path.exists(FLOWS_FILE):
        print(f"Error: flows file not found at {FLOWS_FILE}")
        return

    with open(FLOWS_FILE, "r", encoding="utf-8") as f:
        flows = json.load(f)

    print("Generating schemas from captured traffic...")

    client_req = None
    client_resp = None
    savings_req = None
    savings_resp = None
    transfer_req = None
    transfer_resp = None
    savings_detail = None

    savings_approve_req = None
    savings_approve_resp = None
    savings_activate_req = None
    savings_activate_resp = None
    deposit_req = None
    deposit_resp = None

    for entry in flows:
        uri = entry.get("uri", "")
        type_ = entry.get("type", "")
        body = entry.get("body")
        status_code = entry.get("status_code") or entry.get("http.response.code") or entry.get("http.response_code")
        
        if not body:
            continue

        if type_ == "request":
            if "/clients" in uri and not client_req:
                client_req = body
            elif uri.endswith("/savingsaccounts") and not savings_req:
                savings_req = body
            elif "command=approve" in uri and not savings_approve_req:
                savings_approve_req = body
            elif "command=activate" in uri and not savings_activate_req:
                savings_activate_req = body
            elif "command=deposit" in uri and not deposit_req:
                deposit_req = body
            elif "/accounttransfers" in uri and not transfer_req:
                transfer_req = body
        elif type_ == "response" and status_code is not None and int(status_code) == 200:
            if "clientId" in body and "officeId" in body and "resourceId" in body and "savingsId" not in body:
                client_resp = body
            elif "savingsId" in body and "resourceId" in body and "gsimId" in body:
                savings_resp = body
            elif "resourceId" in body and "savingsId" in body and "changes" in body:
                changes = body.get("changes", {})
                if "approvedOnDate" in changes and not savings_approve_resp:
                    savings_approve_resp = body
                elif "activatedOnDate" in changes and not savings_activate_resp:
                    savings_activate_resp = body
                elif "paymentTypeId" in changes and not deposit_resp:
                    deposit_resp = body
            elif "resourceId" in body and "savingsId" in body and len(body.keys()) == 2:
                transfer_resp = body
            elif "accountNo" in body and "clientName" in body:
                savings_detail = body

    def get_schema(payload, fallback=None):
        if payload:
            return to_schema(payload)
        return {"type": "object", "properties": fallback or {}}

    clients_spec = {
        "openapi": "3.0.3",
        "info": {
            "title": "Fineract Clients API Spec (Reconstructed)",
            "description": "Reconstructed client onboarding endpoints from captured traffic logs.",
            "version": "1.0.0"
        },
        "servers": [{"url": "http://127.0.0.1:8080/fineract-provider/api/v1"}],
        "paths": {
            "/clients": {
                "post": {
                    "summary": "Create new client profile",
                    "tags": ["Clients"],
                    "security": [{"BasicAuth": []}],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": to_schema(client_req)
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Client created successfully",
                            "content": {
                                "application/json": {
                                    "schema": to_schema(client_resp)
                                }
                            }
                        }
                    }
                }
            }
        },
        "components": {
            "securitySchemes": {
                "BasicAuth": {
                    "type": "http",
                    "scheme": "basic"
                }
            }
        }
    }

    transactions_spec = {
        "openapi": "3.0.3",
        "info": {
            "title": "Fineract Transactions & Accounts API Spec (Reconstructed)",
            "description": "Reconstructed savings accounts, deposits, and internal transfers from captured traffic logs.",
            "version": "1.0.0"
        },
        "servers": [{"url": "http://127.0.0.1:8080/fineract-provider/api/v1"}],
        "paths": {
            "/savingsaccounts": {
                "post": {
                    "summary": "Submit savings account application",
                    "tags": ["Savings Accounts"],
                    "security": [{"BasicAuth": []}],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": to_schema(savings_req)
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Savings application submitted",
                            "content": {
                                "application/json": {
                                    "schema": to_schema(savings_resp)
                                }
                            }
                        }
                    }
                }
            },
            "/savingsaccounts/{accountId}": {
                "post": {
                    "summary": "Approve or activate savings account application",
                    "tags": ["Savings Accounts"],
                    "security": [{"BasicAuth": []}],
                    "parameters": [
                        {
                            "name": "accountId",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "integer"}
                        },
                        {
                            "name": "command",
                            "in": "query",
                            "required": True,
                            "schema": {
                                "type": "string",
                                "enum": ["approve", "activate"]
                            }
                        }
                    ],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "oneOf": [
                                        get_schema(savings_approve_req, {
                                            "approvedOnDate": {"type": "string", "example": "16 June 2026"},
                                            "dateFormat": {"type": "string", "example": "dd MMMM yyyy"},
                                            "locale": {"type": "string", "example": "en"}
                                        }),
                                        get_schema(savings_activate_req, {
                                            "activatedOnDate": {"type": "string", "example": "16 June 2026"},
                                            "dateFormat": {"type": "string", "example": "dd MMMM yyyy"},
                                            "locale": {"type": "string", "example": "en"}
                                        })
                                    ]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Command executed successfully",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "oneOf": [
                                            get_schema(savings_approve_resp, {
                                                "officeId": {"type": "integer", "example": 1},
                                                "clientId": {"type": "integer", "example": 6},
                                                "savingsId": {"type": "integer", "example": 6},
                                                "resourceId": {"type": "integer", "example": 6}
                                            }),
                                            get_schema(savings_activate_resp, {
                                                "officeId": {"type": "integer", "example": 1},
                                                "clientId": {"type": "integer", "example": 6},
                                                "savingsId": {"type": "integer", "example": 6},
                                                "resourceId": {"type": "integer", "example": 6}
                                            })
                                        ]
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/savingsaccounts/{accountId}/transactions": {
                "post": {
                    "summary": "Post a savings account transaction",
                    "tags": ["Transactions"],
                    "security": [{"BasicAuth": []}],
                    "parameters": [
                        {
                            "name": "accountId",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "integer"}
                        },
                        {
                            "name": "command",
                            "in": "query",
                            "required": True,
                            "schema": {
                                "type": "string",
                                "enum": ["deposit", "withdrawal"]
                            }
                        }
                    ],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": get_schema(deposit_req, {
                                    "locale": {"type": "string", "example": "en"},
                                    "dateFormat": {"type": "string", "example": "dd MMMM yyyy"},
                                    "transactionDate": {"type": "string", "example": "16 June 2026"},
                                    "transactionAmount": {"type": "number", "example": 1000.0},
                                    "paymentTypeId": {"type": "integer", "example": 1}
                                })
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Transaction posted successfully",
                            "content": {
                                "application/json": {
                                    "schema": get_schema(deposit_resp, {
                                        "officeId": {"type": "integer", "example": 1},
                                        "clientId": {"type": "integer", "example": 6},
                                        "savingsId": {"type": "integer", "example": 6},
                                        "resourceId": {"type": "integer", "example": 8}
                                    })
                                }
                            }
                        }
                    }
                }
            },
            "/accounttransfers": {
                "post": {
                    "summary": "Create internal fund transfer",
                    "tags": ["Account Transfers"],
                    "security": [{"BasicAuth": []}],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": to_schema(transfer_req)
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Transfer completed",
                            "content": {
                                "application/json": {
                                    "schema": to_schema(transfer_resp)
                                }
                            }
                        }
                    }
                }
            }
        },
        "components": {
            "securitySchemes": {
                "BasicAuth": {
                    "type": "http",
                    "scheme": "basic"
                }
            }
        }
    }

    if savings_detail:
        if "/savingsaccounts/{accountId}" not in transactions_spec["paths"]:
            transactions_spec["paths"]["/savingsaccounts/{accountId}"] = {}
        transactions_spec["paths"]["/savingsaccounts/{accountId}"]["get"] = {
            "summary": "Retrieve savings account details and transactions",
            "tags": ["Savings Accounts"],
            "security": [{"BasicAuth": []}],
            "parameters": [
                {
                    "name": "accountId",
                    "in": "path",
                    "required": True,
                    "schema": {"type": "integer"}
                },
                {
                    "name": "associations",
                    "in": "query",
                    "required": False,
                    "schema": {"type": "string", "example": "transactions"}
                }
            ],
            "responses": {
                "200": {
                    "description": "Savings details returned",
                    "content": {
                        "application/json": {
                            "schema": to_schema(savings_detail)
                        }
                    }
                }
            }
        }

    loans_spec = {
        "openapi": "3.0.3",
        "info": {
            "title": "Fineract Loans API Spec (Reconstructed)",
            "description": "Reconstructed loan products and accounts endpoints from Fineract Swagger specs and Java models.",
            "version": "1.0.0"
        },
        "servers": [{"url": "http://127.0.0.1:8080/fineract-provider/api/v1"}],
        "paths": {
            "/loans": {
                "post": {
                    "summary": "Submit a loan application",
                    "tags": ["Loans"],
                    "security": [{"BasicAuth": []}],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": [
                                        "clientId", "productId", "principal", "loanTermFrequency",
                                        "loanTermFrequencyType", "numberOfRepayments", "repaymentEvery",
                                        "repaymentFrequencyType", "interestRatePerPeriod", "amortizationType",
                                        "interestType", "interestCalculationPeriodType", "expectedDisbursementDate",
                                        "submittedOnDate", "dateFormat", "locale"
                                    ],
                                    "properties": {
                                        "clientId": {"type": "integer", "example": 1},
                                        "productId": {"type": "integer", "example": 1},
                                        "principal": {"type": "number", "example": 10000.00},
                                        "loanTermFrequency": {"type": "integer", "example": 12},
                                        "loanTermFrequencyType": {"type": "integer", "example": 2},
                                        "numberOfRepayments": {"type": "integer", "example": 12},
                                        "repaymentEvery": {"type": "integer", "example": 1},
                                        "repaymentFrequencyType": {"type": "integer", "example": 2},
                                        "interestRatePerPeriod": {"type": "number", "example": 1.5},
                                        "amortizationType": {"type": "integer", "example": 1},
                                        "interestType": {"type": "integer", "example": 1},
                                        "interestCalculationPeriodType": {"type": "integer", "example": 1},
                                        "expectedDisbursementDate": {"type": "string", "example": "2026-06-20"},
                                        "submittedOnDate": {"type": "string", "example": "2026-06-16"},
                                        "dateFormat": {"type": "string", "example": "yyyy-MM-dd"},
                                        "locale": {"type": "string", "example": "en"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Loan application submitted successfully",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "officeId": {"type": "integer", "example": 1},
                                            "clientId": {"type": "integer", "example": 1},
                                            "loanId": {"type": "integer", "example": 1},
                                            "resourceId": {"type": "integer", "example": 1}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/loans/{loanId}": {
                "get": {
                    "summary": "Retrieve a loan account details",
                    "tags": ["Loans"],
                    "security": [{"BasicAuth": []}],
                    "parameters": [
                        {
                            "name": "loanId",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "integer"}
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Loan details returned",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "id": {"type": "integer", "example": 1},
                                            "accountNo": {"type": "string", "example": "000000001"},
                                            "status": {
                                                "type": "object",
                                                "properties": {
                                                    "id": {"type": "integer", "example": 300},
                                                    "code": {"type": "string", "example": "loanStatusType.active"},
                                                    "description": {"type": "string", "example": "Active"},
                                                    "pendingApproval": {"type": "boolean", "example": False},
                                                    "waitingForDisbursal": {"type": "boolean", "example": False},
                                                    "active": {"type": "boolean", "example": True},
                                                    "closedObligationsMet": {"type": "boolean", "example": False},
                                                    "closedWrittenOff": {"type": "boolean", "example": False},
                                                    "closedRescheduled": {"type": "boolean", "example": False},
                                                    "closed": {"type": "boolean", "example": False},
                                                    "overpaid": {"type": "boolean", "example": False}
                                                }
                                            },
                                            "clientId": {"type": "integer", "example": 1},
                                            "clientName": {"type": "string", "example": "Kampala first Client"},
                                            "clientOfficeId": {"type": "integer", "example": 2},
                                            "currency": {
                                                "type": "object",
                                                "properties": {
                                                    "code": {"type": "string", "example": "UGX"},
                                                    "name": {"type": "string", "example": "Uganda Shilling"},
                                                    "decimalPlaces": {"type": "integer", "example": 2},
                                                    "displaySymbol": {"type": "string", "example": "USh"},
                                                    "nameCode": {"type": "string", "example": "currency.UGX"},
                                                    "displayLabel": {"type": "string", "example": "Uganda Shilling (USh)"}
                                                }
                                            },
                                            "summary": {
                                                "type": "object",
                                                "properties": {
                                                    "principalDisbursed": {"type": "number", "example": 1000000.00},
                                                    "principalPaid": {"type": "number", "example": 0.00},
                                                    "principalOutstanding": {"type": "number", "example": 1000000.00},
                                                    "interestCharged": {"type": "number", "example": 240000.00},
                                                    "interestPaid": {"type": "number", "example": 0.00},
                                                    "interestOutstanding": {"type": "number", "example": 240000.00},
                                                    "totalExpectedRepayment": {"type": "number", "example": 1258000.00},
                                                    "totalRepayment": {"type": "number", "example": 0.00},
                                                    "totalOutstanding": {"type": "number", "example": 1258000.00}
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "components": {
            "securitySchemes": {
                "BasicAuth": {
                    "type": "http",
                    "scheme": "basic"
                }
            }
        }
    }

    os.makedirs(SCHEMAS_DIR, exist_ok=True)
    
    clients_path = os.path.join(SCHEMAS_DIR, "clients.yaml")
    with open(clients_path, "w", encoding="utf-8") as f:
        yaml.dump(clients_spec, f, default_flow_style=False, sort_keys=False)
    print(f"Saved clients schema to: {clients_path}")

    tx_path = os.path.join(SCHEMAS_DIR, "transactions.yaml")
    with open(tx_path, "w", encoding="utf-8") as f:
        yaml.dump(transactions_spec, f, default_flow_style=False, sort_keys=False)
    print(f"Saved transactions schema to: {tx_path}")

    loans_path = os.path.join(SCHEMAS_DIR, "loans.yaml")
    with open(loans_path, "w", encoding="utf-8") as f:
        yaml.dump(loans_spec, f, default_flow_style=False, sort_keys=False)
    print(f"Saved loans schema to: {loans_path}")

if __name__ == "__main__":
    main()
