from rest_framework import status, views
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Movie
from .serializers import MovieSerializer


class MovieAPIView(views.APIView):
    def post(self, request):
        serializer = MovieSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, pk=None):
        if pk:
            # Retrieve a single movie
            movie = get_object_or_404(Movie, pk=pk)
            serializer = MovieSerializer(movie)
            return Response(serializer.data)
        else:
            # List all movies
            movies = Movie.objects.all()
            serializer = MovieSerializer(movies, many=True)
            return Response(
                {
                    "count": len(serializer.data),
                    "results": serializer.data,
                    "next": None,
                    "previous": None,
                }
            )

    def put(self, request, pk):
        movie = get_object_or_404(Movie, pk=pk)
        serializer = MovieSerializer(movie, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        movie = get_object_or_404(Movie, pk=pk)
        movie.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
