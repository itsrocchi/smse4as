import random

# Funzione per generare umidità con probabilità
def generate_humidity():
    if random.random() < 0.8:  # 80% di probabilità per valori normali
        return random.uniform(30, 60)
    else:  # 20% di probabilità per valori allarmistici
        if random.random() < 0.5:
            return random.uniform(0, 29)
        else: 
            return random.uniform(61, 100) 