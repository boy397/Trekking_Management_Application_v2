from flask import Blueprint, request, jsonify, session
from models import db, User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    phone = data.get('phone')

    if not name or not email or not password or not phone:
        return jsonify({'error': 'Missing required registration details.'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'User with this email already exists.'}), 400

    new_user = User(
        name=name,
        email=email,
        password=password, # plain string password for 1/10 complexity
        phone=phone,
        role='User',
        status='Approved'
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'Registration successful! Please log in.'}), 201

@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'error': 'Missing email or password.'}), 400

    user = User.query.filter_by(email=email).first()
    if not user or user.password != password:
        return jsonify({'error': 'Invalid email or password.'}), 401

    if user.status != 'Approved':
        return jsonify({'error': f'Your account is {user.status.lower()}. Access denied.'}), 403

    session['user_id'] = user.id
    return jsonify({
        'message': 'Login successful!',
        'user': {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'phone': user.phone,
            'role': user.role,
            'status': user.status
        }
    })

@auth_bp.route('/api/auth/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return jsonify({'message': 'Logged out successfully.'})

@auth_bp.route('/api/auth/me', methods=['GET'])
def get_me():
    if 'user_id' not in session:
        return jsonify({'logged_in': False}), 200
    
    user = User.query.get(session['user_id'])
    if not user or user.status != 'Approved':
        session.pop('user_id', None)
        return jsonify({'logged_in': False}), 200

    return jsonify({
        'logged_in': True,
        'user': {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'phone': user.phone,
            'role': user.role,
            'status': user.status
        }
    })
