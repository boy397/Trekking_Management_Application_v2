import os
import json
import threading
from flask import Blueprint, request, jsonify, send_from_directory, current_app
from models import db, User, Trek, Booking
from utils import decode_token

user_bp = Blueprint('user', __name__)

def check_user():
    auth_header = request.headers.get('Authorization')
    token = None
    
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
    elif request.args.get('token'):
        token = request.args.get('token')
        
    if not token:
        return None, jsonify({'error': 'Unauthorized. Please login.'}), 401
        
    user_id, error_msg = decode_token(token)
    if error_msg:
        return None, jsonify({'error': error_msg}), 401
    
    user = User.query.get(user_id)
    if not user or user.status != 'Approved':
        return None, jsonify({'error': 'Unauthorized or account inactive.'}), 403
    if user.role != 'User':
        return None, jsonify({'error': 'Access forbidden. User role required.'}), 403
    return user, None, None

@user_bp.route('/api/users/treks', methods=['GET'])
def user_get_treks():
    user, err_resp, err_code = check_user()
    if err_resp:
        return err_resp, err_code

    cached_data = current_app.cache.get('users_open_treks')
    if cached_data:
        results = cached_data
    else:
        treks = Trek.query.filter(Trek.status.in_(['Open', 'Approved'])).all()
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
                'staff_name': staff.name if staff else 'Unassigned',
                'description': t.description,
                'start_date': t.start_date.strftime('%Y-%m-%d') if t.start_date else '',
                'end_date': t.end_date.strftime('%Y-%m-%d') if t.end_date else ''
            })
        current_app.cache.set('users_open_treks', results, timeout=300)

    search = request.args.get('search', '').lower()
    difficulty = request.args.get('difficulty', '')
    location = request.args.get('location', '').lower()
    max_duration = request.args.get('duration', '')

    filtered_results = []
    for r in results:
        if search and (search not in r['trek_name'].lower() and search not in r['location'].lower()):
            continue
        if difficulty and r['difficulty'] != difficulty:
            continue
        if location and location not in r['location'].lower():
            continue
        if max_duration:
            try:
                if r['duration_days'] > int(max_duration):
                    continue
            except ValueError:
                pass
        filtered_results.append(r)

    return jsonify(filtered_results)

@user_bp.route('/api/users/bookings', methods=['POST'])
def user_book_trek():
    user, err_resp, err_code = check_user()
    if err_resp:
        return err_resp, err_code

    user_id = user.id
    data = request.get_json() or {}
    trek_id = data.get('trek_id')

    if not trek_id:
        return jsonify({'error': 'Trek ID is required to book.'}), 400

    trek = Trek.query.get_or_404(trek_id)

    if trek.status != 'Open':
        return jsonify({'error': f'Booking is not allowed. Trek status is {trek.status}.'}), 400

    if trek.slots <= 0:
        return jsonify({'error': 'No available slots left for this trek.'}), 400

    existing_booking = Booking.query.filter_by(user_id=user_id, trek_id=trek_id).filter(Booking.status != 'Cancelled').first()
    if existing_booking:
        return jsonify({'error': 'You have already booked this trek.'}), 400

    new_booking = Booking(
        user_id=user_id,
        trek_id=trek_id,
        status='Booked'
    )
    trek.slots -= 1

    db.session.add(new_booking)
    db.session.commit()

    current_app.cache.delete('users_open_treks')

    return jsonify({'message': 'Trek booked successfully!', 'booking_id': new_booking.id}), 201

@user_bp.route('/api/users/bookings', methods=['GET'])
def user_get_bookings():
    user, err_resp, err_code = check_user()
    if err_resp:
        return err_resp, err_code

    user_id = user.id
    bookings = Booking.query.filter_by(user_id=user_id).all()
    
    results = []
    for b in bookings:
        t = b.trek
        results.append({
            'booking_id': b.id,
            'trek_id': b.trek_id,
            'trek_name': t.trek_name if t else 'Deleted Trek',
            'location': t.location if t else 'N/A',
            'difficulty': t.difficulty if t else 'N/A',
            'duration_days': t.duration_days if t else 0,
            'start_date': t.start_date.strftime('%Y-%m-%d') if t and t.start_date else 'N/A',
            'end_date': t.end_date.strftime('%Y-%m-%d') if t and t.end_date else 'N/A',
            'booking_date': b.booking_date.strftime('%Y-%m-%d %H:%M:%S') if b.booking_date else 'N/A',
            'status': b.status
        })
    return jsonify(results)

@user_bp.route('/api/users/bookings/<int:booking_id>/cancel', methods=['POST'])
def user_cancel_booking(booking_id):
    user, err_resp, err_code = check_user()
    if err_resp:
        return err_resp, err_code

    user_id = user.id
    booking = Booking.query.get_or_404(booking_id)

    if booking.user_id != user_id:
        return jsonify({'error': 'Unauthorized action.'}), 403

    if booking.status == 'Cancelled':
        return jsonify({'error': 'Booking is already cancelled.'}), 400

    if booking.status == 'Completed':
        return jsonify({'error': 'Cannot cancel a completed trek.'}), 400

    booking.status = 'Cancelled'
    
    trek = booking.trek
    if trek:
        trek.slots += 1

    db.session.commit()

    current_app.cache.delete('users_open_treks')

    return jsonify({'message': 'Booking cancelled successfully.'})

@user_bp.route('/api/users/profile', methods=['PUT'])
def user_update_profile():
    user, err_resp, err_code = check_user()
    if err_resp:
        return err_resp, err_code

    user_id = user.id
    user_obj = User.query.get(user_id)
    data = request.get_json() or {}

    name = data.get('name')
    phone = data.get('phone')

    if name:
        user_obj.name = name
    if phone:
        user_obj.phone = phone

    db.session.commit()
    return jsonify({
        'message': 'Profile updated successfully!',
        'user': {
            'id': user_obj.id,
            'name': user_obj.name,
            'email': user_obj.email,
            'phone': user_obj.phone,
            'role': user_obj.role,
            'status': user_obj.status
        }
    })

@user_bp.route('/api/users/export-history', methods=['POST'])
def user_export_history():
    user, err_resp, err_code = check_user()
    if err_resp:
        return err_resp, err_code

    user_id = user.id
    import time
    from tasks import export_user_bookings_csv_task
    
    filename = f"bookings_user_{user_id}_{int(time.time())}.csv"
    export_user_bookings_csv_task.delay(user_id, filename)
    
    return jsonify({
        'message': 'Export process triggered via Celery. You will be alerted when the download file is ready.',
        'status': 'Pending'
    })

@user_bp.route('/api/users/export-status', methods=['GET'])
def user_export_status():
    user, err_resp, err_code = check_user()
    if err_resp:
        return err_resp, err_code

    user_id = user.id
    status_file = f'static/exports/status_{user_id}.json'
    if os.path.exists(status_file):
        try:
            with open(status_file, 'r') as f:
                return jsonify(json.load(f))
        except Exception:
            return jsonify({'status': 'None'})
    return jsonify({'status': 'None'})

@user_bp.route('/api/users/download-export/<filename>', methods=['GET'])
def download_export(filename):
    user, err_resp, err_code = check_user()
    if err_resp:
        return err_resp, err_code

    user_id = user.id
    if f"user_{user_id}" not in filename:
        return jsonify({'error': 'Unauthorized file access.'}), 403
        
    directory = os.path.join(current_app.root_path, 'static', 'exports')
    return send_from_directory(directory, filename, as_attachment=True)
