from typing import Any, List, Optional

from pydantic import BaseModel
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# Define a generic Item model
class Item(BaseModel):
    id: int
    attributes: dict


class UserPreferences(BaseModel):
    preferences: Optional[dict] = None
    watch_history: Optional[List[int]] = []


def combine_attributes(item: Item) -> str:
    """
    Combines the attributes of an item into a single string for vectorization.
    If an attribute is a list (e.g., genres), it flattens the list into a space-separated string.
    """
    combined_attributes = []

    for value in item.attributes.values():
        if isinstance(value, list):
            # Flatten the list into a space-separated string
            combined_attributes.append(" ".join(v.lower() for v in value))
        else:
            # Convert the value to a string and make it lowercase
            combined_attributes.append(str(value).lower())

    return " ".join(combined_attributes).strip()


# Implement the get_recommendations function
def get_recommendations(
    user_preferences: UserPreferences, items: list[Item], top_n: int = 10
) -> list[Item]:
    # Combine item attributes into a single text field for vectorization
    combined_tags = [combine_attributes(item) for item in items]

    # Initialize a CountVectorizer
    cv = CountVectorizer(max_features=10000, stop_words="english")

    # Combine user preferences into a single text field
    raw_user_tags = []
    if user_preferences.preferences:
        for key, value in user_preferences.preferences.items():
            if isinstance(value, list):
                raw_user_tags += [str(v).lower() for v in value]
            else:
                raw_user_tags.append(str(value).lower())

    user_tags = " ".join(raw_user_tags)

    # Fit CountVectorizer on both the items and user preferences
    cv.fit(combined_tags + [user_tags])

    # Vectorize the combined tags and user preferences
    item_vectors = cv.transform(combined_tags).toarray()
    user_vector = cv.transform([user_tags]).toarray()

    # Calculate cosine similarity between the user preferences and all item vectors
    similarity_scores = cosine_similarity(user_vector, item_vectors)[0]

    # Rank items by similarity score and get top_n items
    ranked_items = sorted(
        enumerate(similarity_scores), key=lambda x: x[1], reverse=True
    )

    # Exclude items the user has already interacted with
    ranked_items = [
        items[i]
        for i, score in ranked_items
        if items[i].id not in user_preferences.watch_history
    ]

    # Return the top_n items
    return ranked_items[:top_n]
