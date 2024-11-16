from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('upload_snapshot/', views.upload_snapshot, name='upload_snapshot'),
    path('get_route/', views.get_route, name='get_route'),
]
