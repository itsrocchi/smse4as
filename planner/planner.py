from calendar import c
import time
import pika 
from influxdb_client import InfluxDBClient, Point, QueryApi
import json
import re
import os


PIKA_USER = os.getenv("PIKA_USER")
PIKA_PASSWORD = os.getenv("PIKA_PASSWORD")

# Define credentials
credentials = pika.PlainCredentials(PIKA_USER, PIKA_PASSWORD)

# Rabbitmq configuration
connection = pika.BlockingConnection(pika.ConnectionParameters(host='host.docker.internal', port=5672, credentials=credentials))
channel = connection.channel()

INFLUXDB_URL = os.getenv("INFLUXDB_URL")
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN")
INFLUXDB_ORG = os.getenv("INFLUXDB_ORG")
INFLUXDB_BUCKET = os.getenv("INFLUXDB_BUCKET")

file_path = "/shared/actuators.json"

# Initialize InfluxDB client
influx_client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
query_api = influx_client.query_api()

def query_influxdb_topic(topic, time_range="-20s"):
    """
    Queries InfluxDB for a specific topic.
    """
    query = f"""
    from(bucket: "{INFLUXDB_BUCKET}") 
    |> range(start: {time_range})
    |> filter(fn: (r) => r._measurement == "mqtt_consumer")
    |> filter(fn: (r) => r.topic == "{topic}")
    |> filter(fn: (r) => r._field == "state")
    |> sort(columns: ["_time"], desc: true)
    |> limit(n: 1)
    """
    try:
        tables = query_api.query(query)
        results = []
        for table in tables:
            for record in table.records:
                results.append(
                    f"Time: {record.get_time()}, State: {record.get_value()}"
                )
        return results if results else f"No data found for topic '{topic}'."
    except Exception as e:
        return f"Error querying InfluxDB for topic '{topic}': {e}"
    

def generate_plans(results_dict):

    # create a new dictionary to store the values of the actuators read from the actuators.json file:
    
    actuators = {}
    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            try:
                actuators = json.load(file)
            except json.JSONDecodeError:
                actuators = {}

    #print("State of the actuators:", actuators)
    #print("Results Dictionary:", results_dict)

    """ in actuators c'è lo stato "attuale" degli attuatori, mentre in result dict c'è lo stato "attuale" della room
        ora per ogni stanza ho bisogno di un dizionario del tipo: 
        roomX: {
            {presence: result_dict['analysed/room/roomX/presence'], door: actuators[roomX][door]}, 
            {temperature: result_dict['analysed/room/roomX/temperature'], hvac_temp: actuators[roomX][hvac_temp]}, 
            {humidity: result_dict['analysed/room/roomX/humidity'], hvac_hum: actuators[roomX][hvac_hum]}, 
            {light: result_dict['analysed/room/roomX/light'], adaptive_light: actuators[roomX][adaptive_light]}, 
            {air_quality: result_dict['analysed/room/roomX/air_quality'], ventilation: actuators[roomX][ventilation]}}
    """

    
    snapshot = {}
    for room in actuators.keys():
        snapshot[room] = {
            "door": {"sensor": results_dict.get(f"analysed/room/{room}/presence", "unknown"), "door": actuators[room].get("door", "unknown")},
            "hvac_temp": {"sensor": results_dict.get(f"analysed/room/{room}/temperature", "unknown"), "hvac_temp": actuators[room].get("hvac_temp", "unknown")},
            "hvac_hum": {"sensor": results_dict.get(f"analysed/room/{room}/humidity", "unknown"), "hvac_hum": actuators[room].get("hvac_hum", "unknown")},
            "adaptive_light": {"sensor": results_dict.get(f"analysed/room/{room}/light", "unknown"), "adaptive_light": actuators[room].get("adaptive_light", "unknown")},
            "ventilation": {"sensor": results_dict.get(f"analysed/room/{room}/air_quality", "unknown"), "ventilation": actuators[room].get("ventilation", "unknown")}
        }

    print("Snapshot:", snapshot)
    

    #in generale, se snapshot[room][metric]['sensor'] è 0 allora non faccio nulla
    #se snapshot[room][metric]['sensor'] è 1 e snapshot[room][metric]['actuator'] è 0, allora plan[room][metric] = -1
    #se snapshot[room][metric]['sensor'] è 1 e snapshot[room][metric]['actuator'] è -1, allora plan[room][metric] = -2
    #se snapshot[room][metric]['sensor'] è 1 e snapshot[room][metric]['actuator'] è maggiore o uguale 1, allora plan[room][metric] = 0
    #se snapshot[room][metric]['sensor'] è -1 e snapshot[room][metric]['actuator'] è 0, allora plan[room][metric] = 1
    #se snapshot[room][metric]['sensor'] è -1 e snapshot[room][metric]['actuator'] è 1, allora plan[room][metric] = 2
    #se snapshot[room][metric]['sensor'] è -1 e snapshot[room][metric]['actuator'] è minore o uguale -1, allora plan[room][metric] = 0

    #quanto detto vale nel caso generale, per la metrica presence, se snapshot[room][presence]['sensor'] è 2 allora plan[room][presence] = 1
    #se snapshot[room][presence]['sensor'] è 1oppure0 allora plan[room][presence] = 0

    plans = {}

    for room in snapshot.keys():
        plans[room] = {}
        for actuator in snapshot[room].keys():
            sensor_value = float(snapshot[room][actuator]['sensor'])  # Conversione
            actuator_value = snapshot[room][actuator].get('actuator', 0)  # Assicurati che esista

            if actuator == "door":
                if sensor_value == 1:
                    plans[room][actuator] = 1
                else:
                    plans[room][actuator] = 0
            else:
                if sensor_value == 0:
                    plans[room][actuator] = 0
                elif sensor_value == 1:
                    if actuator_value == 0:
                        plans[room][actuator] = -1
                    elif actuator_value == -1:
                        plans[room][actuator] = -2
                    elif actuator_value >= 1:
                        plans[room][actuator] = 0
                elif sensor_value == -1:
                    if actuator_value == 0:
                        plans[room][actuator] = 1
                    elif actuator_value == 1:
                        plans[room][actuator] = 2
                    elif actuator_value <= -1:
                        plans[room][actuator] = 0

    print("Plans:", plans)
    return plans

    




def run():

    

    # Load room configuration from JSON file
    config_path = '/app/rooms_config.json'
    with open(config_path, 'r') as config_file:
        room_config = json.load(config_file)
        n_rooms = len(room_config)  # Count the number of rooms in the dictionary

    metrics = ["presence", "temperature", "humidity", "light", "air_quality"]
    topics = [f"analysed/room/room{i}/{metric}" for i in range(1, n_rooms + 1) for metric in metrics]

    results_dict = {}

    for topic in topics:
        print(f"\nQuerying InfluxDB for topic '{topic}'...")
        result = query_influxdb_topic(topic)
        if isinstance(result, list):
            for res in result:
                results_dict[f"{topic}"] = res.split(", State: ")[1]
        else:
            results_dict[f"{topic}"] = result
        #print(result)

    #print("\nFinished querying predefined topics.")
    #print("Results Dictionary:", results_dict)

    plans = generate_plans(results_dict)
    #print("\nGenerated plans:", plans)

    channel.queue_declare(queue='planner_queue')
    json_message = json.dumps(plans)

    channel.basic_publish(exchange='', routing_key='planner_queue', body=json_message)
    print(" [x] Sent %r" % json_message)

    connection.close()


if __name__ == "__main__":
    time.sleep(20)  # Wait for InfluxDB to start
    run()