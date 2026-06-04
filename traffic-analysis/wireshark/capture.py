import subprocess
import time
import os
import sys

PCAP_FILE = "d:/open-banking-automation-sandbox/traffic-analysis/captured-flows/traffic.pcap"
SEED_SCRIPT = "d:/open-banking-automation-sandbox/automation/seed.py"

def check_tshark():
    try:
        subprocess.run(["tshark", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except FileNotFoundError:
        win_path = "C:\\Program Files\\Wireshark\\tshark.exe"
        if os.path.exists(win_path):
            os.environ["PATH"] += os.path.pathsep + "C:\\Program Files\\Wireshark"
            return True
        return False

def main():
    if not check_tshark():
        print("Error: tshark not found in PATH")
        sys.exit(1)

    os.makedirs(os.path.dirname(PCAP_FILE), exist_ok=True)
    if os.path.exists(PCAP_FILE):
        try:
            os.remove(PCAP_FILE)
        except Exception as e:
            print(f"Warning: could not remove old PCAP: {e}")

    tshark_cmd = [
        "tshark",
        "-i", "9",
        "-f", "tcp port 8080",
        "-w", PCAP_FILE
    ]

    print("Starting packet capture...")
    tshark_proc = subprocess.Popen(tshark_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(2)

    print("Running seeding script...")
    try:
        seed_proc = subprocess.run(["python", SEED_SCRIPT], capture_output=True, text=True)
        print(seed_proc.stdout)
        if seed_proc.stderr:
            print(f"Seed Error: {seed_proc.stderr}", file=sys.stderr)
    except Exception as e:
        print(f"Error running seed script: {e}")

    time.sleep(1)

    print("Stopping capture...")
    tshark_proc.terminate()
    try:
        tshark_proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        tshark_proc.kill()

    print(f"PCAP written to: {PCAP_FILE}")

if __name__ == "__main__":
    main()
