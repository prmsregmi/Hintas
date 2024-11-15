from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import base64
import threading
import time
import math
from .models import DroneSettings, ListData
import redis
import json
from .sorting import process_image
import pprint
from django.core.files.base import ContentFile
from .forms import DroneSettingsForm

redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)


def index(request):
    redis_client.flushdb()
    drone_settings = DroneSettings.load()
    if request.method == 'POST':
        form = DroneSettingsForm(request.POST, instance=drone_settings)
        if form.is_valid():
            form.save()
    else:
        form = DroneSettingsForm(instance=drone_settings)
    initial_gps = {
        'lat': DroneSettings.load().starting_lat,
        'lon': DroneSettings.load().starting_lon,
    }
    initial_gps_json = json.dumps(initial_gps)
    context = {
        'initial_gps': initial_gps_json,
        'form': form,
    }
    return render(request, 'index.html', context)

# Direction bearings in degrees
DIRECTION_BEARINGS = {
    'N': 0,
    'NE': 45,
    'E': 90,
    'SE': 135,
    'S': 180,
    'SW': 225,
    'W': 270,
    'NW': 315,
}

def calculate_new_gps(lat1, lon1, distance_km, bearing_degrees):
    R = 6371.0  # Earth's radius in kilometers
    bearing_rad = math.radians(bearing_degrees)
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)

    delta = distance_km / R  # Angular distance in radians

    lat2_rad = math.asin(
        math.sin(lat1_rad) * math.cos(delta) +
        math.cos(lat1_rad) * math.sin(delta) * math.cos(bearing_rad)
    )

    lon2_rad = lon1_rad + math.atan2(
        math.sin(bearing_rad) * math.sin(delta) * math.cos(lat1_rad),
        math.cos(delta) - math.sin(lat1_rad) * math.sin(lat2_rad)
    )

    lat2 = math.degrees(lat2_rad)
    lon2 = math.degrees(lon2_rad)

    return lat2, lon2

CLASS_ORDER = {'Mild': 1, 'Moderate': 2, 'Severe': 3, 'Destructed': 4}


def get_sorted_snapshots():
    # Fetch all snapshots sorted by class order
    snapshots = redis_client.zrange('snapshots', 0, -1)
    # Decode the snapshots
    decoded_snapshots = [json.loads(snapshot) for snapshot in snapshots]
    return decoded_snapshots


@csrf_exempt
def upload_snapshot(request):
    if request.method == 'POST':
        data = request.POST['image']
        elapsed_time = float(request.POST.get('time', 0))

        # Decode image
        image_data = data.split(',')[1]
        image_bytes = base64.b64decode(image_data)

        # Get drone settings
        drone_settings = DroneSettings.load()
        starting_lat = drone_settings.starting_lat
        starting_lon = drone_settings.starting_lon
        speed_kmh = drone_settings.speed_kmh
        direction = drone_settings.direction

        # Calculate distance traveled
        distance_km = speed_kmh * (elapsed_time / 3600)  # Convert time to hours

        # Get bearing in degrees
        bearing_degrees = DIRECTION_BEARINGS.get(direction, 0)

        # Calculate new GPS coordinates
        new_lat, new_lon = calculate_new_gps(
            starting_lat, starting_lon, distance_km, bearing_degrees
        )

        # Pass image and GPS coordinates to your processing pipeline
        _class, _size = process_image(image_data, new_lat, new_lon)
        _time = time.time()
        # Generate a unique key for the snapshot
        # snapshot_id = str(time.time())
        snapshots = {
            # 'image': base64.b64encode(image_bytes).decode('utf-8'),
            'gps': (new_lat, new_lon),
            'class': _class,
            'size': _size,
            'timestamp': _time,
        }
        _id = _time + new_lat + new_lon
         # Generate a unique filename for the image
        image_filename = f'snapshot_{_time}.png'

        # Create a ContentFile from the image bytes
        image_file = ContentFile(image_bytes, name=image_filename)

        list_data = ListData.objects.create(id=_id, lat=new_lat, lon=new_lon, time=_time, class_name=_class, size=_size)
        list_data.image.save(image_filename, image_file)
        list_data.save()

        # class_score = your_function(all parameters you need)
        # Store in Redis sorted set with class order as score
        redis_client.zadd('snapshots', {json.dumps(snapshots): CLASS_ORDER[_class]})

        # Start a timer to delete the snapshot after 10 seconds
        # threading.Timer(10, lambda: snapshots.pop(snapshot_id, None)).start()
        sorted_snapshot = get_sorted_snapshots()


        return JsonResponse({'status': 'success', 'gps': {'lat': new_lat, 'lon': new_lon}, 'class': _class, 'size': _size, 'sorted_snapshot': sorted_snapshot})
    return JsonResponse({'status': 'fail'})