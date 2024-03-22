from typing import Any, Type

from django.contrib.auth import get_user_model
from django.db.models.base import ModelBase
from django.db.models.signals import post_save
from django.dispatch import receiver

from movies.models import UserMoviePreferences

User = get_user_model()


@receiver(post_save, sender=User)
def create_or_update_user_movie_preferences(
    sender: Type[ModelBase], instance: Any, created: bool, **kwargs: dict[str, Any]
) -> None:
    if created:
        UserMoviePreferences.objects.create(user=instance)
    else:
        instance.movie_preferences.save()
