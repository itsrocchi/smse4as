from influxdb_client import InfluxDBClient
import time
import paho.mqtt.client as mqtt
import re

# InfluxDB configuration
INFLUXDB_URL = "http://host.docker.internal:8086"
INFLUXDB_TOKEN = "VKuvU-mLUHcoFVpCkrBCNp7VlNDzFa5A2UV3X_88yaJCNys8Z_ne1hkiVnpsurc_kb1dp3ZDoovA-ko1hC8VLw=="
INFLUXDB_ORG = "smse4as"
INFLUXDB_BUCKET = "SmartMuseum"

# MQTT configuration
mqtt_broker = "host.docker.internal"
mqtt_port = 1883
client_mqtt = mqtt.Client()

# Thresholds
THRESHOLDS = {
    "temperature": {"min": 17, "max": 26},
    "humidity": {"min": 30, "max": 60},
    "air_quality": {"min": 400, "max": 1000},
    "light": {"min": 50, "max": 200},
    "presence": {"max": lambda room_size: room_size // 2},
}

# Analyze data function
def analyze_data(metric, values, thresholds):
    avg_value = sum(values) / len(values)
    if metric == "presence":
        room_size = 100  # Example room size
        max_threshold = thresholds["max"](room_size)
        if avg_value > max_threshold:
            return "Critical", avg_value
    else:
        if "min" in thresholds and avg_value < thresholds["min"]:
            return "Critical", avg_value
        if "max" in thresholds and avg_value > thresholds["max"]:
            return "Critical", avg_value
    return "Regular", avg_value

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

            print(f"Generated Flux query for {metric}:\n{query}")

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

                state, avg_value = analyze_data(metric, values, thresholds)
                result_topic = f"analysed/room/{room}/{metric}"
                client_mqtt.publish(result_topic, f"{avg_value}: {state}")
                print(f"Published to {result_topic}: {avg_value}: {state}")

    client_mqtt.disconnect()


if __name__ == "__main__":
    time.sleep(20)
    analyze()
