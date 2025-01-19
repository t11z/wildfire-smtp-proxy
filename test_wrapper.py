import subprocess
import os
import signal
import time
import sys

# Paths to the scripts
SMTP_PROXY_SCRIPT = "wildfire_proxy.py"
TEST_SCRIPT = "test.py"

# Start the logs
def log(message, level="INFO"):
    print(f"[{level}] {message}")

# Function to start the SMTP proxy
def start_smtp_proxy():
    log("Starting SMTP Proxy...")
    process = subprocess.Popen(
        ["python3", SMTP_PROXY_SCRIPT],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid,
    )
    log("SMTP Proxy started.")
    return process

# Function to run the test script
def run_test_script():
    log("Running Test Script...")
    try:
        result = subprocess.run(
            ["python3", TEST_SCRIPT],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        log(f"Test Script Output:\n{result.stdout}")
        if result.returncode == 0:
            log("Test Script executed successfully.", "SUCCESS")
            return True
        else:
            log(f"Test Script failed with errors:\n{result.stderr}", "ERROR")
            return False
    except Exception as e:
        log(f"Error running Test Script: {e}", "ERROR")
        return False

# Function to stop the SMTP proxy process
def stop_smtp_proxy(process):
    log("Stopping SMTP Proxy...")
    try:
        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        log("SMTP Proxy stopped.")
    except Exception as e:
        log(f"Error stopping SMTP Proxy: {e}", "ERROR")

# Main function
def main():
    smtp_process = None
    try:
        # Step 1: Start SMTP Proxy
        smtp_process = start_smtp_proxy()
        time.sleep(5)  # Wait until the SMTP proxy is fully started

        # Step 2: Run the test script
        test_result = run_test_script()

        # Return result
        if test_result:
            log("All tests passed successfully!", "SUCCESS")
            sys.exit(0)  # Success
        else:
            log("Tests failed.", "FAILURE")
            sys.exit(1)  # Failure
    except Exception as e:
        log(f"Error in wrapper script: {e}", "ERROR")
        sys.exit(1)  # Failure
    finally:
        # Step 3: Stop SMTP Proxy
        if smtp_process:
            stop_smtp_proxy(smtp_process)

if __name__ == "__main__":
    main()
