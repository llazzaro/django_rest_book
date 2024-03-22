import json

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from movies.models import Movie

from .factories import MovieFactory, UserFactory


@pytest.mark.django_db
def test_create_movie(client: APIClient) -> None:
    url = reverse("movies:movie-api")
    data = {"title": "A New Hope", "genres": json.dumps(["Sci-Fi", "Adventure"])}

    response = client.post(url, data=data)

    assert response.status_code == status.HTTP_201_CREATED, response.json()
    assert Movie.objects.filter(title="A New Hope").exists()
    assert Movie.objects.filter(title="A New Hope").count() == 1


@pytest.mark.django_db
def test_retrieve_movie(client: APIClient) -> None:
    movie = MovieFactory()
    url = reverse("movies:movie-api-detail", kwargs={"pk": movie.id})

    response = client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "id": movie.id,
        "title": movie.title,
        "genres": movie.genres,
    }


@pytest.mark.django_db
def test_update_movie(client: APIClient) -> None:
    movie = MovieFactory()
    new_title = "Updated Movie Title"
    url = reverse("movies:movie-api-detail", kwargs={"pk": movie.id})
    data = {"title": new_title}

    response = client.put(url, data=data, content_type="application/json")

    assert response.status_code == status.HTTP_200_OK, response.json()
    movie = Movie.objects.filter(id=movie.id).first()
    assert movie
    assert movie.title == new_title


@pytest.mark.django_db
def test_delete_movie(client: APIClient) -> None:
    movie = MovieFactory()
    url = reverse("movies:movie-api-detail", kwargs={"pk": movie.id})

    response = client.delete(url)

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not Movie.objects.filter(id=movie.id).exists()


@pytest.mark.django_db
def test_list_movies_with_pagination(client: APIClient) -> None:
    # Create a batch of movies, adjust the number according to your PAGE_SIZE setting
    movies = MovieFactory.create_batch(10)  # Assuming PAGE_SIZE is set to 10

    # Define the URL for the list movies endpoint
    url = reverse("movies:movie-api")

    # Perform a GET request to the list endpoint
    response = client.get(url)

    # Assert that the response status code is 200 OK
    assert response.status_code == status.HTTP_200_OK

    # Convert the response data to JSON
    data = response.json()

    # Assert the structure of the paginated response
    assert "count" in data
    assert "next" in data
    assert "previous" in data
    assert "results" in data

    # Assert that the count matches the total number of movies created
    assert data["count"] == 10  # Adjust according to the number of movies created

    # Assert the pagination metadata (if applicable, depending on the number of items and page size)
    # For example, if you expect more items and multiple pages:
    # assert data["next"] is not None
    # But in this case, if all movies fit on one page:
    assert data["next"] is None
    assert data["previous"] is None

    # Assert that the number of movies in the results matches the number of movies created
    # This checks the first page of results in case of multiple pages
    assert len(data["results"]) == 10  # Adjust based on your PAGE_SIZE setting

    # Use a set to ensure that the returned movies match the expected movies
    returned_movie_ids = {movie["id"] for movie in data["results"]}
    expected_movie_ids = {movie.id for movie in movies}
    assert returned_movie_ids == expected_movie_ids

    # Additionally, verify that each movie in the response contains the expected keys
    for movie_data in data["results"]:
        assert set(movie_data.keys()) == {"id", "title", "genres"}


@pytest.mark.django_db
@pytest.mark.parametrize(
    "new_preferences, expected_genre",
    [
        ({"genre": "sci-fi"}, "sci-fi"),
        ({"genre": "drama"}, "drama"),
        ({"genre": "action"}, "action"),
        (
            {"genre": "sci-fi", "actor": "Sigourney Weaver", "year": "1979"},
            "sci-fi",
        ),
        # Adding more scenarios if needed where a 200 response is expected
    ],
)
def test_add_and_retrieve_preferences_success(
    new_preferences: dict[str, str], expected_genre: str
) -> None:
    user = UserFactory()
    client = APIClient()
    preferences_url = reverse("movies:user-preferences", kwargs={"user_id": user.id})

    # Add new preferences
    response = client.post(
        preferences_url, {"new_preferences": new_preferences}, format="json"
    )
    assert response.status_code in [200, 201]

    # Retrieve preferences to verify
    response = client.get(preferences_url)
    assert response.status_code == 200
    assert response.data["genre"] == [expected_genre]


@pytest.mark.django_db
@pytest.mark.parametrize(
    "new_preferences",
    [
        ({}),  # Empty preferences
        ({"genreee": "comedy"}),  # Invalid field
        # Include additional cases as needed where a 400 response is expected
    ],
)
def test_add_preferences_failure(new_preferences: dict[str, str]) -> None:
    user = UserFactory()
    client = APIClient()
    preferences_url = reverse("movies:user-preferences", kwargs={"user_id": user.id})

    # Attempt to add new preferences
    response = client.post(
        preferences_url, {"new_preferences": new_preferences}, format="json"
    )
    assert response.status_code == 400, response.json()


@pytest.mark.django_db
def test_add_and_retrieve_watch_history_with_movie_id() -> None:
    user = UserFactory()
    client = APIClient()
    watch_history_url = reverse(
        "movies:user-watch-history", kwargs={"user_id": user.id}
    )

    # Create movie instances using the MovieFactory
    movie1 = MovieFactory(
        title="The Godfather",
        release_year=1972,
        extra_data={
            "directors": ["Francis Ford Coppola"],
            "genres": ["Crime", "Drama"],
        },
    )
    movie2 = MovieFactory(
        title="Taxi Driver",
        release_year=1976,
        extra_data={"directors": ["Martin Scorsese"], "genres": ["Crime", "Drama"]},
    )

    # Add movies to watch history using their IDs
    for movie in [movie1, movie2]:
        response = client.post(watch_history_url, {"id": movie.id}, format="json")
        assert response.status_code == 201, response.json()

    # Retrieve watch history to verify the addition
    response = client.get(watch_history_url)
    assert response.status_code == 200
    # This assumes your response includes the movie IDs in the watch history
    retrieved_movie_titles = [item["title"] for item in response.data["watch_history"]]
    for movie_title in [movie1.title, movie2.title]:
        assert movie_title in retrieved_movie_titles


@pytest.mark.django_db
def test_add_invalid_movie_id_to_watch_history() -> None:
    # Arrange: Create a user instance using Factory Boy
    user = UserFactory()
    client = APIClient()
    watch_history_url = reverse(
        "movies:user-watch-history", kwargs={"user_id": user.id}
    )

    # Act: Attempt to add a non-existent movie to the user's watch history
    invalid_movie_id = 99999  # Assuming this ID does not exist in the database
    response = client.post(
        watch_history_url, {"movie_id": invalid_movie_id}, format="json"
    )

    # Assert: Check for a 400 Bad Request response
    assert (
        response.status_code == 400
    ), "Expected a 400 Bad Request response for an invalid movie ID"


test_data = [
    (
        "file.csv",
        "text/csv",
        b'title,genres,extra_data\ntest,comedy,{"directors": ["name"]}\n',
        201,
    ),  # Expected to succeed for CSV
    (
        "file.json",
        "application/json",
        b'[{"title": "test", "genres": ["comedy"], "extra_data": {"directors": ["name"]}}]',
        201,
    ),  # Expected to succeed for JSON
    (
        "file.txt",
        "text/plain",
        b"This is a test.",
        400,
    ),  # Unsupported file type, expecting failure
]


@pytest.mark.parametrize(
    "file_name, content_type, file_content, expected_status", test_data
)
@pytest.mark.django_db
def test_general_upload_view(
    client: APIClient,
    file_name: str,
    content_type: str,
    file_content: str,
    expected_status: int,
) -> None:
    # Generate the URL dynamically using 'reverse'
    url = reverse("movies:file-upload")

    # Create an in-memory uploaded file
    uploaded_file = SimpleUploadedFile(
        name=file_name, content=file_content, content_type=content_type
    )

    # Make a POST request to the GeneralUploadView endpoint
    response = client.post(url, {"file": uploaded_file}, format="multipart")

    # Assert that the response status code matches the expected status
    assert response.status_code == expected_status, response.json()
