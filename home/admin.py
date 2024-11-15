from django.contrib import admin
from .models import Building, DroneSettings, ListData

# Register your models here.
admin.site.register(Building)
admin.site.register(DroneSettings)
admin.site.register(ListData)