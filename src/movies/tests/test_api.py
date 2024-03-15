import json
import pytest
from django.urls import reverse
from rest_framework import status

from movies.models import Movie
from .factories import (
    MovieFactory,
)


@pytest.mark.django_db
def test_create_movie(client):
    url = reverse("movies:movie-api")
    data = {"title": "A New Hope", "genres": json.dumps(["Sci-Fi", "Adventure"])}

    response = client.post(url, data=data)

    assert response.status_code == status.HTTP_201_CREATED, response.json()
    assert Movie.objects.filter(title="A New Hope").exists()
    assert Movie.objects.filter(title="A New Hope").count() == 1


@pytest.mark.django_db
def test_retrieve_movie(client):
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
def test_update_movie(client):
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
def test_delete_movie(client):
    movie = MovieFactory()
    url = reverse("movies:movie-api-detail", kwargs={"pk": movie.id})

    response = client.delete(url)

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not Movie.objects.filter(id=movie.id).exists()


@pytest.mark.django_db
def test_list_movies_with_pagination(client):
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
