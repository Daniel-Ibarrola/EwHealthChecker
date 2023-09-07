# Earthworm Health Checker

The Earthworm Health Checker is a Python script designed to perform health checks for an Earthworm system, which is commonly used for seismic data processing. This script verifies the following aspects of the Earthworm system:

1. **Connection to the SSN Server:** It checks whether the connection to the (SSN) server is established.
2. **Data Reception:** It uses the 'sniffwave' command to determine if Earthworm is actively receiving data.
3. **Log Analysis:** The script examines the logs of the import_ack module from Earthworm for any connection issues or errors.

If configured, the results of these health checks can be sent to a Telegram channel, providing real-time notifications about the Earthworm system's status.

## Usage

Clone or download the script to your local environment.
```shell
git clone https://github.com/Daniel-Ibarrola/EwHealthChecker
```
Create a virtual environment and install dependencies:

```shell
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Optionally, Set up a Telegram bot for notifications. Create a .env file with the following variables 
BOT_TOKEN and CHAT_ID, which contain the token of the bot you want to use and the id of
the chats where the messages will be sent.

Run the script using the following command:

```shell
python check_health.py
```

You can customize the script behavior with the following optional command-line arguments:
- `--interval` or `-i`: Set the interval (in minutes) for health checks (default is 30 minutes).
- `--telegram` or `-t`: Enable Telegram notifications.
- `--good-news` or `-g`: Report healthy status to Telegram (by default, only unhealthy status is reported).


## Author

This script was created by Daniel Ibarrola.

## Acknowledgments

- The Earthworm Health Checker script is based on the Earthworm seismic data processing system.
