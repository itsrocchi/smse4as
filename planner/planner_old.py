import paho.mqtt.client as mqtt
import re
import time

# MQTT configuration
mqtt_broker = "host.docker.internal"
mqtt_port = 1883
#mqtt_client = mqtt.Client()
mqtt_topic = "analysed/room/#"

def connect_mqtt() -> mqtt.Client:
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)

    client = mqtt.Client()
    # client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.connect(mqtt_broker, mqtt_port)
    return client

def perform_action(room, metric, state, value):
    if state == "Critical":
        # Esegui azione per stato critico
        print(f"CRITICAL: {metric} in {room} is {value}. Taking action!")
        # Qui puoi aggiungere azioni specifiche come inviare un'email, attivare un allarme, ecc.
    else:
        # Esegui azione per stato regolare
        print(f"REGULAR: {metric} in {room} is {value}. No action needed.")


def subscribe(client: mqtt.Client):

    def on_message(client, userdata, msg):
        print(f"Received message on topic {msg.topic}: {msg.payload.decode('utf-8')}")
        
        topic = msg.topic
        payload = msg.payload.decode('utf-8')
        
        # Extract room, metric, and state
        match = re.search(r"analysed/room/([^/]+)/([^/]+)", topic)
        if match:
            room = match.group(1)
            metric = match.group(2)
            
            # Example payload: "23.273663630907574: Regular"
            value, state = payload.split(": ")
            
            # Perform action based on the state
            perform_action(room, metric, state, value)

    client.subscribe(mqtt_topic)
    client.on_message = on_message

def run():
    client = connect_mqtt()
    subscribe(client)
    client.loop_forever()


if __name__ == '__main__':
    run()

