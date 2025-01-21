from influxdb_client import InfluxDBClient
from influxdb_client.client.query_api import QueryApi
import os

# Configurazione InfluxDB
INFLUXDB_URL = "http://host.docker.internal:8086"
INFLUXDB_TOKEN = "VKuvU-mLUHcoFVpCkrBCNp7VlNDzFa5A2UV3X_88yaJCNys8Z_ne1hkiVnpsurc_kb1dp3ZDoovA-ko1hC8VLw=="
INFLUXDB_ORG = "smse4as"
INFLUXDB_BUCKET = "SmartMuseum"

# Threshold per analisi
THRESHOLDS = {
    "temperature": {"min": 17, "max": 26},
    "humidity": {"min": 30, "max": 60},
    "air_quality": {"min": 400, "max": 1000},
    "light": {"min": 50, "max": 200},
    "presence": {"max": lambda room_size: room_size // 2},
}

# Funzione per calcolare lo stato
def analyze_data(metric, values, thresholds):
    avg_value = sum(values) / len(values)
    if metric == "presence":
        room_size = 100  # Example room size, replace with actual value
        max_threshold = thresholds["max"](room_size)
        if avg_value > max_threshold:
            return "Critical", avg_value
    else:
        if "min" in thresholds and avg_value < thresholds["min"]:
            return "Critical", avg_value
        if "max" in thresholds and avg_value > thresholds["max"]:
            return "Critical", avg_value
    return "Regular", avg_value

# Funzione principale di analisi
def analyze():
    with InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG) as client:
        query_api = client.query_api()

        for metric, thresholds in THRESHOLDS.items():
                metric_topic_map = {
                    "temperature": "room/.*/temperature",
                    "humidity": "room/.*/humidity",
                    "air_quality": "room/.*/air_quality",
                    "light": "room/.*/light",
                    "presence": "room/.*/presence",
                }

                if metric not in metric_topic_map:
                    print(f"Unknown metric: {metric}")
                    continue

                regex_pattern = metric_topic_map[metric]
                query = f"""
                from(bucket: "{INFLUXDB_BUCKET}") 
                |> range(start: -30s)
                |> filter(fn: (r) => r._measurement == "mqtt_consumer")
                |> filter(fn: (r) => r.topic =~ /room\\/.*\\/{metric}/)
                |> filter(fn: (r) => r._field == "int_value" or r._field == "float_value")
                |> keep(columns: ["_value"])
                """

                print(f"Generated Flux query for {metric}:\n{query}")

                try:
                    tables = query_api.query(query)
                except Exception as e:
                    print(f"Error querying for {metric}: {e}")
                    continue

                values = [record.get_value() for table in tables for record in table.records]

                if not values:
                    print(f"No data for metric {metric}")
                    continue

                state, avg_value = analyze_data(metric, values, thresholds)
                print(f"Metric: {metric}, Average: {avg_value}, State: {state}")

"""
if __name__ == "__main__":
    # sleep per dare il tempo al monitor di inserire i dati
    import time
    time.sleep(40)
    analyze()"""
