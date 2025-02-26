from influxdb_client import InfluxDBClient
import time
import paho.mqtt.client as mqtt
import re
import json
import os



# InfluxDB configuration
INFLUXDB_URL = os.getenv("INFLUXDB_URL")
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN")
INFLUXDB_ORG = os.getenv("INFLUXDB_ORG")
INFLUXDB_BUCKET = os.getenv("INFLUXDB_BUCKET")

# MQTT configuration
mqtt_broker = "host.docker.internal"
mqtt_port = 1883
client_mqtt = mqtt.Client()

rooms_config_path = "/app/rooms_config.json"
with open(rooms_config_path, "r") as file:
    rooms = json.load(file)

# Estrarre solo le dimensioni delle stanze
room_sizes = {room: data["size"] for room, data in rooms.items()}

# Leggere la variabile d'ambiente
thresholds_json = os.getenv("THRESHOLDS")
THRESHOLDS = json.loads(thresholds_json) if thresholds_json else {}

# Sostituire il segnaposto con la funzione lambda
if "presence" in THRESHOLDS and "max" in THRESHOLDS["presence"]:
    if THRESHOLDS["presence"]["max"] == "ROOM_SIZE_HALF":
        THRESHOLDS["presence"]["max"] = lambda room: room_sizes[room] // 2

# Analyze data function
def analyze_data(metric, values, thresholds, room):
    avg_value = sum(values) / len(values)
    state = 0  # Default: Regular

    if metric == "presence":
        max_threshold = thresholds["max"](room)
        if avg_value > max_threshold:
            state = 1  # Critical
    else:
        if "min" in thresholds and avg_value < thresholds["min"]:
            state = -1  # Critical: Below min threshold
        if "max" in thresholds and avg_value > thresholds["max"]:
            state = 1  # Critical: Above max threshold
    return state, avg_value

# Main analyze function
def analyze():
    client_mqtt.connect(mqtt_broker, mqtt_port)

    with InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG) as client:
        query_api = client.query_api()

        for metric, thresholds in THRESHOLDS.items():
            query = f"""
            from(bucket: "{INFLUXDB_BUCKET}") 
            |> range(start: -20s)
            |> filter(fn: (r) => r._measurement == "mqtt_consumer")
            |> filter(fn: (r) => r.topic =~ /room\\/.*\\/{metric}/)
            |> filter(fn: (r) => r._field == "int_value" or r._field == "float_value")
            |> keep(columns: ["_value", "topic"])
            """

            #print(f"Generated Flux query for {metric}:\n{query}")

            try:
                tables = query_api.query(query)
            except Exception as e:
                print(f"Error querying for {metric}: {e}")
                continue

            room_data = {}
            for table in tables:
                for record in table.records:
                    topic = record.values.get("topic", "")
                    value = record.get_value()
                    match = re.search(r"room/([^/]+)/", topic)
                    if match:
                        room = match.group(1)
                        if room not in room_data:
                            room_data[room] = []
                        room_data[room].append(value)

            for room, values in room_data.items():
                if not values:
                    print(f"No data for metric {metric} in room {room}")
                    continue

                state, avg_value = analyze_data(metric, values, thresholds, room)            
                result_topic = f"analysed/room/{room}/{metric}"

                # Prepare payload with both float_value and state
                payload = {
                    "average": avg_value,
                    "state": state  # 0 = Regular, 1 = Above max, -1 = Below min
                }

                client_mqtt.publish(result_topic, json.dumps(payload))
                print(f"Published {metric} analysis for room {room}: {json.dumps(payload)}")

    time.sleep(1) # Wait for messages to be sent
    client_mqtt.disconnect()


if __name__ == "__main__":
    time.sleep(20)
    analyze()
