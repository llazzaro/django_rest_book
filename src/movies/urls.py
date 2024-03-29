# urls.py
from django.urls import path

from movies.api import MovieDetailAPIView, MovieListCreateAPIView

app_name = "movies"  # Define the application namespace


urlpatterns = [
    path("/", MovieListCreateAPIView.as_view(), name="movie-api"),
    path("/<int:pk>/", MovieDetailAPIView.as_view(), name="movie-api-detail"),
]
