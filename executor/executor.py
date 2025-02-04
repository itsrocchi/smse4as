import pika
import json
import time

# Rabbitmq configuration
connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq', 5672))
channel = connection.channel()
channel.queue_declare(queue='planner_queue')

def execute_plan(plan):
    """
    Esegue il piano ricevuto, simulando l'attivazione degli attuatori.
    """
    for room, actions in plan.items():
        print(f"Eseguendo piano per {room}:")
        for action, value in actions.items():
            action_str = "Nessuna azione" if value == 0 else ("Abbassa" if value == -1 else "Alza")
            print(f"  - {action}: {action_str} ({value})")
        print("-")

# Callback quando si riceve un messaggio MQTT
def callback(ch, method, properties, body):
    try:
        payload = json.loads(body)
        print("\nRicevuto piano dal planner:", payload)
        #execute_plan(payload)
    except json.JSONDecodeError as e:
        print("Errore nella decodifica JSON:", e)


channel.basic_consume(queue='planner_queue', on_message_callback=callback, auto_ack=True)
print('In attesa di messaggi...')
channel.start_consuming()
