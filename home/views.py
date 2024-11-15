from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import base64
import threading
import time

# In-memory storage for snapshots
snapshots = {}

def index(request):
    return render(request, 'index.html')

@csrf_exempt
def upload_snapshot(request):
    if request.method == 'POST':
        data = request.POST['image']
        image_data = data.split(',')[1]
        image_bytes = base64.b64decode(image_data)

        # Generate a unique key for the snapshot
        snapshot_id = str(time.time())
        snapshots[snapshot_id] = image_bytes

        # Start a timer to delete the snapshot after 10 seconds
        threading.Timer(10, lambda: snapshots.pop(snapshot_id, None)).start()

        # Here you can pass `image_bytes` to your processing pipeline

        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'fail'})
