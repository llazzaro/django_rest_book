# urls.py
from django.urls import path

from movies.api import MovieAPIView

app_name = "movies"  # Define the application namespace


urlpatterns = [
    path("movies/", MovieAPIView.as_view(), name="movie-api"),
    path("movies/<int:pk>/", MovieAPIView.as_view(), name="movie-api-detail"),
]
