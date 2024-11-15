import random

def process_image(image_bytes, new_lat, new_lon):
    _class = random.choice(["Mild", "Moderate", "Severe", "Destructed"])
    _size = random.choice(["Small", "Medium", "Large"])
    return _class, _size