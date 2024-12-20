# Temp Monitor

This is a simple python script that monitors a temperature data source over serial.

## Features
- Monitor temperature data over serial
- Record temperature data to a SQLite database file
- Warn the user if the temperature exceeds a certain threshold
- If enabled, send the temperature data to thingspeak
- If enabled, send a shutdown signal using the Proxmox API if the temperature exceeds a certain threshold
- Allow a custom temperature threshold to be set (and reset) by the user for testing purposes
- Web API for getting the current temperature and setting custom temperatures (/temperature {temp} (0-99) or /temperature {"reset"})
- Customizable settings in the config.yaml file
- OS independent, tested on Windows and Linux, should work on macOS as well (untested) Specify the serial port in the config.yaml file
- Default config file generated if not found

## Requirements
- Python 3.6 or higher
- pyserial
- requests
- pyyaml
- sqlite3
- flask
- proxmoxer
- (optional) thingspeak account
- (optional) Proxmox server

## Installation
1. Clone the repository
2. Install the required packages using pip
```bash
pip install -r requirements.txt
```
3. Edit the config.yaml file to your liking
4. Run the script
```bash
python temp_monitor.py
```

## Usage
- Run the script
- The script will generate a ```config.yaml``` and a ```temperature_data.db``` file if it does not exist
- The script will start monitoring the temperature data over serial and record it to the database while presenting it to over a web api at ```http://localhost:5050/temp```
- Custom temperatures can be set by sending a POST request to ```http://localhost:5050/temp``` with the desired temperature in the body (0-99) or by sending a POST request with the body ```{"reset"}``` to reset the temperature.

## Example API testing commands
- Set the temperature to 50
```bash
curl -X POST http://localhost:5050/temp -H "Content-Type: application/json" -d '{"temperature": 50}'
```
- Reset the temperature
```bash
curl -X POST http://localhost:5050/temp -H "Content-Type: application/json" -d '{"temperature": "reset"}'
```

## Configuration
The script will use the default settings in the config.yaml file if it is not found. The default settings are as follows, please check if the serial port is correct for your system:
```yaml
database:
  file_path: temperature_data.db

logging:
  file_path: app.log
  level: INFO
  log_temperature: false
  log_temperature_no_db: true
  log_thingspeak: false

arduino:
  windows_port: COM3
  unix_like_port: /dev/ttyACM0
  unknown_port: /dev/ttyACM0
  baud_rate: 9600
  poll_interval: 5

web:
  port: 5050
  address: 0.0.0.0

enabled_modules:
  - web
  - database

```



## License
[MIT](https://choosealicense.com/licenses/mit/)
```

# File: README.MD
