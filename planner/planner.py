import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient, Point, QueryApi

# MQTT configuration
mqtt_broker = "host.docker.internal"  # Replace with the actual broker address
mqtt_port = 1883
mqtt_topic = "analysed/room/+/+"  # Wildcard subscription
mqtt_client = mqtt.Client()

# InfluxDB configuration
INFLUXDB_URL = "http://host.docker.internal:8086"
INFLUXDB_TOKEN = "VKuvU-mLUHcoFVpCkrBCNp7VlNDzFa5A2UV3X_88yaJCNys8Z_ne1hkiVnpsurc_kb1dp3ZDoovA-ko1hC8VLw=="
INFLUXDB_ORG = "smse4as"
INFLUXDB_BUCKET = "SmartMuseum"

# Initialize InfluxDB client
influx_client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
query_api = influx_client.query_api()


def query_influxdb_metrics(metrics, time_range="-20s"):
    """
    Queries InfluxDB for the given metrics and time range.
    """
    for metric in metrics:
        query = f"""
        from(bucket: "{INFLUXDB_BUCKET}") 
        |> range(start: {time_range})
        |> filter(fn: (r) => r._measurement == "mqtt_consumer")
        |> filter(fn: (r) => r.topic =~ /room\\/.*\\/{metric}/)
        |> filter(fn: (r) => r._field == "int_value" or r._field == "float_value")
        |> keep(columns: ["_time", "_value", "topic"])
        |> sort(columns: ["_time"], desc: true)
        |> limit(n: 1)
        """
        print(f"Generated Flux query for {metric}:\n{query}")

        try:
            tables = query_api.query(query)
            results = []
            for table in tables:
                for record in table.records:
                    results.append(
                        f"Time: {record.get_time()}, Topic: {record['topic']}, Value: {record['_value']}"
                    )
            if results:
                print(f"Results for {metric}:\n" + "\n".join(results))
            else:
                print(f"No data found for {metric} in the specified time range.")
        except Exception as e:
            print(f"Error querying InfluxDB for {metric}: {e}")


def query_influxdb_topic(topic, time_range="-1h"):
    """
    Queries InfluxDB for a specific topic.
    """
    query = f"""
    from(bucket: "{INFLUXDB_BUCKET}") 
    |> range(start: {time_range})
    |> filter(fn: (r) => r["_measurement"] == "{topic}")
    |> sort(columns: ["_time"], desc: true)
    |> limit(n: 1)
    """
    try:
        tables = query_api.query(query)
        results = []
        for table in tables:
            for record in table.records:
                results.append(
                    f"Time: {record.get_time()}, Value: {record.get_value()}"
                )
        return "\n".join(results) if results else f"No data found for topic '{topic}'."
    except Exception as e:
        return f"Error querying InfluxDB for topic '{topic}': {e}"


def on_connect(client, userdata, flags, rc):
    """
    Callback function when MQTT connects to the broker.
    """
    if rc == 0:
        print("Connected to MQTT broker!")
        client.subscribe(mqtt_topic)
    else:
        print(f"Failed to connect to MQTT broker, return code: {rc}")


def run():
    """
    Main function to query predefined topics from InfluxDB.
    """
    # Setup MQTT client
    mqtt_client.on_connect = on_connect
    mqtt_client.connect(mqtt_broker, mqtt_port)
    mqtt_client.loop_start()

    # Predefined topics
    topics = ["analysed/room/room1/presence", "analysed/room/room1/temperature"]

    for topic in topics:
        print(f"\nQuerying InfluxDB for topic '{topic}'...")
        result = query_influxdb_topic(topic)
        print(result)

    print("\nFinished querying predefined topics.")

if __name__ == "__main__":
    run()
