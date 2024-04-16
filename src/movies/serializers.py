from typing import Any

from django.core.files.uploadedfile import InMemoryUploadedFile
from rest_framework import serializers

from .models import Movie


class MovieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movie
        fields = ["id", "title", "genres"]


class PreferencesDetailSerializer(serializers.Serializer):
    genre = serializers.CharField(max_length=100, allow_blank=True, required=False)
    director = serializers.CharField(max_length=100, allow_blank=True, required=False)
    actor = serializers.CharField(max_length=100, allow_blank=True, required=False)
    year = serializers.IntegerField(
        min_value=1900, max_value=2099, required=False, allow_null=False
    )

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        # Check if all fields are empty or not provided
        if all(value in [None, ""] for value in data.values()):
            raise serializers.ValidationError(
                "At least one preference must be provided."
            )
        return data


class AddPreferenceSerializer(serializers.Serializer):
    new_preferences = PreferencesDetailSerializer()


class PreferencesSerializer(serializers.Serializer):
    genre = serializers.ListField(child=serializers.CharField(), required=False)
    director = serializers.ListField(child=serializers.CharField(), required=False)
    actor = serializers.ListField(child=serializers.CharField(), required=False)
    year = serializers.ListField(child=serializers.CharField(), required=False)


class AddToWatchHistorySerializer(serializers.Serializer):
    id = serializers.IntegerField()

    def validate_id(self, value: int) -> int:
        """
        Check if the id corresponds to an existing movie.
        """
        try:
            Movie.objects.get(id=value)
        except Movie.DoesNotExist:
            raise serializers.ValidationError("Invalid movie ID. No such movie exists.")
        return value


class WatchHistorySerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    year = serializers.IntegerField()
    director = serializers.CharField(max_length=255)
    genre = serializers.CharField(max_length=255)


class GeneralFileUploadSerializer(serializers.Serializer):
    file = serializers.FileField()

    def validate_file(self, value: InMemoryUploadedFile) -> InMemoryUploadedFile:
        # Validate file MIME type
        allowed_types = ["text/csv", "application/json", "application/xml"]
        if value.content_type not in allowed_types:
            raise serializers.ValidationError("Unsupported file type.")

        return value
