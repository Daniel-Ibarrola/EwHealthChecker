# Check if earthworm is receiving data
import argparse
from enum import Enum
import logging
import os
import subprocess
import sys
import time
from telegrambot import TelegramBot
from typing import Optional


class Status(Enum):
    """ Enum indicates the status of the health check"""
    HEALTHY = 1
    UNHEALTHY = 2
    ERROR = 3


def get_logger() -> logging.Logger:
    """ Get the logger with a stream handler. Doesn't log to files.
     """
    logger = logging.getLogger(__name__)
    formatter = logging.Formatter(
        '%(asctime)s [%(name)-12s] %(levelname)-5s %(message)s'
    )

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    logger.setLevel(logging.INFO)

    return logger


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
    command = ["sniffwave", "WAVE_RING"]
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


def send_to_telegram(
                 msg: str,
                 status: Status,
                 report_healthy: bool,
                 logger: logging.Logger,
                 bot: Optional[TelegramBot],
                 chat_id: str = "") -> None:
    """ Send health check status to telegram
    """
    if bot is not None:
        if (status == Status.HEALTHY and report_healthy) \
                or status == Status.UNHEALTHY:
            success, status_code, _ = bot.send_message(msg, chat_id)
            if not success:
                logger.info(f"Failed to send message with bot. Status code: {status_code}")


def health_checks(logger: logging.Logger,
                  bot: Optional[TelegramBot] = None,
                  chat_id: str = "",
                  report_healthy: bool = False
                  ) -> None:
    """ Check that earthworm has a connection established for receiving data,
        that the wave ring is receiving data, and that there are no connection
        issues in earthworm logs.

        If a telegram bot is given the status of the health checks will be sent to
        telegram.
    """
    conn_status = check_connection()
    if conn_status == Status.HEALTHY:
        msg = "Connection to SSN is healthy"
    elif conn_status == Status.UNHEALTHY:
        msg = "Failed to establish connection to SSN"
    else:
        msg = f"Connection health check failed"

    logger.info(msg)
    send_to_telegram(msg, conn_status, report_healthy, logger, bot, chat_id)

    sniff_status = check_sniff()
    if sniff_status == Status.HEALTHY:
        msg = "Earthworm is receiving data"
    elif sniff_status == Status.UNHEALTHY:
        msg = "Earthworm is not receiving data"
    else:
        msg = "Sniff health check failed"

    logger.info(msg)
    send_to_telegram(msg, conn_status, report_healthy, logger, bot, chat_id)

    if conn_status == Status.UNHEALTHY or sniff_status == Status.UNHEALTHY:
        log_status, log_file = check_logs()
        if log_status == Status.HEALTHY:
            msg = "No issues find in logs"
        elif log_status == Status.UNHEALTHY:
            msg = f"Found issues in log: {log_file}"
        else:
            msg = f"Error: logs health check failed. {log_file}"

    logger.info(msg)
    send_to_telegram(msg, conn_status, report_healthy, logger, bot, chat_id)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Perform regular health checks for earthworm"
    )
    parser.add_argument(
        "--interval",
        "-i",
        type=float,
        default=30,
        help="Interval of the health checks in minutes"
    )
    parser.add_argument(
        "--telegram",
        "-t",
        action="store_true",
        help="Whether to send the status of the health checks"
             " to telegram"
    )
    parser.add_argument(
        "--good-news",
        "-g",
        action="store_true",
        help="Whether to send the status of the health checks to telegram"
             " if they are healthy. Default behavior is to report only"
             " unhealthy status."
    )
    return parser.parse_args()


def main():
    args = parse_args()
    interval = args.interval * 60
    use_bot: bool = args.telegram
    report_healthy: bool = args.good_news

    if use_bot:
        bot = TelegramBot(os.environ["BOT_TOKEN"])
        chat_id = os.environ["CHAT_ID"]
    else:
        bot = None
        chat_id = ""

    logger = get_logger()
    logger.info("Earthworm Health Checker")
    logger.info(f"Health checks interval: {interval / 60} minute(s)")

    while True:
        health_checks(logger, bot, chat_id, report_healthy)
        time.sleep(interval)


if __name__ == "__main__":
    main()
