from celery import Celery
import os

# Initialize Celery with Redis broker and backend
app = Celery(
    "tasks",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

# Celery beat schedule to run the task every hour
app.conf.beat_schedule = {
    "filter-suspicious-data-every-hour": {
        "task": "machine_learning.filter_data.filter_suspicious_data_task",
        "schedule": 3600.0,  # Run every hour (in seconds)
    }
}
app.conf.timezone = "UTC"
