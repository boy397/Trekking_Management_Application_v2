import os
import threading
from flask import Flask
from dotenv import load_dotenv
from flask_cors import CORS

# Load environment variables
load_dotenv()

# Import Database and Models
from models import db, User, Trek, Booking

app = Flask(__name__)
CORS(app, supports_credentials=True)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'tma_super_secret_key_9876543210')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///trekking.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Celery Configurations pointing to Redis Broker
app.config["CELERY"] = {
    "broker_url": os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    "result_backend": os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    "task_ignore_result": True,
}


# Initialize Database
db.init_app(app)

# Initialize Caching Manager from cache.py
from cache import CacheManager
app.cache = CacheManager()

# Import Blueprints
from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.staff import staff_bp
from routes.user import user_bp

# Register Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(staff_bp)
app.register_blueprint(user_bp)



# Ensure database tables exist and seed Admin user on startup
with app.app_context():
    db.create_all()
    admin = User.query.filter_by(role='Admin').first()
    if not admin:
        admin_user = User(
            name="System Admin",
            email="admin@trek.com",
            password="admin123",
            phone="9999999999",
            role="Admin",
            status="Approved"
        )
        db.session.add(admin_user)
        db.session.commit()
        print("Successfully seeded database with Admin user (admin@trek.com / admin123)")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8085, debug=True)
