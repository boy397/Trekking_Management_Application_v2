import jwt
import datetime
from flask import current_app

def generate_token(user_id):
    """
    Generates the Auth Token
    :return: string
    """
    try:
        payload = {
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1, seconds=5),
            'iat': datetime.datetime.utcnow(),
            'sub': str(user_id)
        }
        return jwt.encode(
            payload,
            current_app.config.get('SECRET_KEY'),
            algorithm='HS256'
        )
    except Exception as e:
        return str(e)

def decode_token(auth_token):
    """
    Decodes the auth token
    :param auth_token:
    :return: (user_id, error_string)
    """
    try:
        payload = jwt.decode(auth_token, current_app.config.get('SECRET_KEY'), algorithms=['HS256'])
        return int(payload['sub']), None
    except jwt.ExpiredSignatureError:
        return None, 'Signature expired. Please log in again.'
    except jwt.InvalidTokenError as e:
        return None, f'Invalid token: {str(e)}'
    except Exception as e:
        return None, f'Other error: {str(e)}'
