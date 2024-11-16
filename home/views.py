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
from .utils.emergency import emergency_sort, filter_within_range
import numpy as np
from .utils.rebuild import rebuild_score
from .utils.order import order_rebuild
from enum import Enum


#in memory global variables
starting_point = {
    'lat': -1,
    'lon': -1,
}
maxrange = 10
mappoints = 5


redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)

def get_sorted_snapshots():
    # Fetch all snapshots sorted by class order
    snapshots = redis_client.zrange('snapshots', 0, -1)
    # Decode the snapshots
    decoded_snapshots = [json.loads(snapshot) for snapshot in snapshots]
    return decoded_snapshots

def haversine(coord1, coord2):
    """Calculate the Haversine distance between two GPS coordinates."""
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    R = 6371  # Earth's radius in kilometers
    phi1 = math.radians(float(lat1))
    phi2 = math.radians(float(lat2))
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2.0) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    meters = R * c * 1000  # Convert to meters
    return meters

def select_best_gps_points(data_list, starting_pnt, map_points, w_score=0.7, w_distance=0.3):
    """
    Select the best GPS points based on score and proximity to the starting point.

    Parameters:
    - data_list: List of dictionaries containing GPS data and scores.
    - starting_point: Tuple of (latitude, longitude).
    - map_points: Number of GPS points to select.
    - w_score: Weight for the score in combined score calculation.
    - w_distance: Weight for the distance in combined score calculation.

    Returns:
    - selected_points: List of selected GPS dictionaries.
    """
    # Copy the data_list to avoid modifying the original list
    remaining_points = data_list.copy()
    
    # Extract all scores to compute min and max scores
    all_scores = [item['score'] for item in data_list]
    min_score = min(all_scores)
    max_score = max(all_scores)

    selected_points = []
    current_position = starting_pnt

    for _ in range(map_points):
        if not remaining_points:
            break  # No more points to select

        # Compute distances from current position to all remaining GPS points
        for item in remaining_points:
            item['distance'] = haversine(current_position, item['gps'])

        # Extract distances to compute min and max distances
        distances = [item['distance'] for item in remaining_points]
        min_distance = min(distances)
        max_distance = max(distances)

        # Avoid division by zero in normalization
        score_range = max_score - min_score if max_score != min_score else 1
        distance_range = max_distance - min_distance if max_distance != min_distance else 1

        # Compute combined scores
        for item in remaining_points:
            normalized_score = (item['score'] - min_score) / score_range
            # For distance, closer points should have higher normalized value
            normalized_distance = (max_distance - item['distance']) / distance_range
            item['combined_score'] = w_score * normalized_score + w_distance * normalized_distance

        # Select the GPS point with the highest combined score
        best_item = max(remaining_points, key=lambda x: x['combined_score'])
        selected_points.append(best_item)
        current_position = best_item['gps']
        remaining_points.remove(best_item)

    return selected_points

@csrf_exempt  # Use this decorator if you're not handling CSRF tokens
def get_route(request):
    if request.method == 'POST':
        snapshot = get_sorted_snapshots()
        snapshot = [snap for snap in snapshot if snap['score'] != 0]
        map_list = select_best_gps_points(snapshot, (starting_point['lat'], starting_point['lon']), mappoints)
        map_list = [list(point['gps']) for point in map_list]
        print(map_list)
        return JsonResponse({'map_list': map_list})
    else:
        return JsonResponse({'error': 'Invalid request method.'}, status=400)
    

def index(request):
    global starting_point, maxrange, mappoints
    drone_settings = DroneSettings.load()
    if request.method == 'POST' and 'clear_log' in request.POST:
        redis_client.flushdb()

    if request.method == 'POST' and 'emergency' in request.POST:
        print("Emergency")
        latitude = request.POST.get("latitude")
        longitude = request.POST.get("longitude")
        maxrange = float(request.POST.get("maxrange"))
        mappoints = int(request.POST.get("mappoints"))
        
        # Save the data in memory
        starting_point = {
            'lat': float(latitude),
            'lon': float(longitude),
        }
        
    if request.method == 'POST' and 'rebuild' in request.POST:
        redis_client.flushdb()
        pass

    if request.method == 'POST' and 'drone_simulation' in request.POST:
        print("Drone simulation")
        form = DroneSettingsForm(request.POST, instance=drone_settings)
        if form.is_valid():
            form.save()
    else:
        form = DroneSettingsForm(instance=drone_settings)

    initial_gps = {
        'lat': DroneSettings.load().starting_lat,
        'lon': DroneSettings.load().starting_lon,
    }
    if starting_point == {'lat': -1, 'lon': -1}:
        starting_point = initial_gps
    initial_gps_json = json.dumps(initial_gps)

    context = {
        'gps': initial_gps,
        'starting_point': starting_point,
        'maxrange': maxrange,
        'mappoints': mappoints,
        'initial_gps': initial_gps_json,
        'form': form,
        'sorted_snapshot': json.dumps(get_sorted_snapshots()),
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

def damage_class_score(damage_class):
    if damage_class == 2:
        return 0.8
    elif damage_class == 3:
        return 0.5
    elif damage_class == 4:
        return 0.4
    elif damage_class == 1:
        return 0.3
    else:
        return 0.0

def class_score(_class, _size, lat, lon, starting_point, max_distance_miles):
    W1 = 0.7
    W2 = 0.3
    starting_point = [starting_point['lat'], starting_point['lon']]
    if not filter_within_range(lat, lon, starting_point, max_distance_miles):
        return 0
    score = (W1 * damage_class_score(_class) + W2*_size)
    return score

class Size(Enum):
    SMALL = 1
    MEDIUM = 2
    LARGE = 3

class Damage(Enum):
    NONE = 0
    MILD = 1
    MODERATE = 2
    SEVERE = 3
    CATASTROPHIC = 4

@csrf_exempt
def upload_snapshot(request):
    global starting_point, maxrange
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
        _class, _size = process_image(base64.b64encode(image_bytes).decode('utf-8'))
        _time = time.time()
        

        score = class_score(_class, _size, new_lat, new_lon, starting_point, maxrange)
        snapshots = {
            # 'image': base64.b64encode(image_bytes).decode('utf-8'),
            'gps': (round(new_lat, 6), round(new_lon, 6)),
            'class': Damage(_class).name,
            'size': Size(_size).name,
            'timestamp': round(_time, 4),
            'score': round(score, 4)
        }
        _id = _time + new_lat + new_lon
         # Generate a unique filename for the image
        image_filename = f'snapshot_{_time}.png'

        # Create a ContentFile from the image bytes
        image_file = ContentFile(image_bytes, name=image_filename)

        list_data = ListData.objects.create(id=_id, lat=new_lat, lon=new_lon, time=_time, class_name=_class, size=_size)
        list_data.image.save(image_filename, image_file)
        list_data.save()

        
        # Store in Redis sorted set with the calculated score
        redis_client.zadd('snapshots', {json.dumps(snapshots): -score})
    
        # Start a timer to delete the snapshot after 10 seconds
        # threading.Timer(10, lambda: snapshots.pop(snapshot_id, None)).start()
        sorted_snapshot = get_sorted_snapshots()


        return JsonResponse({'status': 'success', 'gps': {'lat': new_lat, 'lon': new_lon}, 'class': Damage(_class).name, 'size': Size(_size).name, 'sorted_snapshot': sorted_snapshot})
    return JsonResponse({'status': 'fail'})