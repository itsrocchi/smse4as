import os
import time
import json
import paho.mqtt.client as mqtt
from air_quality import generate_air_quality
from temperature import generate_temperature
from presence import generate_people_detector
from light import generate_light
from humidity import generate_humidity
import threading


# MQTT configuration
mqtt_broker = "host.docker.internal"
mqtt_port = 1883
client = mqtt.Client()

file_path = "/shared/state.json"

rooms_config_path = "/app/rooms_config.json"
with open(rooms_config_path, "r") as file:
    rooms = json.load(file)

# Initialize room data with people_count
for room in rooms:
    rooms[room]["people_count"] = 0

# Arrays to store sensor data
sensor_data = {
    "presence": [],
    "temperature": [],
    "humidity": [],
    "light": [],
    "air_quality": []
}

method_values = []


# Function to update sensors in a room and publish data to MQTT
def update_room_sensors(room_name, room_data):

    if os.path.exists(file_path):  # Controlla se il file esiste
            with open(file_path, "r") as f:
                try:
                    state = json.load(f)  # Legge lo stato dal file
                    # legge i dati della stanza room_name
                    room_state = state[room_name]
                    #print(room_name, room_state)
                except json.JSONDecodeError:
                    print("Monitor: Errore nella decodifica del file JSON")
    

    client.connect(mqtt_broker, mqtt_port)
    air_quality = generate_air_quality(room_state["air_quality"])
    temperature = generate_temperature(room_state["temperature"])
    light = generate_light(room_state["light"])
    humidity = generate_humidity(room_state["humidity"])
    presence_change = generate_people_detector(room_data["people_count"], room_state["presence"])
    room_data["people_count"] = max(presence_change, 0)  # Avoid negative numbers
    
    # Publish data to MQTT in JSON format with different field names
    client.publish(f"room/{room_name}/presence", json.dumps({"int_value": room_data['people_count']}))
    client.publish(f"room/{room_name}/temperature", json.dumps({"float_value": temperature}))
    client.publish(f"room/{room_name}/humidity", json.dumps({"float_value": humidity}))
    client.publish(f"room/{room_name}/light", json.dumps({"float_value": light}))
    client.publish(f"room/{room_name}/air_quality", json.dumps({"float_value": air_quality}))   


def main():
    #scrive sul file in file path un json con i dati delle stanze impostati a 0, il numero di stanze lo valuti in base a rooms_config.json
    state = {}
    for room_name in rooms:
        state[room_name] = {
            "presence": 0,
            "temperature": 0,
            "humidity": 0,
            "light": 0,
            "air_quality": 0
        }
    with open(file_path, "w") as f:
        json.dump(state, f, indent=4)
    print("Monitor: Stato iniziale scritto")

    #ciclo infinito che ogni 5 secondi legge lo stato dal file e aggiorna i sensori delle stanze
    while True:
        for room_name, room_data in rooms.items():
            update_room_sensors(room_name, room_data)
        time.sleep(5)

if __name__ == "__main__":
    main()
