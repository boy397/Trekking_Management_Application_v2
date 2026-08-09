from app import app, celery

# Ensure tasks are registered with Celery
import tasks
