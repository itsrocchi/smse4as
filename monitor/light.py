import random

# Funzione per generare luce con probabilità
def generate_light():
    if random.random() < 0.8:  # 80% di probabilità per valori normali
        return random.uniform(50, 200)
    else:  # 20% di probabilità per valori allarmistici
        if random.random() < 0.5:
            return random.uniform(0, 49)
        else: 
            return random.uniform(201, 300) 