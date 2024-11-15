from django.db import models

class Building(models.Model):
    building_size = models.CharField(max_length=100)
    destruction_level = models.CharField(max_length=100)
    gps = models.CharField(max_length=100)

    def __str__(self):
        return f"Building {self.id}"
    
# Direction choices
DIRECTION_CHOICES = [
    ('N', 'North'),
    ('NE', 'North-East'),
    ('E', 'East'),
    ('SE', 'South-East'),
    ('S', 'South'),
    ('SW', 'South-West'),
    ('W', 'West'),
    ('NW', 'North-West'),
]

class DroneSettings(models.Model):
    starting_lat = models.FloatField()
    starting_lon = models.FloatField()
    speed_kmh = models.FloatField()
    direction = models.CharField(max_length=2, choices=DIRECTION_CHOICES)

    def __str__(self):
        return "Drone Settings"

    def save(self, *args, **kwargs):
        self.pk = 1  # Ensure singleton by always setting pk to 1
        super(DroneSettings, self).save(*args, **kwargs)

    @classmethod
    def load(cls):
        return cls.objects.get_or_create(pk=1)[0]

class ListData(models.Model):
    id = models.CharField(max_length=100, primary_key=True)
    image = models.ImageField(upload_to='snapshots/')
    lat = models.FloatField()
    lon = models.FloatField()
    time = models.FloatField()
    class_name = models.CharField(max_length=100)
    size = models.CharField(max_length=100)
    def __str__(self):
        return f"List Data {self.id}"