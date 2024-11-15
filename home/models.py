from django.db import models

class Building(models.Model):
    building_size = models.CharField(max_length=100)
    destruction_level = models.CharField(max_length=100)
    gps = models.CharField(max_length=100)

    def __str__(self):
        return f"Building {self.id}"
