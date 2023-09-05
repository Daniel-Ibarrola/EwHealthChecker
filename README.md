# Earthworm Health Checker

Program to check that earthworm is receiving data. It performs three health
checks:

1. Checks that there is an established connection to the address where earthworm
expects to receive data from.
2. Checks that there is data in earthworm's wave ring.
3. Checks the latest logs to see if there are nay connectivity issues registered.

## Installation

Create virtual environment, activate it and run the program:

```shell
python3.11 -m venv venv
source venv/bin/activate
python check_health.py
```
