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

## How to read the temperature over the API
To read the current temperature, send a GET request to the endpoint, this returns the current temperature as a JSON object.

> Example command: ```curl http://localhost:5050```

## How to set a custom temperature
To set a custom temperature, make sure the `commands_enabled` configuration option is set to `True` send a POST request to the `/temp` endpoint with the desired temperature as the body. The temperature should be an integer between 0 and 99. For example, to set the temperature to 50, you would send a POST request to `/temperature` with the body `50`.

> Example command: ```curl -X POST http://localhost:5050/temp -H "Content-Type: application/json" -d '{"temperature": 50}'```

## How to reset the temperature
To reset the temperature to the default value, send a POST request to the `/temp` endpoint with the body `{"temperature": "reset"}`.

> Example command: ```curl -X POST http://localhost:5050/temp -H "Content-Type: application/json" -d '{"temperature": "reset"}'```
