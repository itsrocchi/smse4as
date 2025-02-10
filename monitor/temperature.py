import random

# Funzione per generare temperatura con probabilità
def generate_temperature(value):

    if value == -1:
        if random.random() < 0.9:
            return random.uniform(18, 25)
        else: 
            return random.uniform(26, 35)
    elif value == 1:
        if random.random() < 0.9: 
            return random.uniform(18, 25)
        else:  
            return random.uniform(8, 17)    
    else:
        if random.random() < 0.8:  # 80% di probabilità per valori normali
            return random.uniform(18, 25)
        else:  # 20% di probabilità per valori allarmistici
            if random.random() < 0.5:
                return random.uniform(8, 17)
            else: 
                return random.uniform(26, 35) 