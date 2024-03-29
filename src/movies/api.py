from rest_framework import generics

from .models import Movie
from .serializers import MovieSerializer


# For listing all movies and creating a new movie
class MovieListCreateAPIView(generics.ListCreateAPIView):
    queryset = Movie.objects.all().order_by("id")
    serializer_class = MovieSerializer


# For retrieving, updating, and deleting a single movie
class MovieDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer
