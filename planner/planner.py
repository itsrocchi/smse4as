import time
import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient, Point, QueryApi
import json
import re


# InfluxDB configuration
INFLUXDB_URL = "http://host.docker.internal:8086"
INFLUXDB_TOKEN = "VKuvU-mLUHcoFVpCkrBCNp7VlNDzFa5A2UV3X_88yaJCNys8Z_ne1hkiVnpsurc_kb1dp3ZDoovA-ko1hC8VLw=="
INFLUXDB_ORG = "smse4as"
INFLUXDB_BUCKET = "SmartMuseum"


# Initialize InfluxDB client
influx_client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
query_api = influx_client.query_api()

def query_influxdb_topic(topic, time_range="-1h"):
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
    plans = {}

    for topic, state in results_dict.items():

        # Estrarre stanza e metrica dal topic
        match = re.match(r"analysed/room/(room\d+)/(\w+)", topic)
        if not match:
            continue  # Salta i topic non validi
        room, metric = match.groups()

        # Inizializzare il piano della stanza se non esiste
        if room not in plans:
            plans[room] = {}

        # Aggiungere l'azione al piano della stanza
        plans[room][metric] = state

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
        print(result)

    print("\nFinished querying predefined topics.")
    print("Results Dictionary:", results_dict)

    plans = generate_plans(results_dict)
    print("\nGenerated plans:", plans)


if __name__ == "__main__":
    time.sleep(27)  # Wait for InfluxDB to start
    run()