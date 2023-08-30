This repository contains prototype_2.py, a Python script designed for real-time data simulation and monitoring.
This script interfaces with InfluxDB, utilizing its client API to write points.
The program is also equipped with a basic Flask app to log information and handle API requests from Grafana.

Features: 

- Real-Time Data Generation: Generates simulated data for 50 different providers, sending it to InfluxDB.
- Logging: Logs every API request, including specifics like the User-Agent and SIA Number.
- Flask API: Allows the data generation process to be started and stopped via HTTP requests.
- Multi-Processing: Spawns multiple processes to simulate the data simultaneously.

How to Use:
- Clone this repository.
- Install the required packages: pip install <library>
- Run python prototype_2.py.

API Endpoints:
- /start: Starts the data generation. POST request.
- /stop: Stops the data generation. POST request.
- /query: Handles Grafana GET queries.

File Structure:
- application.log: Log file.
- provider_data.json: JSON file containing data about different providers.

Dependencies :
- Flask
- InfluxDBClient
- requests

Notes:
- The INFLUXDB_TOKEN, INFLUXDB_ORG, and INFLUXDB_BUCKET must be set in the environment variables or directly in the script.
- Make sure InfluxDB is running at the specified URL and port.

About the Code:
- import os, random, time, json, datetime, multiprocessing, influxdb_client, logging, flask, requests, itertools: Imported modules.
- app = Flask(__name__): Initializes Flask app.
- handler = logging.FileHandler('application.log'): Sets up logging.
- client = InfluxDBClient(...): Initializes InfluxDB Client.
- load_or_generate_data(): Loads existing or generates new provider data.
- start_data_generation() and stop_data_generation(): Start and stop data generation via API.
- generate_data_simultaneously(): Function to generate data simultaneously for different providers.
Feel free to edit this README.md as needed.





