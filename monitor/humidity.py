import random

# Funzione per generare umidità con probabilità
def generate_humidity(value):

    if (value == -2 | value == 2):
        return random.uniform(30, 60)
    elif value == -1:
        if random.random() < 0.9:
            return random.uniform(30, 60)
        else: 
            return random.uniform(0, 29)
    elif value == 1:
        if random.random() < 0.9: 
            return random.uniform(30, 60)
        else:  
            return random.uniform(61, 100)
    else:
        if random.random() < 0.8:  # 80% di probabilità per valori normali
            return random.uniform(30, 60)
        else:  # 20% di probabilità per valori allarmistici
            if random.random() < 0.5:
                return random.uniform(0, 29)
            else: 
                return random.uniform(61, 100) 