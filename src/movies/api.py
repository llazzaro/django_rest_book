from contextlib import contextmanager
from typing import Any

from django.core.files.storage import default_storage
from rest_framework import generics, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from movies.models import Movie
from movies.services import add_preference, add_watch_history

from .serializers import (
    AddPreferenceSerializer,
    AddToWatchHistorySerializer,
    GeneralFileUploadSerializer,
    MovieSerializer,
)
from .services import FileProcessor, user_preferences, user_watch_history


# For listing all movies and creating a new movie
class MovieListCreateAPIView(generics.ListCreateAPIView):
    queryset = Movie.objects.all().order_by("id")
    serializer_class = MovieSerializer


# For retrieving, updating, and deleting a single movie
class MovieDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer


class UserPreferencesView(APIView):
    """
    View to add new user preferences and retrieve them.
    """

    def post(self, request: Request, user_id: int) -> Response:
        serializer = AddPreferenceSerializer(data=request.data)
        if serializer.is_valid():
            add_preference(user_id, serializer.validated_data["new_preferences"])
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request: Request, user_id: int) -> Response:
        data = user_preferences(user_id)
        return Response(data)


class WatchHistoryView(APIView):
    """
    View to retrieve and add movies to the user's watch history.
    """

    def get(self, request: Request, user_id: int) -> Response:
        data = user_watch_history(user_id)
        return Response(data)

    def post(self, request: Request, user_id: int) -> Response:
        serializer = AddToWatchHistorySerializer(data=request.data)
        if serializer.is_valid():
            add_watch_history(
                user_id,
                serializer.validated_data["id"],
            )
            return Response(
                {"message": "Movie added to watch history."},
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@contextmanager
def temporary_file(uploaded_file):
    try:
        file_name = default_storage.save(uploaded_file.name, uploaded_file)
        file_path = default_storage.path(file_name)
        yield file_path
    finally:
        default_storage.delete(file_name)


class GeneralUploadView(APIView):
    def post(self, request, *args: Any, **kwargs: Any) -> Response:
        serializer = GeneralFileUploadSerializer(data=request.data)
        if serializer.is_valid():
            uploaded_file = serializer.validated_data["file"]
            file_type = uploaded_file.content_type

            with temporary_file(uploaded_file) as file_path:
                processor = FileProcessor()
                movies_processed = processor.process(file_path, file_type)
                return Response(
                    {"message": f"{movies_processed} movies processed successfully."},
                    status=status.HTTP_201_CREATED,
                )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
