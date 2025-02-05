import os
import pika
import json
import time
import paho.mqtt.client as mqtt


file_path = "/shared/state.json"

# Define credentials
credentials = pika.PlainCredentials('user', 'password')

def execute_plan(plan):
    
    state = {}
    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            try:
                state = json.load(file)
            except json.JSONDecodeError:
                state = {}

    for room, values in plan.items():
        state[room] = {
            "presence": int(float(values['presence'])),
            "temperature": int(float(values['temperature'])),
            "humidity": int(float(values['humidity'])),
            "light": int(float(values['light'])),
            "air_quality": int(float(values['air_quality']))
        }

    with open(file_path, "w") as file:
        json.dump(state, file, indent=4)

    print("Stato delle stanze aggiornato")


# Callback quando si riceve un messaggio Rabbitmq
def callback(ch, method, properties, body):
    try:
        payload = json.loads(body)
        execute_plan(payload)
        print("ricevuti: ", payload)
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except json.JSONDecodeError as e:
        print("Errore nella decodifica JSON:", e)

def run():
    # Rabbitmq configuration
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='host.docker.internal', port=5672, credentials=credentials))
    channel = connection.channel()
    channel.queue_declare(queue='planner_queue')
    channel.basic_consume(queue='planner_queue', on_message_callback=callback, auto_ack=True)
    print('In attesa di messaggi...')
    channel.start_consuming()

if __name__ == "__main__":
    run()