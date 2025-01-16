import random

# Funzione per generare la qualità dell'aria con probabilità
def generate_air_quality():
    if random.random() < 0.8:  # 80% di probabilità per valori normali
        return random.uniform(500, 1000)
    else:  # 20% di probabilità per valori allarmistici
        if random.random() < 0.5:
            return random.uniform(0, 499)
        else: 
            return random.uniform(1001, 2000) 