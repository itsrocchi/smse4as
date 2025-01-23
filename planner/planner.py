import paho.mqtt.client as mqtt

# MQTT configuration
mqtt_broker = "host.docker.internal"
mqtt_port = 1883
mqtt_topic = "analysed/room/room1/presence"
mqtt_client = mqtt.Client()

# Callback per la gestione dei messaggi ricevuti
def on_message(client, userdata, msg):
    print(f"Topic: {msg.topic}, Messaggio: {msg.payload.decode('utf-8')}")

def run():
    # Configura il callback per i messaggi
    mqtt_client.on_message = on_message

    # Connessione al broker MQTT
    mqtt_client.connect(mqtt_broker, mqtt_port)
    print("Connesso al broker MQTT")

    # Iscrizione al topic
    mqtt_client.subscribe(mqtt_topic)
    print(f"Iscritto al topic: {mqtt_topic}")

    # Loop per mantenere la connessione attiva e ascoltare i messaggi
    mqtt_client.loop_forever()

if __name__ == '__main__':
    run()
