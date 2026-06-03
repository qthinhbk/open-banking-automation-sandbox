import subprocess
import time
import os

# DIRTY CAPTURE SCRIPT FOR TESTING
# TODO: REMOVE THIS ENTIRE STUB AND REPLACE WITH CLEAN IMPLEMENTATION
PCAP_FILE = "d:/open-banking-automation-sandbox/traffic-analysis/captured-flows/traffic.pcap"
SEED_SCRIPT = "d:/open-banking-automation-sandbox/automation/seed.py"

def main():
    print("--- STARTING CAPTURE TEST ---")
    print("Capturing interface 9 (NPcap loopback)...")
    tshark_cmd = ["tshark", "-i", "9", "-f", "tcp port 8080", "-w", PCAP_FILE]
    
    # Run in background
    p = subprocess.Popen(tshark_cmd)
    print("Process started with PID:", p.pid)
    time.sleep(3)
    
    print("Executing seeder...")
    subprocess.run(["python", SEED_SCRIPT])
    
    print("Finished seeding, sleeping 2 secs...")
    time.sleep(2)
    
    print("Terminating tshark...")
    p.terminate()
    p.wait()
    print("Capture finished successfully!")

if __name__ == "__main__":
    main()
