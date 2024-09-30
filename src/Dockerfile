# --- Build Stage ---
FROM python:3.12.2-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1 \
	PATH="/root/.rye/bin:$PATH" \
	DJANGO_SETTINGS_MODULE=recommendation_system.production

# Install dependencies
RUN apt-get update \
	&& apt-get install -y --no-install-recommends curl libpq-dev

# Install Rye
RUN pip install rye

# Copy the project files into the builder stage
WORKDIR /app

COPY requirements.lock ./
# Install project dependencies with Rye
RUN rye pip install --no-cache --system -r requirements.lock

# Copy the rest of the application's code
COPY recommendation_system /app

# Collect static files
RUN rye run python manage.py collectstatic --noinput


# --- Production Stage ---
# Define the base image for the production stage
FROM python:3.12.2-slim as production

# Copy virtual env and other necessary files from builder stage
# Copy installed packages and binaries from builder stage
COPY --from=builder /usr/local /usr/local
COPY --from=builder /app /app

# Set the working directory in the container
WORKDIR /app

# Set user to use when running the image
# UID 1000 is often the default user
RUN groupadd -r django && useradd --no-log-init -r -g django && \
	chown -R django:django /app
USER django

# Start Gunicorn with a configuration file
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "recommendation_system.wsgi"]

# Inform Docker that the container listens on the specified network ports at runtime
EXPOSE 8000
