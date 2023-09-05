# Check if earthworm is receiving data
from enum import Enum
import os
import subprocess
import time


class Status(Enum):
    """ Enum indicates the status of the health check"""
    HEALTHY = 1
    UNHEALTHY = 2
    ERROR = 3


def set_ew_env_variables(env: dict[str, str]) -> None:
    """ Set earthworm variables necessary for sniffwave command to function"""
    if "EW_HOME" not in env:
        env["EW_HOME"] = "/home/daniel/ew"
    if "EW_VERSION" not in env:
        env["EW_VERSION"] = "earthworm_7.10"
    if "SYS_NAME" not in env:
        env["SYS_NAME"] = "hostname"
    if "EW_INSTALLATION" not in env:
        env["EW_INSTALLATION"] = "INST_SSN"
    if "EW_PARAMS" not in env:
        env["EW_PARAMS"] = "/home/daniel/ew/pozo/params/"
    if "EW_LOG" not in env:
        env["EW_LOG"] = "/home/daniel/ew/pozo/log/"
    if "EW_DATA_DIR" not in env:
        env["EW_DATA_DIR"] = "/home/daniel/ew/pozo/data/"
        env["PATH"] = "/home/daniel/ew/earthworm_7.10/bin:"


def check_connection() -> Status:
    """ Check that the connection to the SSN server is established.
    """
    address = "132.247.71.225:16401"
    command = ["ss", "-tnp"]
    result = subprocess.run(
        command,
        shell=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    if result.returncode == 0:
        text = result.stdout
        if address in text:
            return Status.HEALTHY
        else:
            return Status.UNHEALTHY
    else:
        return Status.ERROR


def check_sniff() -> Status:
    """ Use 'sniffwave' command to check if earthworm is receiving data.
    """
    command = ["sniffwave",  "WAVE_RING"]
    env = os.environ.copy()
    set_ew_env_variables(env)
    process = subprocess.Popen(
        command,
        shell=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env
    )
    time.sleep(1)
    process.terminate()
    stdout, stderr = process.communicate()

    if len(stdout) > 0:
        return Status.HEALTHY

    return Status.UNHEALTHY


def check_logs() -> tuple[Status, str]:
    """ Check the logs of the import_ack module from earthworm.


    """
    logs_path = "/home/daniel/ew/pozo/log/"
    import_files = []
    root = ""
    for root, _, file_list in os.walk(logs_path):
        for file in file_list:
            if "import" in file:
                import_files.append(file)

    if not import_files:
        return Status.ERROR, "No log files found"

    import_files.sort()
    latest_log = os.path.join(root, import_files[-1])

    with open(latest_log) as fp:
        for line in fp.readlines():
            line = line.strip()
            if "Failed to set up TCP client connection" in line:
                print("Found error")
                return Status.UNHEALTHY, latest_log

    return Status.HEALTHY, ""


def main() -> None:
    """ Check that earthworm has a connection established for receiving data,
        that the wave ring is receiving data, and that there are no connection
        issues in earthworm logs.
    """
    conn_status = check_connection()
    if conn_status == Status.HEALTHY:
        print("Connection to SSN is healthy")
    elif conn_status == Status.UNHEALTHY:
        print("Failed to establish connection to SSN")
    else:
        print(f"Connection health check failed")

    sniff_status = check_sniff()
    if sniff_status == Status.HEALTHY:
        print("Earthworm is receiving data")
    elif sniff_status == Status.UNHEALTHY:
        print("Earthworm is not receiving data")
    else:
        print("Sniff health check failed")

    if conn_status == Status.UNHEALTHY or sniff_status == Status.UNHEALTHY:
        log_status, log_file = check_logs()
        if log_status == Status.HEALTHY:
            print("No issues find in logs")
        elif log_status == Status.UNHEALTHY:
            print(f"Found issues in log: {log_file}")
        else:
            print(f"Error: logs health check failed. {log_file}")


if __name__ == "__main__":
    main()
