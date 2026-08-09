from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from models import db, User, Trek, Booking
from tasks import send_staff_credentials_email
from utils import decode_token

admin_bp = Blueprint('admin', __name__)

def check_admin():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None, jsonify({'error': 'Unauthorized. Please login.'}), 401
        
    token = auth_header.split(' ')[1]
    user_id, error_msg = decode_token(token)
    if error_msg:
        return None, jsonify({'error': error_msg}), 401
    
    user = User.query.get(user_id)
    if not user or user.status != 'Approved':
        return None, jsonify({'error': 'Unauthorized or account inactive.'}), 403
    if user.role != 'Admin':
        return None, jsonify({'error': 'Access forbidden. Admin role required.'}), 403
    return user, None, None

@admin_bp.route('/api/admin/dashboard', methods=['GET'])
def admin_dashboard():
    user, err_resp, err_code = check_admin()
    if err_resp:
        return err_resp, err_code

    total_treks = Trek.query.count()
    total_users = User.query.filter_by(role='User').count()
    total_staff = User.query.filter_by(role='Staff').count()
    total_bookings = Booking.query.count()

    return jsonify({
        'total_treks': total_treks,
        'total_users': total_users,
        'total_staff': total_staff,
        'total_bookings': total_bookings
    })

@admin_bp.route('/api/admin/treks', methods=['GET'])
def admin_get_treks():
    user, err_resp, err_code = check_admin()
    if err_resp:
        return err_resp, err_code

    treks = Trek.query.all()
    results = []
    for t in treks:
        staff = User.query.get(t.staff_id) if t.staff_id else None
        results.append({
            'id': t.id,
            'trek_name': t.trek_name,
            'location': t.location,
            'difficulty': t.difficulty,
            'slots': t.slots,
            'status': t.status,
            'duration_days': t.duration_days,
            'staff_id': t.staff_id,
            'staff_name': staff.name if staff else 'Unassigned',
            'description': t.description,
            'start_date': t.start_date.strftime('%Y-%m-%d') if t.start_date else '',
            'end_date': t.end_date.strftime('%Y-%m-%d') if t.end_date else '',
            'bookings_count': len(t.bookings)
        })
    return jsonify(results)

@admin_bp.route('/api/admin/treks', methods=['POST'])
def admin_create_trek():
    user, err_resp, err_code = check_admin()
    if err_resp:
        return err_resp, err_code

    data = request.get_json() or {}
    trek_name = data.get('trek_name')
    location = data.get('location')
    difficulty = data.get('difficulty', 'Moderate')
    slots = int(data.get('slots', 0))
    status = data.get('status', 'Open')
    duration_days = int(data.get('duration_days', 1))
    staff_id = data.get('staff_id')
    description = data.get('description', '')
    
    start_date_str = data.get('start_date')
    end_date_str = data.get('end_date')
    
    start_date_obj = None
    end_date_obj = None
    if start_date_str:
        start_date_obj = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    if end_date_str:
        end_date_obj = datetime.strptime(end_date_str, '%Y-%m-%d').date()

    if not trek_name or not location:
        return jsonify({'error': 'Trek Name and Location are required.'}), 400

    new_trek = Trek(
        trek_name=trek_name,
        location=location,
        difficulty=difficulty,
        slots=slots,
        status=status,
        duration_days=duration_days,
        staff_id=staff_id if staff_id else None,
        description=description,
        start_date=start_date_obj,
        end_date=end_date_obj
    )
    db.session.add(new_trek)
    db.session.commit()
    
    # Invalidate Cache using app instance cache reference
    current_app.cache.delete('users_open_treks')
    return jsonify({'message': 'Trek created successfully!', 'id': new_trek.id}), 201

@admin_bp.route('/api/admin/treks/<int:trek_id>', methods=['PUT'])
def admin_update_trek(trek_id):
    user, err_resp, err_code = check_admin()
    if err_resp:
        return err_resp, err_code

    trek = Trek.query.get_or_404(trek_id)
    data = request.get_json() or {}

    trek.trek_name = data.get('trek_name', trek.trek_name)
    trek.location = data.get('location', trek.location)
    trek.difficulty = data.get('difficulty', trek.difficulty)
    trek.slots = int(data.get('slots', trek.slots))
    trek.status = data.get('status', trek.status)
    trek.duration_days = int(data.get('duration_days', trek.duration_days))
    trek.staff_id = data.get('staff_id') if data.get('staff_id') else None
    trek.description = data.get('description', trek.description)
    
    start_date_str = data.get('start_date')
    end_date_str = data.get('end_date')
    
    if start_date_str:
        trek.start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    else:
        trek.start_date = None
        
    if end_date_str:
        trek.end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    else:
        trek.end_date = None

    db.session.commit()
    
    # Invalidate Cache
    current_app.cache.delete('users_open_treks')
    return jsonify({'message': 'Trek updated successfully!'})

@admin_bp.route('/api/admin/treks/<int:trek_id>', methods=['DELETE'])
def admin_delete_trek(trek_id):
    user, err_resp, err_code = check_admin()
    if err_resp:
        return err_resp, err_code

    trek = Trek.query.get_or_404(trek_id)
    db.session.delete(trek)
    db.session.commit()
    
    # Invalidate Cache
    current_app.cache.delete('users_open_treks')
    return jsonify({'message': 'Trek deleted successfully!'})

@admin_bp.route('/api/admin/users-staff', methods=['GET'])
def admin_get_users_staff():
    user, err_resp, err_code = check_admin()
    if err_resp:
        return err_resp, err_code

    search = request.args.get('search', '').lower()
    
    users = User.query.all()
    results = []
    for u in users:
        if search and (search not in u.name.lower() and search not in u.email.lower() and search not in u.role.lower()):
            continue
            
        results.append({
            'id': u.id,
            'name': u.name,
            'email': u.email,
            'phone': u.phone,
            'role': u.role,
            'status': u.status,
            'created_at': u.created_at.strftime('%Y-%m-%d') if u.created_at else ''
        })
    return jsonify(results)

@admin_bp.route('/api/admin/staff', methods=['POST'])
def admin_add_staff():
    user, err_resp, err_code = check_admin()
    if err_resp:
        return err_resp, err_code

    data = request.get_json() or {}
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    phone = data.get('phone')

    if not name or not email or not password or not phone:
        return jsonify({'error': 'Missing required staff details.'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'A user/staff with this email already exists.'}), 400

    new_staff = User(
        name=name,
        email=email,
        password=password,
        phone=phone,
        role='Staff',
        status='Approved'
    )
    db.session.add(new_staff)
    db.session.commit()

    # Dispatch email task using celery
    send_staff_credentials_email.delay(email, password, name)

    return jsonify({'message': 'Trek Staff created successfully!'}), 201

@admin_bp.route('/api/admin/deactivate-blacklist', methods=['POST'])
def admin_deactivate_blacklist():
    user, err_resp, err_code = check_admin()
    if err_resp:
        return err_resp, err_code

    data = request.get_json() or {}
    user_id = data.get('user_id')
    action = data.get('action')

    if not user_id or not action:
        return jsonify({'error': 'User ID and Action are required.'}), 400

    user_obj = User.query.get_or_404(user_id)
    if user_obj.role == 'Admin':
        return jsonify({'error': 'Cannot modify Admin status.'}), 400

    if action not in ['Approved', 'Deactivated', 'Blacklisted']:
        return jsonify({'error': 'Invalid action status.'}), 400

    user_obj.status = action
    db.session.commit()
    return jsonify({'message': f"User status successfully updated to {action}!"})

@admin_bp.route('/api/admin/reports', methods=['GET'])
def admin_reports():
    user, err_resp, err_code = check_admin()
    if err_resp:
        return err_resp, err_code

    total_treks = Trek.query.count()
    completed_treks = Trek.query.filter_by(status='Completed').count()
    open_treks = Trek.query.filter_by(status='Open').count()
    
    total_bookings = Booking.query.count()
    booked_bookings = Booking.query.filter_by(status='Booked').count()
    cancelled_bookings = Booking.query.filter_by(status='Cancelled').count()
    
    treks = Trek.query.all()
    trek_stats = []
    for t in treks:
        trek_stats.append({
            'trek_name': t.trek_name,
            'location': t.location,
            'bookings_count': len(t.bookings),
            'status': t.status
        })
    trek_stats.sort(key=lambda x: x['bookings_count'], reverse=True)

    return jsonify({
        'total_treks': total_treks,
        'completed_treks': completed_treks,
        'open_treks': open_treks,
        'total_bookings': total_bookings,
        'booked_bookings': booked_bookings,
        'cancelled_bookings': cancelled_bookings,
        'popular_treks': trek_stats[:5]
    })

@admin_bp.route('/api/logs', methods=['GET'])
def get_job_logs():
    user, err_resp, err_code = check_admin()
    if err_resp:
        return err_resp, err_code
    import os, json
    if os.path.exists('job_logs.json'):
        try:
            with open('job_logs.json', 'r') as f:
                return jsonify(json.load(f))
        except Exception:
            return jsonify([])
    return jsonify([])

@admin_bp.route('/api/admin/trigger-job', methods=['POST'])
def trigger_manual_job():
    user, err_resp, err_code = check_admin()
    if err_resp:
        return err_resp, err_code

    data = request.get_json() or {}
    job_type = data.get('job_type')
    
    from tasks import send_daily_reminders_task, generate_monthly_report_task
    
    if job_type == 'reminders':
        send_daily_reminders_task.delay()
        return jsonify({'message': 'Daily reminders job triggered successfully via Celery.'})
    elif job_type == 'report':
        generate_monthly_report_task.delay()
        return jsonify({'message': 'Monthly activity report job triggered successfully via Celery.'})
    else:
        return jsonify({'error': 'Invalid job type.'}), 400
