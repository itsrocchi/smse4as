from calendar import c
import time
import pika 
from influxdb_client import InfluxDBClient, Point, QueryApi
import json
import re
import os

# Define credentials
credentials = pika.PlainCredentials('user', 'password')

# Rabbitmq configuration
connection = pika.BlockingConnection(pika.ConnectionParameters(host='host.docker.internal', port=5672, credentials=credentials))
channel = connection.channel()

INFLUXDB_URL = os.getenv("INFLUXDB_URL")
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN")
INFLUXDB_ORG = os.getenv("INFLUXDB_ORG")
INFLUXDB_BUCKET = os.getenv("INFLUXDB_BUCKET")

# Initialize InfluxDB client
influx_client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
query_api = influx_client.query_api()

def query_influxdb_topic(topic, time_range="-20s"):
    """
    Queries InfluxDB for a specific topic.
    """
    query = f"""
    from(bucket: "{INFLUXDB_BUCKET}") 
    |> range(start: {time_range})
    |> filter(fn: (r) => r._measurement == "mqtt_consumer")
    |> filter(fn: (r) => r.topic == "{topic}")
    |> filter(fn: (r) => r._field == "state")
    |> sort(columns: ["_time"], desc: true)
    |> limit(n: 1)
    """
    try:
        tables = query_api.query(query)
        results = []
        for table in tables:
            for record in table.records:
                results.append(
                    f"Time: {record.get_time()}, State: {record.get_value()}"
                )
        return results if results else f"No data found for topic '{topic}'."
    except Exception as e:
        return f"Error querying InfluxDB for topic '{topic}': {e}"
    

def generate_plans(results_dict):
    plans = {}

    for topic, state in results_dict.items():

        # Estrarre stanza e metrica dal topic
        match = re.match(r"analysed/room/(room\d+)/(\w+)", topic)
        if not match:
            continue  # Salta i topic non validi
        room, metric = match.groups()

        # Inizializzare il piano della stanza se non esiste
        if room not in plans:
            plans[room] = {}

        # Aggiungere l'azione al piano della stanza
        plans[room][metric] = state

    return plans



def run():

    

    # Load room configuration from JSON file
    config_path = '/app/rooms_config.json'
    with open(config_path, 'r') as config_file:
        room_config = json.load(config_file)
        n_rooms = len(room_config)  # Count the number of rooms in the dictionary

    metrics = ["presence", "temperature", "humidity", "light", "air_quality"]
    topics = [f"analysed/room/room{i}/{metric}" for i in range(1, n_rooms + 1) for metric in metrics]

    results_dict = {}

    for topic in topics:
        print(f"\nQuerying InfluxDB for topic '{topic}'...")
        result = query_influxdb_topic(topic)
        if isinstance(result, list):
            for res in result:
                results_dict[f"{topic}"] = res.split(", State: ")[1]
        else:
            results_dict[f"{topic}"] = result
        print(result)

    print("\nFinished querying predefined topics.")
    print("Results Dictionary:", results_dict)

    plans = generate_plans(results_dict)
    print("\nGenerated plans:", plans)

    channel.queue_declare(queue='planner_queue')
    json_message = json.dumps(plans)

    channel.basic_publish(exchange='', routing_key='planner_queue', body=json_message)
    print(" [x] Sent %r" % json_message)

    connection.close()

    # i piani vanno in input ad una funzione executor, che dovrebbe essere presente nel modulo execution (una sottodirectory del planner) che viene importato
    # la funzione che fa? diverse possibilità
    # idea 1:
        # executor pubblica i dati su una coda mqtt (o rabbitmq), la coda viene letta da sensors che utilizza i parametri ricevuti per cambiare l'esecuzione 
        # delle funzioni di generazione dati (vale per tutti i topic tranne per i presence)
        # per il topic presence viene mandato un messaggio ad analysis che cambia dinamicamente per un certo intervallo di tempo la tresholds se è troppo alta
        #(oppure viene manipolato il conteggio di persone e diminuito di un certo valore per "simulare" l'uscita delle persone)
    # idea 2:
        # executor è un modulo a parte ed è lui stesso a simulare l'attivazione degli attuatori (è proprio nella funzione di executor che vengono generati nuovi
        # dati per ogni topic non allarmistici) (come fare praticamente questa cosa è da valutare, sicuramente i piani vengono passati all'executor
        # dal planner tramite code (o influx) e in base ai piani l'executor genera dati). questo script viene tenuto in vita ed è funzionante solo per un periodo di tempo, 
        # poi i dati torna a generarli monitor (comunque questi dati vanno tenuti e mantenuti nella knowledge come se fosse il monitor a generarli).

    # idea 3 (quella da attuare dopo esserci confrontati con il Prof.):
    # mix di idea 1 ed idea 2:
    # il planner manda i piani all'executor (che deve essere un container a parte e non un modulo del planner), l'executor aggiorna una variabile globale
    # la variabile è letta dal monitor che la usa per cambiare i parametri di generazione
    # NB (valutare se usare anche qui le code MQTT); modificare le funzioni di generazione per cambiare i parametri da generare (magari con dei valori in input al metodo);
    # divertirsi!   

    
    # machine learning? si potrebbe pensare che l'analisi usi la knowledge per predire quanti visitatori sono nell
    # valutare comunque se farla, se riusciamo meglio, altrimenti amen.
    


if __name__ == "__main__":
    time.sleep(20)  # Wait for InfluxDB to start
    run()