from django.contrib import admin

from movies.models import Movie, UserMoviePreferences

admin.site.register(Movie)
admin.site.register(UserMoviePreferences)
