# urls.py
from django.urls import path

from movies.api import MovieDetailAPIView, MovieListCreateAPIView

app_name = "movies"  # Define the application namespace


urlpatterns = [
    path('movies/', MovieListCreateAPIView.as_view(), name='movie-api'),
    path('movies/<int:pk>/', MovieDetailAPIView.as_view(), name='movie-api-detail'),
]