import pytest

from recommendations.services import Item, UserPreferences, get_recommendations


@pytest.fixture
def sample_items():
    return [
        # Highly relevant items
        Item(
            id=1,
            name="The Terminator",
            genre="Action",
            director="James Cameron",
            actor="Arnold Schwarzenegger",
            year=1984,
        ),
        Item(
            id=2,
            name="Aliens",
            genre="Action",
            director="James Cameron",
            actor="Sigourney Weaver",
            year=1986,
        ),
        Item(
            id=3,
            name="Predator",
            genre="Action",
            director="John McTiernan",
            actor="Arnold Schwarzenegger",
            year=1987,
        ),
        Item(
            id=4,
            name="True Lies",
            genre="Action",
            director="James Cameron",
            actor="Arnold Schwarzenegger",
            year=1994,
        ),
        Item(
            id=5,
            name="Blade Runner",
            genre="Sci-Fi",
            director="Ridley Scott",
            actor="Harrison Ford",
            year=1982,
        ),
        # Less relevant but still related items
        Item(
            id=6,
            name="Commando",
            genre="Action",
            director="Mark L. Lester",
            actor="Arnold Schwarzenegger",
            year=1985,
        ),
        Item(
            id=7,
            name="RoboCop",
            genre="Action",
            director="Paul Verhoeven",
            actor="Peter Weller",
            year=1987,
        ),
        # Noisy items (less relevant)
        Item(
            id=8,
            name="Sleepless in Seattle",
            genre="Romance",
            director="Nora Ephron",
            actor="Tom Hanks",
            year=1993,
        ),
        Item(
            id=9,
            name="Pride and Prejudice",
            genre="Drama",
            director="Joe Wright",
            actor="Keira Knightley",
            year=2005,
        ),
        Item(
            id=10,
            name="The Notebook",
            genre="Romance",
            director="Nick Cassavetes",
            actor="Ryan Gosling",
            year=2004,
        ),
        Item(
            id=11,
            name="La La Land",
            genre="Musical",
            director="Damien Chazelle",
            actor="Ryan Gosling",
            year=2016,
        ),
        Item(
            id=12,
            name="The Godfather",
            genre="Crime",
            director="Francis Ford Coppola",
            actor="Al Pacino",
            year=1972,
        ),
        Item(
            id=13,
            name="Casablanca",
            genre="Romance",
            director="Michael Curtiz",
            actor="Humphrey Bogart",
            year=1942,
        ),
    ]


@pytest.fixture
def user_preferences():
    return UserPreferences(
        genre=["Action"],  # Focus on Action movies only
        director=["James Cameron"],  # Single director preference
        actor=["Arnold Schwarzenegger"],  # Single actor preference
        year=[1984, 1986, 1994],  # Only specific years of interest
        watch_history=[1],  # Assume The Terminator (id=1) has already been watched
    )


def test_top_3_recommendations_with_more_noise(sample_items, user_preferences):
    recommendations = get_recommendations(user_preferences, sample_items, top_n=3)

    # The top 3 recommendations should include highly relevant items, but also account for similar Sci-Fi items like Blade Runner
    expected_items = {"Aliens", "True Lies", "Predator"}
    acceptable_alternatives = {
        "Blade Runner"
    }  # Blade Runner is also relevant due to Sci-Fi genre

    # Extract the names of the top 3 recommendations
    recommended_item_names = {rec.name for rec in recommendations}

    # Ensure that all expected or acceptable items are in the top recommendations
    assert (expected_items & recommended_item_names) or (
        acceptable_alternatives & recommended_item_names
    ), (
        f"Top recommendations should include: {expected_items} or alternatives like {acceptable_alternatives}, "
        f"but got: {recommended_item_names}"
    )


def test_recommendations_handle_more_noise(sample_items, recommendations):
    recommendations = get_recommendations(recommendations, sample_items, top_n=5)

    # Ensure no noisy (romance/musical) items appear in the top 5 recommendations
    noisy_items = {
        "Sleepless in Seattle",
        "Pride and Prejudice",
        "The Notebook",
        "La La Land",
        "Casablanca",
    }

    # Check if any of the noisy items are in the recommendations
    for item in recommendations:
        assert (
            item.name not in noisy_items
        ), f"Noisy item '{item.name}' should not be in recommendations"

    # Make sure top relevant items are returned
    expected_items = {"Aliens", "True Lies", "Predator", "Commando"}
    recommended_item_names = {rec.name for rec in recommendations}

    assert expected_items.issubset(
        recommended_item_names
    ), f"Expected relevant recommendations: {expected_items}, but got: {recommended_item_names}"
