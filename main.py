import json
import logging
import os
import sys
import threading
import time
import serial
from flask import Flask, request, jsonify
from proxmoxer import ProxmoxAPI
import sqlite3
import yaml
import thingspeak

def read_config():

    try:
        with open('config.yaml', 'r') as config_file:
            config = yaml.safe_load(config_file)
            return config
    except Exception as e:
        default_config = {
            'database': {'file_path': 'temperature_data.db'},
            'logging': {'file_path': 'app.log', 'level': 'INFO', 'log_temperature': False, 'log_temperature_no_db': True, 'log_thingspeak': False},
            'arduino': {'windows_port': 'COM3', 'unix_like_port': '/dev/ttyACM0', 'unknown_port': '/dev/ttyACM0', 'baud_rate': 9600, 'poll_interval': 5},
            'web': {'port': 5050, 'address': '0.0.0.0'},
            'enabled_modules': ['web', 'database']}
        print(f"Error in reading the config file, creating new config.yaml. error: {e}")

        try:
            with open('config.yaml', 'w') as config_file:
                yaml.dump(default_config, config_file)
        except Exception as e:
            print(f"Error in creating the config file, continuing from memory without persistence: {e}")
            default_config = {
                'database': {'file_path': 'temperature_data.db'},
                'logging': {'file_path': 'app.log', 'level': 'INFO', 'log_temperature_no_db': True, 'log_thingspeak': False},
                'arduino': {'windows_port': 'COM3', 'unix_like_port': '/dev/ttyACM0', 'unknown_port': '/dev/ttyACM0', 'baud_rate': 9600, 'poll_interval': 5},
                'web': {'port': 5050, 'address': '0.0.0.0'},
                'enabled_modules': ['web']
            }
        finally:
            return default_config
app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=read_config()['logging']['level'],
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(read_config()['logging']['file_path']),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("main")

flask_logger = logging.getLogger('werkzeug')
flask_logger.setLevel(logging.INFO)
flask_logger.handlers = logger.handlers

def check_os():
    if os.name == 'nt':
        return 'windows'
    elif os.name == 'posix':
        return 'unix-like'
    else:
        return 'unknown'

def init_db():
    try:
        conn = sqlite3.connect("temperature_data.db")
        cursor = conn.cursor()
        cursor.execute("""
                CREATE TABLE IF NOT EXISTS temperature_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    temperature REAL NOT NULL,
                    humidity REAL NOT NULL,
                    status TEXT NOT NULL
                )
            """)
        conn.commit()
        conn.close()
        logger.info("Database created successfully.")
    except Exception as e:
        logger.error(f"Error in creating the database: {e}")
        return

def save_temperature_to_db(temperature, humidity, status):
    try:

        conn = sqlite3.connect("temperature_data.db")
        cursor = conn.cursor()
        cursor.execute("""
                INSERT INTO temperature_logs (timestamp, temperature, humidity, status)
                VALUES (datetime('now'), ?, ?, ?)
            """, (temperature, humidity, status))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error in saving the temperature data to the database: {e}")
        return

def send_data_to_thingspeak(temperature, humidity, status, channel_id):
    with open("thingspeak.secret", "r") as thingspeak_secret:
        thingspeak_api_key = thingspeak_secret.read().strip()
        channel = thingspeak.Channel(id=channel_id, api_key=thingspeak_api_key)
        if temperature is None or humidity is None or status is None:
            logger.error("Seen data is None, not sending to thingspeak.")
            logger.error(f"Temperature: {temperature}, Humidity: {humidity}, Status: {status}")
        else:
            try:
                channel.update({'field1': temperature, 'field2': humidity})
                if read_config()['logging']['log_thingspeak']:
                    logger.info(f"Temperature: {temperature}, Humidity: {humidity} sent to thingspeak.")

            except Exception as e:
                logger.error(f"Error in sending data to thingspeak: {e}")

def shutdown_all_hosts():

    # Create a connection to the proxmox server.
    with open("proxmox.secret", "r") as proxmox_secret:
        proxmox_password = proxmox_secret.read().strip()
        try:
            proxmox = ProxmoxAPI(
                read_config()['proxmox']['server_ip'],
                user=read_config()['proxmox']['username'],
                password=proxmox_password,
                verify_ssl=read_config()['proxmox']['verify_ssl']
            )

            # Get the list of all the nodes.
            nodes = proxmox.nodes.get()
            for i in nodes:
                logger.info(f"Shutting down the node: {i['node']}")
                # Shutdown the node.
                proxmox.nodes(i['node']).status.post(command='shutdown')

        except Exception as e:
            logger.error(f"Error in connecting to the proxmox server: {e}")
            return
        finally:
            logger.info('All the nodes have been shutdown successfully (If online).')
            return

def init_serial():
    serial_connection = serial.Serial()
    serial_connection.baudrate = 9600
    if check_os() == 'windows':
        serial_connection.port = read_config()['arduino']['windows_port']
    elif check_os() == 'unix-like':
        serial_connection.port = read_config()['arduino']['unix_like_port']

    serial_connection.timeout = 10

    while True:
        try:
            serial_connection.open()
            return serial_connection
        except serial.SerialException:
            logger.error('Error in opening the serial connection, retrying in 2 seconds.')
            time.sleep(2)

def send_data(data):
    serial_connection = init_serial()
    serial_connection.write(data.encode('utf-8'))
    return

def read_data():
    serial_connection = init_serial()
    try:
        data = serial_connection.readline().decode('utf-8')
    except UnicodeDecodeError:
        logger.error('Error in decoding the data')
        return {'temperature': 0, 'humidity': 0, 'status': 'error'}


    # Decode the data from json to components.
    try :
        data_dict = json.loads(data)
        return data_dict
    except json.JSONDecodeError:
        logger.error(f"Error in decoding the data: {data}")
        return {'temperature': 0, 'humidity': 0, 'status': 'error'}
@app.route('/', methods=['GET'])
def get_sensor_data():
    data = read_data()
    return jsonify(data)

@app.route('/temp', methods=['POST'])
def send_temp_to_arduino():
    data = request.json
    temperature = data['temperature']
    if temperature is None:
        return jsonify({'message': 'Temperature is not provided.'}), 400
    if temperature == 'reset':
        send_data('DHT')
        logger.info('The arduino is now using real data')
        return jsonify({'message': 'The arduino is now using real data.'})
    if not isinstance(temperature, int):
        return jsonify({'message': 'Temperature should be an integer.'}),400
    if temperature < 0 or temperature > 99:
        return jsonify({'message': 'Temperature should be between 0 and 99'}), 400

    send_data(f'temp {temperature}')
    logger.info(f"Temperature: {temperature} sent to the arduino.")
    return jsonify({'message': 'Temperature sent to the arduino.'})

def main():
    config = read_config()
    logger.info(f"Enabled Modules: {config['enabled_modules']}")
    logger.log(logging.INFO, f"OS: {check_os()}")
    logger.info(f'Polling rate: {config["arduino"]["poll_interval"]} seconds')
    if "database" in config['enabled_modules']:
        logger.info('Initializing the database.')
        init_db()
    else:
        logger.debug("Database service is not enabled in the config file.")

    logger.info('Starting the program.')

    while True:
        data = read_data()

        temperature = data['temperature']
        humidity = data['humidity']
        status = data['status']
        if "database" in config['enabled_modules']:
            if config['logging']['log_temperature']:
                logger.info(f"Temperature: {temperature}, Humidity: {humidity}, Status: {status}")
            save_temperature_to_db(
                temperature,
                humidity,
                status
            )

        else:
            if config['logging']['log_temperature_no_db']:
                logger.info(f"Temperature: {temperature}, Humidity: {humidity}, Status: {status}")



        if "thingspeak" in config['enabled_modules'] and os.path.exists("thingspeak.secret"):
            send_data_to_thingspeak(temperature, humidity, status, read_config()['thingspeak']['channel_id'])
        else:
            logger.debug("Thingspeak service is not enabled in the config file or no thingspeak.secret file.")

        if status == 'HIGH':
            logger.warning(f"Temperature({temperature}) is high")
            if "proxmox" in config['enabled_modules'] and os.path.exists("proxmox.secret"):
                shutdown_all_hosts()
                break
            else:
                logger.debug("Proxmox service is not enabled in the config file or no proxmox.secret file.")


        time.sleep(config['arduino']['poll_interval'])

    logger.info('Exiting the program.')
    sys.exit(0)

def run_main_thread_in_background():
    thread = threading.Thread(
        target=main,
        daemon=True
    )
    thread.start()

if __name__ == '__main__':
    if "web" in read_config()['enabled_modules']:
        logger.info('Starting the web server.')
        run_main_thread_in_background()
        app.run(
            debug=False,
            use_reloader=False,
            port=read_config()['web']['port'],
            host=read_config()['web']['address']

        )
    else:
        logger.debug('Starting without the web server.')
        main()


