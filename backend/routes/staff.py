from flask import Blueprint, request, jsonify, session, current_app
from models import db, User, Trek, Booking

staff_bp = Blueprint('staff', __name__)

def check_staff():
    user_id = session.get('user_id')
    if not user_id:
        return None, jsonify({'error': 'Unauthorized. Please login.'}), 401
    user = User.query.get(user_id)
    if not user or user.status != 'Approved':
        return None, jsonify({'error': 'Unauthorized or account inactive.'}), 403
    if user.role != 'Staff':
        return None, jsonify({'error': 'Access forbidden. Staff role required.'}), 403
    return user, None, None

@staff_bp.route('/api/staff/treks', methods=['GET'])
def staff_get_treks():
    user, err_resp, err_code = check_staff()
    if err_resp:
        return err_resp, err_code

    staff_id = session['user_id']
    treks = Trek.query.filter_by(staff_id=staff_id).all()
    
    results = []
    for t in treks:
        results.append({
            'id': t.id,
            'trek_name': t.trek_name,
            'location': t.location,
            'difficulty': t.difficulty,
            'slots': t.slots,
            'status': t.status,
            'duration_days': t.duration_days,
            'start_date': t.start_date.strftime('%Y-%m-%d') if t.start_date else '',
            'end_date': t.end_date.strftime('%Y-%m-%d') if t.end_date else '',
            'registered_users_count': len(t.bookings)
        })
    return jsonify(results)

@staff_bp.route('/api/staff/treks/<int:trek_id>', methods=['PUT'])
def staff_update_trek(trek_id):
    user, err_resp, err_code = check_staff()
    if err_resp:
        return err_resp, err_code

    staff_id = session['user_id']
    trek = Trek.query.get_or_404(trek_id)
    
    if trek.staff_id != staff_id:
        return jsonify({'error': 'Unauthorized. You are not assigned to manage this trek.'}), 403

    data = request.get_json() or {}
    
    if 'slots' in data:
        trek.slots = int(data.get('slots'))
    if 'status' in data:
        new_status = data.get('status')
        if new_status in ['Open', 'Closed', 'Completed', 'Approved', 'Pending']:
            trek.status = new_status
            
            if new_status == 'Completed':
                for b in trek.bookings:
                    if b.status == 'Booked':
                        b.status = 'Completed'

    db.session.commit()
    
    # Invalidate Cache
    current_app.cache.delete('users_open_treks')
    return jsonify({'message': 'Trek details successfully updated by staff.'})

@staff_bp.route('/api/staff/treks/<int:trek_id>/users', methods=['GET'])
def staff_get_trek_participants(trek_id):
    user, err_resp, err_code = check_staff()
    if err_resp:
        return err_resp, err_code

    staff_id = session['user_id']
    trek = Trek.query.get_or_404(trek_id)
    
    if trek.staff_id != staff_id:
        return jsonify({'error': 'Unauthorized. You are not assigned to manage this trek.'}), 403

    bookings = Booking.query.filter_by(trek_id=trek_id).all()
    results = []
    for b in bookings:
        user_obj = b.user
        results.append({
            'booking_id': b.id,
            'user_id': user_obj.id,
            'name': user_obj.name,
            'email': user_obj.email,
            'phone': user_obj.phone,
            'booking_status': b.status
        })
    return jsonify(results)
