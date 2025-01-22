import random

def generate_people_detector(num_people):
    if random.random() < 0.8:
        return (num_people + random.randint(0, 5))
    else:
        return (num_people - random.randint(0, 5))