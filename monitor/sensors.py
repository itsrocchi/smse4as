import time
import json
import paho.mqtt.client as mqtt

from air_quality import generate_air_quality
from temperature import generate_temperature
from presence import generate_people_detector
from light import generate_light
from humidity import generate_humidity

# MQTT configuration
mqtt_broker = "host.docker.internal"
mqtt_port = 1883
client = mqtt.Client()

# Room configuration
rooms = {
    "room1": {"size": 50, "people_count": 0},
    "room2": {"size": 80, "people_count": 0},
    "room3": {"size": 120, "people_count": 0},
}


# Update sensors in a room 
def update_room_sensors(room_name, room_data):
    client.connect(mqtt_broker, mqtt_port)
    air_quality = generate_air_quality()
    temperature = generate_temperature()
    light = generate_light()
    humidity = generate_humidity()
    people_count = room_data["people_count"]
    presence_change = generate_people_detector(people_count)
    room_data["people_count"] = max(people_count + presence_change, 0)  # Avoid negative numbers
    
    # Publish data to MQTT in JSON format with different field names
    client.publish(f"room/{room_name}/air_quality", json.dumps({"float_value": air_quality}))
    client.publish(f"room/{room_name}/temperature", json.dumps({"float_value": temperature}))
    client.publish(f"room/{room_name}/light", json.dumps({"float_value": light}))
    client.publish(f"room/{room_name}/humidity", json.dumps({"float_value": humidity}))
    client.publish(f"room/{room_name}/presence", json.dumps({"int_value": room_data['people_count']}))    

def main():
    while True:
        for room_name, room_data in rooms.items():
            update_room_sensors(room_name, room_data)
        time.sleep(5)

if __name__ == "__main__":
    main()