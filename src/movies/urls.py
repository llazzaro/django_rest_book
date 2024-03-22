# urls.py
from django.urls import path

from movies.api import (
    GeneralUploadView,
    MovieDetailAPIView,
    MovieListCreateAPIView,
    UserPreferencesView,
    WatchHistoryView,
)

app_name = "movies"  # Define the application namespace


urlpatterns = [
    path("", MovieListCreateAPIView.as_view(), name="movie-api"),
    path("<int:pk>/", MovieDetailAPIView.as_view(), name="movie-api-detail"),
    path(
        "user/<int:user_id>/preferences/",
        UserPreferencesView.as_view(),
        name="user-preferences",
    ),
    path(
        "user/<int:user_id>/watch-history/",
        WatchHistoryView.as_view(),
        name="user-watch-history",
    ),
    path("upload/", GeneralUploadView.as_view(), name="file-upload"),
]
