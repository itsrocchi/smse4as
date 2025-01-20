import time
import json
import paho.mqtt.client as mqtt

from air_quality import generate_air_quality
from temperature import generate_temperature
from proximity import generate_proximity
from presence import generate_people_detector
from light import generate_light
from humidity import generate_humidity

# MQTT configuration
mqtt_broker = "host.docker.internal"
mqtt_port = 1883
client = mqtt.Client()

# Alarm thresholds configuration
AIR_QUALITY_ALARM_MIN = 1001
AIR_QUALITY_ALARM_MAX = 500
TEMPERATURE_ALARM_MIN = 26
TEMPERATURE_ALARM_MAX = 17
LIGHT_ALARM_MIN = 201
LIGHT_ALARM_MAX = 49
HUMIDITY_ALARM_MIN = 61
HUMIDITY_ALARM_MAX = 29

# Room configuration
rooms = {
    "room1": {"size": 50, "people_count": 0},
    "room2": {"size": 80, "people_count": 0},
    "room3": {"size": 120, "people_count": 0},
}

# Calculate alarm threshold for the rooms based on the size: 1 person for each 2 m²
def calculate_presence_alarm(size):
    return size // 2

# Update sensors in a room 
def update_room_sensors(room_name, room_data):
    client.connect(mqtt_broker, mqtt_port)

    PRESENCE_ALARM = calculate_presence_alarm(room_data["size"])
    air_quality = generate_air_quality()
    temperature = generate_temperature()
    light = generate_light()
    humidity = generate_humidity()
    proximity = generate_proximity()
    people_count = room_data["people_count"]
    presence_change = generate_people_detector(people_count)
    room_data["people_count"] = max(people_count + presence_change, 0)  # Avoid negative numbers

    """air_quality_status = "ALARM" if air_quality > AIR_QUALITY_ALARM_MIN or air_quality < AIR_QUALITY_ALARM_MAX else "REGULAR"
    temperature_status = "ALARM" if temperature > TEMPERATURE_ALARM_MIN or temperature < TEMPERATURE_ALARM_MAX else "REGULAR"
    light_status = "ALARM" if light > LIGHT_ALARM_MIN or light < LIGHT_ALARM_MAX else "REGULAR"
    humidity_status = "ALARM" if humidity > HUMIDITY_ALARM_MIN or humidity < HUMIDITY_ALARM_MAX else "REGULAR"
    proximity_status = "ALARM" if proximity else "REGULAR"
    presence_status = "ALARM" if room_data['people_count'] > PRESENCE_ALARM else "REGULAR"
    """
    
    # Publish data to MQTT in JSON format with different field names
    client.publish(f"room/{room_name}/air_quality", json.dumps({"float_value": air_quality}))
    client.publish(f"room/{room_name}/temperature", json.dumps({"float_value": temperature}))
    client.publish(f"room/{room_name}/light", json.dumps({"float_value": light}))
    client.publish(f"room/{room_name}/humidity", json.dumps({"float_value": humidity}))
    client.publish(f"room/{room_name}/proximity", json.dumps({"int_value": proximity}))
    client.publish(f"room/{room_name}/presence", json.dumps({"int_value": room_data['people_count']}))    

def main():
    while True:
        for room_name, room_data in rooms.items():
            update_room_sensors(room_name, room_data)
        time.sleep(30)

if __name__ == "__main__":
    main()