import os
import uuid
from typing import Any, Optional

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from rest_framework import generics, status
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from api_auth.permissions import CustomDjangoModelPermissions
from movies.models import Movie, UserMoviePreferences
from movies.services import add_preference, add_watch_history
from movies.tasks import process_file
from recommendations.services import Item, UserPreferences, get_recommendations

from .serializers import (
    AddPreferenceSerializer,
    AddToWatchHistorySerializer,
    GeneralFileUploadSerializer,
    MovieSerializer,
)
from .services import user_preferences, user_watch_history


# For listing all movies and creating a new movie
class MovieListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated, CustomDjangoModelPermissions)
    queryset = Movie.objects.all().order_by("id")
    serializer_class = MovieSerializer


# For retrieving, updating, and deleting a single movie
class MovieDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer


class UserPreferencesView(APIView):
    """
    View to add new user preferences and retrieve them.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request: Request, user_id: int) -> Response:
        serializer = AddPreferenceSerializer(data=request.data)
        if serializer.is_valid():
            add_preference(user_id, serializer.validated_data["new_preferences"])
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request: Request, user_id: int) -> Response:
        data = user_preferences(user_id)
        return Response(data)


# View to retrieve and add movies to the user's watch history
@permission_classes([IsAuthenticated])
class WatchHistoryView(APIView):
    """
    View to retrieve and add movies to the user's watch history.
    """

    permission_classes = [IsAuthenticated]

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


class GeneralUploadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args: Any, **kwargs: Any) -> Response:
        serializer = GeneralFileUploadSerializer(data=request.data)
        if serializer.is_valid():
            uploaded_file = serializer.validated_data["file"]
            file_type = uploaded_file.content_type

            # Extract the file extension
            file_extension = os.path.splitext(uploaded_file.name)[1]
            # Generate a unique file name using UUID
            unique_file_name = f"{uuid.uuid4()}{file_extension}"

            # Save the file directly to the default storage
            file_name = default_storage.save(
                unique_file_name, ContentFile(uploaded_file.read())
            )

            process_file.delay(file_name, file_type)

            return Response(
                {"message": f"Job enqueued for processing."},
                status=status.HTTP_202_ACCEPTED,
            )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MovieRecommendationAPIView(APIView):
    def get(self, request):
        user_id = request.query_params.get("user_id")

        if not user_id:
            return self._response_error(
                detail="user_id query parameter is required.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        user_preferences = self._get_user_preferences(user_id)
        if not user_preferences:
            return self._response_error(
                detail="User preferences not found.",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        recommended_items = self._get_recommended_items(user_preferences)
        response_data = self._format_response(recommended_items)

        return Response(response_data, status=status.HTTP_200_OK)

    def _get_user_preferences(self, user_id: str) -> Optional[UserPreferences]:
        """
        Retrieves user preferences from the database and converts them into the UserPreferences Pydantic model.

        :param user_id: The ID of the user whose preferences are to be fetched.
        :return: A UserPreferences object populated with the user's preferences, or None if no preferences exist.
        """
        try:
            # Fetch user preferences from the database
            user_prefs = UserMoviePreferences.objects.get(user_id=user_id)

            # Extracting the relevant preferences
            genre = user_prefs.preferences.get("genre", [])
            director = user_prefs.preferences.get("director", [])
            actor = user_prefs.preferences.get("actor", [])
            year_range = user_prefs.preferences.get("year", [])

            # Handle year range if it's provided (expecting a list)
            year_range_start, year_range_end = (
                (year_range[0], year_range[-1])
                if len(year_range) >= 2
                else (None, None)
            )

            # Build the preferences dictionary
            preferences_dict = {
                "genre": genre,
                "director": director,
                "actor": actor,
                "year_range_start": year_range_start,
                "year_range_end": year_range_end,
            }

            # Instantiate UserPreferences with the preferences dictionary
            return UserPreferences(
                preferences=preferences_dict,
                watch_history=user_prefs.watch_history,  # Assuming this exists in user_prefs
            )
        except UserMoviePreferences.DoesNotExist:
            return None  # Return None if no preferences are found for the user

    def _get_recommended_items(self, user_preferences: UserPreferences) -> list[Item]:
        """
        Generates a list of recommended items (in this case, movies) based on user preferences.

        :param user_preferences: The preferences of the user.
        :return: A list of recommended items as Item objects.
        """
        movies = Movie.objects.all()

        items = [
            Item(
                id=movie.id,
                attributes={
                    "name": movie.title,
                    "genre": movie.genres,
                    "director": movie.extra_data.get("directors", ""),
                    "year": movie.release_year,
                },
            )
            for movie in movies
        ]

        return get_recommendations(user_preferences=user_preferences, items=items)

    def _format_response(self, recommended_items: list[Item]) -> list[dict]:
        """
        Formats the recommended items into a response-friendly structure.

        :param recommended_items: A list of Item objects representing recommended content.
        :return: A list of dictionaries with content ID and name.
        """
        return [
            {"id": item.id, "title": item.attributes.get("name", "Unknown")}
            for item in recommended_items
        ]

    def _response_error(self, detail: str, status_code: int) -> Response:
        """
        Constructs an error response.

        :param detail: The error message to include in the response.
        :param status_code: The HTTP status code for the response.
        :return: A Response object with the error message and status code.
        """
        return Response({"detail": detail}, status=status_code)
