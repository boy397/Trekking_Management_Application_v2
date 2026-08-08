import os
import csv
import json
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, date
from celery import shared_task
from models import db, User, Trek, Booking

def log_job(job_name, message):
    log_file = 'job_logs.json'
    logs = []
    if os.path.exists(log_file):
        try:
            with open(log_file, 'r') as f:
                logs = json.load(f)
        except Exception:
            logs = []
    
    logs.append({
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'job': job_name,
        'message': message
    })
    logs = logs[-100:]  # Keep last 100 logs
    try:
        with open(log_file, 'w') as f:
            json.dump(logs, f)
    except Exception:
        pass

@shared_task
def send_daily_reminders_task():
    """Daily reminder task: checks upcoming treks starting in <= 3 days."""
    try:
        today = date.today()
        active_bookings = Booking.query.filter_by(status='Booked').all()
        reminded_count = 0
        
        for booking in active_bookings:
            trek = Trek.query.get(booking.trek_id)
            user = User.query.get(booking.user_id)
            
            if trek and user and trek.start_date:
                days_until = (trek.start_date - today).days
                if 0 <= days_until <= 3:
                    # Simulate sending email/SMS notification
                    print(f"[REMINDER] Sent notification to {user.name} ({user.email}) for trek '{trek.trek_name}' starting in {days_until} days.")
                    reminded_count += 1
                    
        log_job("Daily Reminders Task", f"Scan complete. Sent notifications to {reminded_count} users for upcoming treks.")
        return f"Sent {reminded_count} reminders"
    except Exception as e:
        log_job("Daily Reminders Error", str(e))
        return f"Error: {str(e)}"

@shared_task
def generate_monthly_report_task():
    """Monthly statistical summary report for the Admin."""
    try:
        total_treks = Trek.query.count()
        completed_treks = Trek.query.filter_by(status='Completed').count()
        open_treks = Trek.query.filter_by(status='Open').count()
        total_bookings = Booking.query.count()
        booked = Booking.query.filter_by(status='Booked').count()
        cancelled = Booking.query.filter_by(status='Cancelled').count()
        
        report_html = f"""
        <html>
        <body>
            <h2>Trekking Management Monthly Report</h2>
            <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <ul>
                <li>Total Trek Routes: {total_treks}</li>
                <li>Completed Treks: {completed_treks}</li>
                <li>Open Treks: {open_treks}</li>
                <li>Total Bookings: {total_bookings} (Booked: {booked}, Cancelled: {cancelled})</li>
            </ul>
        </body>
        </html>
        """
        os.makedirs('static/reports', exist_ok=True)
        report_path = 'static/reports/monthly_report.html'
        with open(report_path, 'w') as f:
            f.write(report_html)
            
        log_job("Monthly Activity Report Task", f"Report generated successfully. Total bookings tracked: {total_bookings}")
        return "Report generated successfully"
    except Exception as e:
        log_job("Monthly Report Error", str(e))
        return f"Error: {str(e)}"

@shared_task
def export_user_bookings_csv_task(user_id, filename):
    """Asynchronous CSV export task for a user's booking history."""
    status_file = f'static/exports/status_{user_id}.json'
    os.makedirs('static/exports', exist_ok=True)
    
    try:
        # Update status to Pending
        with open(status_file, 'w') as f:
            json.dump({'status': 'Pending', 'filename': filename}, f)
            
        user = User.query.get(user_id)
        if not user:
            raise Exception("User not found")
            
        # Simulate processing delay
        time.sleep(2)
        
        bookings = Booking.query.filter_by(user_id=user_id).all()
        filepath = os.path.join('static/exports', filename)
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Booking ID', 'Trek ID', 'Trek Name', 'Location', 'Difficulty', 'Duration (Days)', 'Start Date', 'End Date', 'Booking Status'])
            
            for b in bookings:
                t = Trek.query.get(b.trek_id)
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
                
        # Update status to Ready
        with open(status_file, 'w') as f:
            json.dump({
                'status': 'Ready',
                'filename': filename,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }, f)
            
        log_job("CSV History Export Task", f"Export complete for {user.name} ({user.email}). File saved: {filename}")
        return f"Exported {len(bookings)} bookings"
    except Exception as e:
        with open(status_file, 'w') as f:
            json.dump({'status': 'Failed', 'message': str(e)}, f)
        log_job("CSV Export Task Error", str(e))
        return f"Error: {str(e)}"

@shared_task
def send_staff_credentials_email(email, password, name):
    """Task to send an email to new staff with their credentials."""
    try:
        sender_email = os.environ.get('MAIL_DEFAULT_SENDER', 'admin@trek.com')
        smtp_server = os.environ.get('MAIL_SERVER', 'localhost')
        smtp_port = int(os.environ.get('MAIL_PORT', 1025))
        smtp_user = os.environ.get('MAIL_USERNAME', '')
        smtp_password = os.environ.get('MAIL_PASSWORD', '')

        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = email
        msg['Subject'] = 'Your Staff Account Credentials'
        
        body = f"Hello {name},\n\nYour staff account has been created successfully.\n\nHere are your login credentials:\nEmail: {email}\nPassword: {password}\n\nPlease login and change your password as soon as possible.\n\nBest Regards,\nTrekking Management System"
        msg.attach(MIMEText(body, 'plain'))
        
        try:
            # We will try to connect to SMTP
            server = smtplib.SMTP(smtp_server, smtp_port)
            if smtp_user and smtp_password:
                server.login(smtp_user, smtp_password)
            text = msg.as_string()
            server.sendmail(sender_email, email, text)
            server.quit()
            print(f"[EMAIL SENT] Sent credentials to {email}")
        except Exception as smtp_e:
            print(f"[EMAIL SIMULATION] Could not connect to SMTP server. Simulated sending to {email}: {password}")
            log_job("Staff Credentials Email Warning", f"Could not connect to SMTP. Simulated sending. {str(smtp_e)}")
            
        log_job("Staff Credentials Email", f"Processed credentials email for {email}")
        return f"Processed credentials for {email}"
    except Exception as e:
        log_job("Staff Credentials Email Error", str(e))
        return f"Error: {str(e)}"
