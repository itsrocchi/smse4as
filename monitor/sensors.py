import time
from air_quality import generate_air_quality
from temperature import generate_temperature
from proximity import generate_proximity
from presence import generate_people_detector
from light import generate_light
from humidity import generate_humidity


AIR_QUALITY_ALARM_MIN = 1001
AIR_QUALITY_ALARM_MAX = 500
TEMPERATURE_ALARM_MIN = 26
TEMPERATURE_ALARM_MAX = 17
PRESENCE_ALARM = 60
LIGHT_ALARM_MIN = 201
LIGHT_ALARM_MAX = 49
HUMIDITY_ALARM_MIN = 61
HUMIDITY_ALARM_MAX = 29

def main():
    while True:
        air_quality = generate_air_quality()
        temperature = generate_temperature()
        proximity = generate_proximity()
        people_count = 0  # Example number of people
        presence = generate_people_detector(people_count)
        if presence < 0:
            presence = 0
        light = generate_light()
        humidity = generate_humidity()

        air_quality_status = "ALARM" if air_quality > AIR_QUALITY_ALARM_MIN or air_quality < AIR_QUALITY_ALARM_MAX else "REGULAR"
        temperature_status = "ALARM" if temperature > TEMPERATURE_ALARM_MIN or temperature < TEMPERATURE_ALARM_MAX else "REGULAR"
        light_status = "ALARM" if light > LIGHT_ALARM_MIN or light < LIGHT_ALARM_MAX else "REGULAR"
        humidity_status = "ALARM" if humidity > HUMIDITY_ALARM_MIN or humidity < HUMIDITY_ALARM_MAX else "REGULAR"
        proximity_status = "ALARM" if proximity == True else "REGULAR"
        presence_status = "ALARM" if presence > PRESENCE_ALARM else "REGULAR"

        print(f"Air Quality: {air_quality} ({air_quality_status})")
        print(f"Temperature: {temperature} ({temperature_status})")
        print(f"Proximity: {proximity} ({proximity_status})")
        print(f"Presence: {presence} ({presence_status})")
        print(f"Light: {light} ({light_status})")
        print(f"Humidity: {humidity} ({humidity_status})")
        print("-----------------------------")

        time.sleep(3)

if __name__ == "__main__":
    main()