import os
import random
import time
import json
from datetime import datetime
from multiprocessing import Process
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS, WriteOptions
import logging
from flask import Flask, request, Response
import requests
from itertools import product as cartesian_product

app = Flask(__name__)

handler = logging.FileHandler('application.log') 
handler.setLevel(logging.INFO)  
app.logger.addHandler(handler)  

bucket = "provider_prototype"
org = "PT Aplikanusa Lintasarta"
token = "w_It0QeKJanSyPUHiHU9SpQBdX4zj-jtm-ovqe6lSEzH7_wZ-mvFIc9Zdj0K_kcQvRi2jJGePp1eQGF6XRhYlg=="
url = "http://localhost:8086"

cities = ["Jakarta", "Bandung", "Surabaya", "Medan", "Semarang", "Yogyakarta", "Bali"]

# Initiate Influx Client
client = InfluxDBClient(url=url, token=token, org=org)
write_api = client.write_api(write_options=WriteOptions(batch_size=500, flush_interval=10_000,
                                                        jitter_interval=2_000, retry_interval=5_000))

# Path to data 
data_file_path = "provider_data.json"
processes = []

@app.before_request
def log_request_info():
    user_agent = request.headers.get('User-Agent', '')
    sia_number = request.args.get('sia_number') 
    app.logger.info('User-Agent: %s, SIA Number: %s', user_agent, sia_number)
    if 'grafana' in user_agent.lower():
        app.logger.info('API call: %s %s', request.method, request.url)
        log_api_operation("POST")

@app.route("/query", methods=["POST"])
def handle_grafana_get():
    app.logger.info('Received request for /query')
    query = request.args.get('query')
    app.logger.info(f'Grafana GET request: {query}')
    
    r = requests.get(url + '/query', params={'q': query})
    
    app.logger.info('Finished handling request for /query')
    return Response(r.text, mimetype="application/json")

@app.route("/start", methods=["POST"])
def start_data_generation():
    global processes
    if processes:
        return "Data generation is already running", 400
    else:
        processes = [Process(target=generate_data_simultaneously) for _ in range(50)]
        for p in processes:
            p.start()
        return "Data generation started", 200

@app.route("/stop", methods=["POST"])
def stop_data_generation():
    global processes
    for p in processes:
        p.terminate()
    processes = []
    return "Data generation stopped", 200

def load_or_generate_data():
    if os.path.exists(data_file_path) and os.path.getsize(data_file_path) > 0:
        with open(data_file_path, 'r') as f:
            provider_data = json.load(f)
    else:
        provider_data = {str(i).zfill(3): {'Product': random.choice(["MetroE", "Internet", "IPVPN"]),
                                           'City_A': random.choice(cities),
                                           'City_B': random.choice(cities),
                                           'Endpoint_A': random.choice(["FO", "Radio", "VSAT"]),
                                           'Endpoint_B': random.choice(["FO", "Radio", "VSAT"])} 
                         for i in range(1, 51)}
        with open(data_file_path, 'w') as f:
            json.dump(provider_data, f)
            log_api_operation("POST")
    return provider_data

def log_api_operation(operation_type):
    current_time = datetime.utcnow()
    point = Point("api_calls") \
        .tag("operation_type", operation_type) \
        .field("_value", 1) \
        .time(current_time)
    write_api.write(bucket=bucket, record=point)
    write_api.flush()

provider_data = load_or_generate_data()

def generate_data_simultaneously():
    all_combinations = list(cartesian_product(['A', 'B'], range(1, 51)))
    # Keep generating data 
    while True:
        # Shuffle combinations
        random.shuffle(all_combinations)
        for provider, user in all_combinations:
            data = provider_data[str(user).zfill(3)]
            product = data['Product']
            city_a = data['City_A']
            city_b = data['City_B']
            endpoint_a = data['Endpoint_A']
            endpoint_b = data['Endpoint_B']
            points = []
            generate_data(provider, user, city_a, city_b, product, endpoint_a, endpoint_b, points)
        
        time.sleep(1)

def generate_data(provider, user, city_a, city_b, product, endpoint_a, endpoint_b, points):
    year = str((datetime.utcnow()).year)
    three_digits = "000"
    user_number = str(user).zfill(3)  
    sia_number = year + three_digits + user_number
    bandwidth = random.randint(1, 100)

    up_counter = 0
    total_counter = 0

    current_time = datetime.utcnow()

    utilization = random.randint(0, 100)
    up_down = random.choices(["Up", "Down"], weights=[98, 2])[0] 
    latency = random.randint(5, 80)
    jitters = random.randint(0, 100)

    if up_down == "Up":
        up_counter += 1
    total_counter += 1
    uptime_percentage = (up_counter / total_counter) * 100.0

    point = Point("prototype") \
        .tag("Provider", provider) \
        .tag("SIA_Number", sia_number) \
        .tag("Product", product) \
        .tag("City_A", city_a) \
        .tag("City_B", city_b) \
        .tag("Endpoint_A", endpoint_a) \
        .tag("Endpoint_B", endpoint_b) \
        .tag("User", user_number) \
        .field("Bandwidth", bandwidth) \
        .field("Utilization", utilization) \
        .field("Up_and_Downs", up_down) \
        .field("Latency", latency) \
        .field("Jitters", jitters) \
        .field("Uptime_Percentage", uptime_percentage) \
        .time(current_time)
    points.append(point)
    
    # Print the data point
    print(f"Provider: {provider}, SIA_Number: {sia_number}, City A: {city_a}, City B:{city_b}, Product: {product}, Bandwidth: {bandwidth}, Utilization: {utilization}, Up_down: {up_down}, Endpoint_City_A: {endpoint_a}, Endpoint_City_B: {endpoint_b}, Latency: {latency}, Jitters: {jitters}, Uptime_Percentage: {uptime_percentage}, Time: {current_time}")
    
    
    # if more than 10 points have been generated, write them to InfluxDB
    if len(points) >= 10:
        write_api.write(bucket=bucket, record=points)
        points.clear()

    # if there are any remaining points, write them to InfluxDB
    if points:
        write_api.write(bucket=bucket, record=points)
        
if __name__ == "__main__":
    app.run(debug=True)
