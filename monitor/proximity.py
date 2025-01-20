import random

def generate_proximity():
    if random.random() < 0.95:
        return 0 # false, people not near the quadro
    else:
        return 1