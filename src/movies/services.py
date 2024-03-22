import csv
import datetime
import json
from collections import defaultdict
from typing import Any, Callable, Dict, Tuple

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404

from movies.models import UserMoviePreferences
from movies.serializers import PreferencesSerializer

from .models import Movie


def user_preferences(user_id: int) -> Any:
    user_preferences = get_object_or_404(UserMoviePreferences, user_id=user_id)
    serializer = PreferencesSerializer(user_preferences.preferences)
    return serializer.data


def user_watch_history(user_id: int) -> dict[Any, Any]:
    user_preferences = get_object_or_404(UserMoviePreferences, user_id=user_id)
    return {"watch_history": user_preferences.watch_history}


def add_preference(user_id: int, new_preferences: Dict[str, Any]) -> None:
    """
    Adds new preferences or updates existing ones in the user's movie preferences,
    using defaultdict to automatically handle lists and avoiding duplicate entries.

    :param user_id: ID of the user
    :param new_preferences: Dict containing new preferences to be added or updated
    """
    with transaction.atomic():
        user = get_object_or_404(get_user_model(), id=user_id)
        (
            user_preferences,
            created,
        ) = UserMoviePreferences.objects.select_for_update().get_or_create(
            user_id=user.id, defaults={"preferences": {}}
        )

        # Use defaultdict to automatically handle list creation
        # Convert existing preferences to defaultdict to ease updating
        current_preferences = defaultdict(list, user_preferences.preferences)

        for key, value in new_preferences.items():
            # Ensure value is not already in the list to avoid duplicates
            if value not in current_preferences[key]:
                current_preferences[key].append(value)

        # Convert defaultdict back to dict to ensure compatibility with Django models
        user_preferences.preferences = dict(current_preferences)
        user_preferences.save()


def add_watch_history(user_id: int, movie_id: int) -> None:
    """
    Adds a new movie to the user's watch history.

    :param user_id: ID of the user
    :param movie_info: Dict containing information about the movie watched
    """
    movie = get_object_or_404(Movie, id=movie_id)
    movie_info = {
        "title": movie.title,
        "year": movie.release_year,
        "director": movie.extra_data.get("directors", []),
        "genre": movie.genres,
    }
    user_preferences, created = UserMoviePreferences.objects.get_or_create(
        user_id=user_id, defaults={"watch_history": [movie_info]}
    )
    if not created:
        # Add new movie info to existing watch history
        current_watch_history = user_preferences.watch_history
        current_watch_history.append(movie_info)
        user_preferences.watch_history = current_watch_history
        user_preferences.save()


def create_or_update_movie(
    title: str,
    genres: list[str],
    country: str | None = None,
    extra_data: dict[Any, Any] | None = None,
    release_year: int | None = None,
) -> Tuple[Movie, bool]:
    """
    Service function to create or update a Movie instance.
    """
    # Ensure the release_year is within an acceptable range
    current_year = datetime.datetime.now().year
    if release_year is not None and (
        release_year < 1888 or release_year > current_year
    ):
        raise ValidationError(
            "The release year must be between 1888 and the current year."
        )

    # Attempt to update an existing movie or create a new one
    movie, created = Movie.objects.update_or_create(
        title=title,
        defaults={
            "genres": genres,
            "country": country,
            "extra_data": extra_data,
            "release_year": release_year,
        },
    )
    return movie, created


def parse_csv(file_path: str) -> int:
    movies_processed = 0
    with open(file_path, encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            create_or_update_movie(**row)
            movies_processed += 1
    return movies_processed


def parse_json(file_path: str) -> int:
    movies_processed = 0
    with open(file_path, encoding="utf-8") as file:
        data = json.load(file)
        for item in data:
            create_or_update_movie(**item)
            movies_processed += 1
    return movies_processed


class FileProcessor:
    def process(self, file_path: str, file_type: str) -> int:
        if file_type == "text/csv":
            movies_processed = self.process_file(file_path, parse_csv)
        elif file_type == "application/json":
            movies_processed = self.process_file(file_path, parse_json)
        else:
            raise ValidationError("Invalid file type")

        return movies_processed

    def process_file(
        self, file_path: str, parser_function: Callable[[str], int]
    ) -> int:
        return parser_function(file_path)
