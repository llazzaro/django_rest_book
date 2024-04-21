from celery import Celery

# Create a Celery instance and configure it to use Redis as the message broker
app = Celery("example", broker="redis://localhost:6379/0")


# Define a task
@app.task
def long_running_task(x):
    import time

    time.sleep(5)  # Simulate a long-running operation
    return x * x
