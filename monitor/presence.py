import random

def generate_people_detector(num_people, value):

    if value == 2:
        return (num_people - random.randint(0, 10))
    else:
        if random.random() < 0.5:
            return (num_people + random.randint(0, 5))
        else:
            return (num_people - random.randint(0, 5))