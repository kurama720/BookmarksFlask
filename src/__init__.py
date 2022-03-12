"""Module to run server"""

import os

from flask import Flask, redirect, jsonify
from flask_jwt_extended import JWTManager
from flasgger import Swagger, swag_from

from src.auth import auth
from src.bookmarks import bookmarks
from src.database import db
from src.models import Bookmark
from src.constants.http_status_codes import HTTP_500_INTERNAL_SERVER_ERROR
from src.config.swagger import template, swagger_config


def create_app(test_config=None):
    """Project configuration"""
    app = Flask(__name__, instance_relative_config=True)
    # Get constants for configuration
    if test_config is None:
        app.config.from_mapping(
            SECRET_KEY=os.environ.get('SECRET_KEY'),
            SQLALCHEMY_DATABASE_URI=os.environ.get('SQLALCHEMY_DATABASE_URI'),
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
            JWT_SECRET_KEY=os.environ.get('JWT_SECRET_KEY'),
            SWAGGER={
                'title': 'Bookmarks API',
                'uiversion': 3,
            }
        )
    else:
        app.config.from_mapping(test_config)
    # Configurate db
    db.app = app
    db.init_app(app)
    # Configurate JWT
    JWTManager(app)
    # Register applications
    app.register_blueprint(auth)
    app.register_blueprint(bookmarks)
    # Configure Swagger
    Swagger(app, config=swagger_config, template=template)

    @app.get('/<short_url>')
    @swag_from('docs/short_url.yml')
    def redirect_to_url(short_url):
        """Redirect to real bookmark URL, increase visits field."""
        bookmark = Bookmark.query.filter_by(short_url=short_url).first_or_404()
        if bookmark:
            bookmark.visits = bookmark.visits + 1
            db.session.commit()

            return redirect(bookmark.url)

    @app.errorhandler(HTTP_500_INTERNAL_SERVER_ERROR)
    def handler_500(e):
        """Handle server error"""
        return jsonify({'error': 'Something went wrong, we are working on it'}), HTTP_500_INTERNAL_SERVER_ERROR

    return app



