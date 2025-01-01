# Temp Monitor
This is a simple Python script that monitors a temperature data source over serial. 

## Features
- Monitor temperature data over serial
- Record temperature data to a SQLite database file
- Warn the user if the temperature exceeds a certain threshold
- If enabled, send the temperature data to ThingSpeak
- If enabled, send a shutdown signal using the Proxmox API if the temperature exceeds a certain threshold
- Allow a custom temperature threshold to be set (and reset) by the user for testing purposes
- Web API for getting the current temperature and setting custom temperatures (`/temperature {temp} (0-99)` or `/temperature {"reset"}`)
- Customizable settings in the `config.yaml` file
- OS independent, tested on Windows and Linux, should work on macOS as well (untested)
- Ability to specify the serial port in the `config.yaml` file
- Default config file generated if not found

## Requirements
- Python 3.6 or higher
- pyserial
- requests
- pyyaml
- sqlite3
- flask
- proxmoxer
- (optional) ThingSpeak account
- (optional) Proxmox server

## Installation
1. Clone the repository.
2. Install the required packages using pip:
   `bash
   pip install -r requirements.txt
   `
3. Edit the `config.yaml` file to your liking.
4. Provide the required API keys file if you want to use `thingspeak.secret` and/or `proxmox.secret`.
