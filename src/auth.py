"""Application implementing authorization and registration processes"""

from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
import validators
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from flasgger import swag_from

from src.constants.http_status_codes import HTTP_400_BAD_REQUEST,\
                                            HTTP_409_CONFLICT,\
                                            HTTP_201_CREATED,\
                                            HTTP_401_UNAUTHORIZED,\
                                            HTTP_200_OK
from src.database import db
from src.models import User

auth = Blueprint("auth", __name__, url_prefix='/api/v1/auth')


@auth.post('/register')
@swag_from('docs/auth/register.yml')
def register():
    """Register user"""
    username = request.json['username']
    email = request.json['email']
    password = request.json['password']
    # Validate data
    if len(password) < 6:
        return jsonify({"error": "Password is too short"}), HTTP_400_BAD_REQUEST
    if not username.isalnum() or " " in username:
        return jsonify({"error": "Username should be alphanumeric and no spaces"}), HTTP_400_BAD_REQUEST
    if not validators.email(email):
        return jsonify({"error": "Email is not valid"}), HTTP_400_BAD_REQUEST

    if User.query.filter_by(email=email).first() is not None:
        return jsonify({"error": "Email already exists."}), HTTP_409_CONFLICT
    if User.query.filter_by(username=username).first() is not None:
        return jsonify({"error": "Username already exists."}), HTTP_409_CONFLICT
    # Hash the given password
    pwd_hash = generate_password_hash(password)
    user = User(username=username, password=pwd_hash, email=email)
    # Save user in db
    db.session.add(user)
    db.session.commit()
    return jsonify({"message": "User created",
                    "user": {
                        "username": username,
                        "email": email
                    }}), HTTP_201_CREATED


@auth.post('/login')
@swag_from('docs/auth/login.yml')
def login():
    """Authorize user"""
    email = request.json.get('email', '')
    password = request.json.get('password', '')
    # Get user if exists
    user = User.query.filter_by(email=email).first_or_404()
    # Check password
    if user:
        is_pass_correct = check_password_hash(user.password, password)

        if is_pass_correct:
            # Create tokens
            refresh = create_refresh_token(identity=user.id)
            access = create_access_token(identity=user.id)

            return jsonify({
                'refresh': refresh,
                'access': access,
                'user': {
                    'username': user.username,
                    'email': user.email
                }
            }), HTTP_200_OK
    return jsonify({'error': 'Wrong credentials'}), HTTP_401_UNAUTHORIZED


@auth.get('/me')
@jwt_required()
@swag_from('docs/auth/me.yml')
def me():
    """Return user's info"""
    # Get user if exists
    user = get_jwt_identity()
    user = User.query.filter_by(id=user.id).first_or_404()
    return jsonify({
        "user": {
            "username": user.username,
            "email": user.email
        }
    }), HTTP_200_OK


@auth.get('/token/refresh')
@jwt_required(refresh=True)
def refresh_users_token():
    """Refresh token endpoint"""
    identity = get_jwt_identity()
    access = create_access_token(identity=identity)

    return jsonify({
        "access": access
    }), HTTP_200_OK
