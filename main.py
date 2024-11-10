import asyncio
from grove.factory import Factory
from proxmoxer import ProxmoxAPI
import seeed_dht
import yaml
import logging
from flask import Flask, jsonify
import threading

# Logging
logger = logging.getLogger("RPI-Temperature-Monitor")
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler = logging.FileHandler('main.log')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Load configuration from config.yml
with open("config.yml", "r") as config_file:
    config = yaml.safe_load(config_file)
    # Proxmox
    proxmox_config = config['proxmox']
    enabled_proxmox = proxmox_config['enabled']
    server_ip = proxmox_config['server_ip']
    username = proxmox_config['username']
    password = proxmox_config['password']
    verify_ssl = proxmox_config['verify_ssl']
    node = proxmox_config['node']
    # Temperature
    temperature_config = config['temperature']
    max_temp = temperature_config['limit']

try:
    # LCD 16x2 Characters
    lcd = Factory.getDisplay("JHD1802")
    rows, cols = lcd.size()
    lcd.clear()
except OSError as e:
    logger.error(f"Failed to initialize LCD display: {e}")
    lcd = None  # Fallback in case LCD fails


# Proxmox
proxmox_connected = False
if enabled_proxmox:
    try:
        proxmox = ProxmoxAPI(server_ip, user=username, password=password, verify_ssl=verify_ssl)
        proxmox_connected = True
        logger.info("Successfully connected to proxmox, connected features enabled!")
    except Exception as e:
        logger.error(f"Failed to connect to Proxmox: {e}")
        logger.error("Connected features unavailable!")

# Lock for sensor access
sensor_lock = threading.Lock()

def read_temp():
    with sensor_lock:
        sensor = seeed_dht.DHT("11", 12)
        humidity, temperature = sensor.read()
    return temperature, humidity

app = Flask(__name__)

@app.route('/temperature', methods=['GET'])
def get_temperature():
    temperature, humidity = read_temp()
    return jsonify({'temperature': temperature, 'humidity': humidity})

def display_text(line, text):
    if line < 0 or line >= rows:
        raise ValueError("Line number must be between 0 and {}".format(rows - 1))

    lcd.setCursor(line, 0)
    lcd.write(text)

async def display_temp_info(update_delay):
    while True:
        temperature, humidity = read_temp()
        logger.info(f"Temperature: {temperature} C, Humidity: {humidity} %")
        if lcd:
            lcd.clear()
            display_text(0, f"Temperature: {temperature} C")
            display_text(1, f"Humidity: {humidity} %")
        
        await asyncio.sleep(update_delay)

async def proxmox_temp_monitor(check_delay):
    while True:
        temperature, humidity = read_temp()
        if proxmox_connected:
            if temperature > max_temp:
                logger.error(f"Temperature is above {max_temp} C, Shutting down node {node}")
                try:
                    proxmox.nodes(node).status.shutdown.post()
                    logger.info(f"Shutdown command sent to node {node}")
                    break
                except Exception as e:
                    logger.error(f"Failed to send shutdown command to Proxmox node {node}: {e}")
        await asyncio.sleep(check_delay)

async def main():
    await asyncio.gather(display_temp_info(5), proxmox_temp_monitor(5))

def run_flask_app():
    app.run(host='0.0.0.0', port=5000)

if __name__ == '__main__':
    flask_thread = threading.Thread(target=run_flask_app)
    flask_thread.start()
    
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

    