import random

def generate_people_detector(num_people, value):

    if value == 1:
        return (num_people - random.randint(0, 5))
    else:
        if random.random() < 0.5:
            return (num_people + random.randint(0, 5))
        else:
            return (num_people - random.randint(0, 5))