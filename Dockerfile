# --- Build Stage ---
FROM python:3.12.2-slim AS builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1 \
	PATH="/root/.rye/bin:$PATH" \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_PYTHON=python3.12 \
    UV_PROJECT_ENVIRONMENT=/app \
	DJANGO_SETTINGS_MODULE=recommendation_system.production

# Install dependencies
RUN apt-get update \
	&& apt-get install -y --no-install-recommends  build-essential curl libpq-dev

# Install Rye
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy the project files into the builder stage
RUN uv venv /app

WORKDIR /app

COPY pyproject.toml /app
COPY requirements.lock /app/uv.lock
COPY README.md /app
COPY src/manage.py /app
# Install project dependencies with Rye
RUN uv sync
# Copy the rest of the application's code
COPY src/ /app/

# --- Production Stage ---
# Define the base image for the production stage
FROM python:3.12.2-slim AS production

RUN apt-get update \
	&& apt-get install -y --no-install-recommends libpq-dev


# Copy virtual env and other necessary files from builder stage
# Copy installed packages and binaries from builder stage
COPY --from=builder /app /app

# Set the working directory in the container
WORKDIR /app

# Set user to use when running the image
# UID 1000 is often the default user
RUN groupadd -r django && useradd -r -g django -d /app -s /bin/bash django && \
chown -R django:django /app

USER django

# Start Gunicorn with a configuration file
CMD ["/app/bin/gunicorn", "--bind", "0.0.0.0:8000", "recommendation_system.wsgi"]

# Inform Docker that the container listens on the specified network ports at runtime
EXPOSE 8000
