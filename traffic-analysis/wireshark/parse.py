import subprocess
import json
import os
import sys

PCAP_FILE = "d:/open-banking-automation-sandbox/traffic-analysis/captured-flows/traffic.pcap"
OUTPUT_FILE = "d:/open-banking-automation-sandbox/traffic-analysis/captured-flows/traffic.json"

def find_key_recursive(d, target_key):
    if not isinstance(d, dict):
        return None
    if target_key in d:
        return d[target_key]
    for k, v in d.items():
        if isinstance(v, dict):
            res = find_key_recursive(v, target_key)
            if res is not None:
                return res
    return None

def extract_body(http_layer):
    if "http.file_data" in http_layer:
        raw_hex = http_layer["http.file_data"].replace(":", "")
        try:
            raw_bytes = bytes.fromhex(raw_hex)
            raw_text = raw_bytes.decode("utf-8", errors="ignore")
            try:
                return json.loads(raw_text)
            except Exception:
                return raw_text
        except Exception:
            return http_layer["http.file_data"]
    return None

def main():
    if not os.path.exists(PCAP_FILE):
        print(f"Error: PCAP file not found at {PCAP_FILE}")
        sys.exit(1)

    tshark_cmd = [
        "tshark",
        "-r", PCAP_FILE,
        "-d", "tcp.port==8080,http",
        "-2",
        "-R", "http.request or http.response",
        "-T", "json"
    ]

    print("Running tshark to extract HTTP frames...")
    res = subprocess.run(tshark_cmd, capture_output=True, text=True, encoding="utf-8")
    if res.returncode != 0:
        print(f"Error running tshark: {res.stderr}")
        sys.exit(1)

    try:
        raw_packets = json.loads(res.stdout)
    except Exception as e:
        print(f"Error decoding tshark output: {e}")
        sys.exit(1)

    flows = []
    for pkt in raw_packets:
        layers = pkt.get("_source", {}).get("layers", {})
        if "http" not in layers:
            continue

        http = layers["http"]
        frame = layers.get("frame", {})
        tcp = layers.get("tcp", {})

        entry = {
            "packet_number": int(frame.get("frame.number", 0)),
            "time_relative": float(frame.get("frame.time_relative", 0.0)),
            "tcp_stream": int(tcp.get("tcp.stream", -1)),
            "src_ip": layers.get("ip", {}).get("ip.src", ""),
            "dst_port": int(tcp.get("tcp.dstport", 0))
        }

        method = find_key_recursive(http, "http.request.method") or find_key_recursive(http, "http.request_method")
        uri = find_key_recursive(http, "http.request.uri") or find_key_recursive(http, "http.request_uri")
        status_code = find_key_recursive(http, "http.response.code") or find_key_recursive(http, "http.response_code")

        if method:
            entry["type"] = "request"
            entry["method"] = method
            entry["uri"] = uri
            body = extract_body(http)
            if body:
                entry["body"] = body
        elif status_code:
            entry["type"] = "response"
            entry["status_code"] = int(status_code)
            body = extract_body(http)
            if body:
                entry["body"] = body
        else:
            continue

        flows.append(entry)

    flows.sort(key=lambda x: x["packet_number"])

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(flows, f, indent=2)

    print(f"Saved {len(flows)} HTTP transactions to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
