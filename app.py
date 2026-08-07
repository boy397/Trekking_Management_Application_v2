import os
import time
import json
import csv
import threading
from datetime import datetime, date
from flask import Flask, render_template
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import Database and Models
from models import db, User, Trek, Booking

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'tma_super_secret_key_9876543210')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///trekking.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Enable CORS for all API endpoints
CORS(app)

# Initialize Database
db.init_app(app)

# ----------------------------------------------------------------
# INLINE REDIS CACHING WITH IN-MEMORY FALLBACK
# ----------------------------------------------------------------
class CacheManager:
    def __init__(self):
        self.redis_client = None
        self.memory_cache = {}
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        try:
            import redis
            self.redis_client = redis.Redis.from_url(redis_url, socket_timeout=1)
            self.redis_client.ping()
            print("Connected to Redis successfully for caching.")
        except Exception as e:
            print(f"Redis is not available. Falling back to In-Memory Cache. Error: {e}")
            self.redis_client = None

    def get(self, key):
        if self.redis_client:
            try:
                val = self.redis_client.get(key)
                if val:
                    return json.loads(val.decode('utf-8'))
            except Exception:
                pass
        return self.memory_cache.get(key)

    def set(self, key, value, timeout=300):
        if self.redis_client:
            try:
                self.redis_client.setex(key, timeout, json.dumps(value))
                return
            except Exception:
                pass
        self.memory_cache[key] = value

    def delete(self, key):
        if self.redis_client:
            try:
                self.redis_client.delete(key)
                return
            except Exception:
                pass
        if key in self.memory_cache:
            del self.memory_cache[key]

    def clear(self):
        if self.redis_client:
            try:
                self.redis_client.flushdb()
                return
            except Exception:
                pass
        self.memory_cache.clear()

app.cache = CacheManager()

# ----------------------------------------------------------------
# INLINE BACKGROUND JOBS (NO CELERY, NO UTILS)
# ----------------------------------------------------------------
app.job_logs = []
app.export_status = {}  # user_id -> {'status': 'Pending'/'Ready', 'filename': '...'}

def log_job(app_inst, job_name, message):
    log_entry = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'job': job_name,
        'message': message
    }
    app_inst.job_logs.insert(0, log_entry)
    print(f"[{job_name}] {message}")

def run_daily_reminders(app_inst):
    """Daily Reminder: checks upcoming bookings and notifies users."""
    with app_inst.app_context():
        try:
            today = date.today()
            active_bookings = Booking.query.filter_by(status='Booked').all()
            notified_count = 0
            
            for booking in active_bookings:
                trek = booking.trek
                user = booking.user
                if trek and trek.start_date:
                    days_until = (trek.start_date - today).days
                    if 0 <= days_until <= 3:
                        msg = f"Reminder to {user.name} ({user.email}): Your trek '{trek.trek_name}' is starting on {trek.start_date} in {days_until} days! Location: {trek.location}. Instructions: Pack warm clothes, stay hydrated, and bring trekking gear."
                        log_job(app_inst, "Daily Reminders", msg)
                        notified_count += 1
            
            if notified_count == 0:
                log_job(app_inst, "Daily Reminders", "Completed. No upcoming treks starting in the next 3 days found.")
            else:
                log_job(app_inst, "Daily Reminders", f"Completed. Sent {notified_count} reminders to trekkers.")
        except Exception as e:
            log_job(app_inst, "Daily Reminders Error", str(e))

def run_monthly_report(app_inst):
    """Monthly Activity Report: generated for Admin on the 1st of every month."""
    with app_inst.app_context():
        try:
            total_treks = Trek.query.count()
            completed_treks = Trek.query.filter_by(status='Completed').count()
            total_users = User.query.filter_by(role='User').count()
            total_bookings = Booking.query.count()
            
            treks = Trek.query.all()
            trek_bookings = []
            for t in treks:
                trek_bookings.append({
                    'name': t.trek_name,
                    'location': t.location,
                    'bookings_count': len(t.bookings)
                })
            trek_bookings.sort(key=lambda x: x['bookings_count'], reverse=True)
            popular_treks = trek_bookings[:3]
            
            report_html = f"""
            <html>
            <head><style>body {{ font-family: Arial, sans-serif; }} table {{ border-collapse: collapse; width: 100%; }} th, td {{ border: 1px solid #ddd; padding: 8px; }} th {{ background-color: #f2f2f2; }}</style></head>
            <body>
                <h2>Monthly Trekking Activity Report</h2>
                <p>Report Generated On: {datetime.now().strftime('%Y-%m-%d')}</p>
                <hr/>
                <h4>Overall Metrics:</h4>
                <ul>
                    <li>Total Treks Configured: {total_treks}</li>
                    <li>Completed Treks: {completed_treks}</li>
                    <li>Total Registered Trekkers: {total_users}</li>
                    <li>Total Bookings Registered: {total_bookings}</li>
                </ul>
                <h4>Top Popular Treks:</h4>
                <table>
                    <tr><th>Trek Name</th><th>Location</th><th>Total Bookings</th></tr>
            """
            for pt in popular_treks:
                report_html += f"<tr><td>{pt['name']}</td><td>{pt['location']}</td><td>{pt['bookings_count']}</td></tr>"
            
            report_html += """
                </table>
                <br/>
                <p>Regards,<br/>Trekking Management System Automations</p>
            </body>
            </html>
            """
            
            log_job(app_inst, "Monthly Activity Report", f"HTML Report generated for Admin: {total_bookings} bookings tracked this period. Top trek is '{popular_treks[0]['name'] if popular_treks else 'N/A'}'")
        except Exception as e:
            log_job(app_inst, "Monthly Activity Report Error", str(e))

def async_csv_export(app_inst, user_id):
    """Async background task to export booking history for a user."""
    time.sleep(2)
    with app_inst.app_context():
        try:
            user = User.query.get(user_id)
            if not user:
                app_inst.export_status[user_id] = {'status': 'Failed', 'message': 'User not found'}
                return
            
            bookings = Booking.query.filter_by(user_id=user_id).all()
            filename = f"booking_history_user_{user_id}.csv"
            filepath = os.path.join(app_inst.root_path, 'static', 'exports', filename)
            
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            with open(filepath, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Booking ID', 'Trek ID', 'Trek Name', 'Location', 'Difficulty', 'Duration (Days)', 'Start Date', 'End Date', 'Booking Status'])
                for b in bookings:
                    t = b.trek
                    writer.writerow([
                        b.id,
                        t.id if t else 'N/A',
                        t.trek_name if t else 'N/A',
                        t.location if t else 'N/A',
                        t.difficulty if t else 'N/A',
                        t.duration_days if t else 'N/A',
                        t.start_date.strftime('%Y-%m-%d') if t and t.start_date else 'N/A',
                        t.end_date.strftime('%Y-%m-%d') if t and t.end_date else 'N/A',
                        b.status
                    ])
            
            app_inst.export_status[user_id] = {
                'status': 'Ready',
                'filename': filename,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            log_job(app_inst, "CSV History Export", f"Completed history export for User '{user.name}' ({user.email}). File saved as {filename}")
        except Exception as e:
            app_inst.export_status[user_id] = {'status': 'Failed', 'message': str(e)}
            log_job(app_inst, "CSV History Export Error", str(e))

# Setup export function reference on the app object for Blueprints to call
app.async_csv_export = async_csv_export
app.run_daily_reminders = run_daily_reminders
app.run_monthly_report = run_monthly_report

def scheduler_loop(app_inst):
    time.sleep(5)
    log_job(app_inst, "Scheduler Engine", "Background job runner successfully started.")
    
    last_daily_run = None
    last_monthly_run = None
    
    while True:
        try:
            now = datetime.now()
            
            if last_daily_run is None or last_daily_run.date() != now.date():
                run_daily_reminders(app_inst)
                last_daily_run = now
            
            if last_monthly_run is None or (now.day == 1 and last_monthly_run.month != now.month):
                run_monthly_report(app_inst)
                last_monthly_run = now
                
        except Exception as e:
            print(f"Error in scheduler thread: {e}")
        
        time.sleep(60)

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

# Page Routing (Entry Point for Vue)
@app.route('/')
def index():
    return app.send_static_file('index.html')

# Startup hook to prepare database and initialize threads
if __name__ == '__main__':
    with app.app_context():
        # Ensure database tables exist
        db.create_all()
        
        # Check if Admin user already exists, if not create one
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
            
    # Initialize background scheduler thread
    threading.Thread(target=scheduler_loop, args=(app,), daemon=True).start()
    
    app.run(host='0.0.0.0', port=5000, debug=True)
