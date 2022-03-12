"""Application implementing bookmarks' processes"""

from flask import Blueprint, request, jsonify
import validators
from flask_jwt_extended import get_jwt_identity, jwt_required
from flasgger import swag_from

from src.constants.http_status_codes import HTTP_400_BAD_REQUEST, \
                                            HTTP_409_CONFLICT, \
                                            HTTP_201_CREATED, \
                                            HTTP_200_OK, \
                                            HTTP_404_NOT_FOUND
from src.database import db
from src.models import Bookmark

bookmarks = Blueprint("bookmarks", __name__, url_prefix='/api/v1/bookmarks')


@bookmarks.route('/', methods=['POST', 'GET'])
@jwt_required()
@swag_from('docs/bookmarks/handle_bookmarks.yml')
def handle_bookmarks():
    """Return all the user's bookmarks or create on if POST"""
    # Get user
    current_user = get_jwt_identity()

    if request.method == 'POST':
        # Get data of bookmark
        body = request.get_json().get('body', '')
        url = request.get_json().get('url', '')
        # Validate url
        if not validators.url(url):
            return jsonify({
                'error': 'Enter a valid url'
            }), HTTP_400_BAD_REQUEST
        # Check whether bookmark is unique
        if Bookmark.query.filter_by(url=url).first():
            return jsonify({
                'error': 'URL already exists'
            }), HTTP_409_CONFLICT
        # Create bookmark
        bookmark = Bookmark(url=url, body=body, user_id=current_user)
        db.session.add(bookmark)
        db.session.commit()

        return jsonify({"id": bookmark.id,
                        'url': bookmark.url,
                        'short_url': bookmark.short_url,
                        'visits': bookmark.visits,
                        'body': bookmark.body,
                        'created_at': bookmark.created_at,
                        'updated_at': bookmark.updated_at
                        }), HTTP_201_CREATED
    else:
        # Paginate bookmarks
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 5, type=int)

        users_bookmarks = Bookmark.query.filter_by(user_id=current_user).paginate(page=page, per_page=per_page)
        data = []
        # Find and return all the user's bookmarks
        for bookmark in users_bookmarks.items:
            data.append({"id": bookmark.id,
                         'url': bookmark.url,
                         'short_url': bookmark.short_url,
                         'visits': bookmark.visits,
                         'body': bookmark.body,
                         'created_at': bookmark.created_at,
                         'updated_at': bookmark.updated_at})
        # Return meta info about pagination
        meta = {
            'page': users_bookmarks.page,
            'pages': users_bookmarks.pages,
            'total_count': users_bookmarks.total,
            'prev': users_bookmarks.prev_num,
            'next': users_bookmarks.next_num,
            'has_next': users_bookmarks.has_next,
            'has_prev': users_bookmarks.has_prev,
        }
        return jsonify({'data': data, 'meta': meta}), HTTP_200_OK


@bookmarks.get('/<int:id>')
@jwt_required()
@swag_from('docs/bookmarks/get_bookmark.yml')
def get_bookmark(id):
    """Return specific bookmark by id"""
    current_user = get_jwt_identity()
    # Find a bookmark and return if exists else 404
    bookmark = Bookmark.query.filter_by(user_id=current_user, id=id).first_or_404()

    if not bookmark:
        return jsonify({'message': 'Item not found'}), HTTP_404_NOT_FOUND

    return jsonify({"id": bookmark.id,
                    'url': bookmark.url,
                    'short_url': bookmark.short_url,
                    'visits': bookmark.visits,
                    'body': bookmark.body,
                    'created_at': bookmark.created_at,
                    'updated_at': bookmark.updated_at}), HTTP_200_OK


@bookmarks.put('/<int:id>')
@bookmarks.patch('/<int:id>')
@jwt_required()
@swag_from('docs/bookmarks/edit_bookmark.yml')
def edit_bookmark(id):
    """Update a specific bookmark by id"""
    current_user = get_jwt_identity()
    # Find bookmark and update if exists else 404
    bookmark = Bookmark.query.filter_by(user_id=current_user, id=id).first_or_404()

    if not bookmark:
        return jsonify({'message': 'Item not found'}), HTTP_404_NOT_FOUND
    # Get data to update
    body = request.get_json().get('body', '')
    url = request.get_json().get('url', '')
    # Validate url
    if not validators.url(url):
        return jsonify({
            'error': 'Enter a valid url'
        }), HTTP_400_BAD_REQUEST
    # Save updates
    bookmark.url = url
    bookmark.body = body
    db.session.commit()
    return jsonify({"id": bookmark.id,
                    'url': bookmark.url,
                    'short_url': bookmark.short_url,
                    'visits': bookmark.visits,
                    'body': bookmark.body,
                    'created_at': bookmark.created_at,
                    'updated_at': bookmark.updated_at}), HTTP_200_OK


@bookmarks.delete('/<int:id>')
@jwt_required()
@swag_from('docs/bookmarks/delete_bookmark.yml')
def delete_bookmark(id):
    """Delete a specific bookmark"""
    current_user = get_jwt_identity()
    # Delete bookmark if exists else 404
    bookmark = Bookmark.query.filter_by(user_id=current_user, id=id).first_or_404()

    if not bookmark:
        return jsonify({'message': 'Item not found'}), HTTP_404_NOT_FOUND
    # Delete bookmark and save db
    db.session.delete(bookmark)
    db.session.commit()
    return jsonify({'message': "Bookmark was deleted"}), HTTP_200_OK


@bookmarks.get('/stats')
@jwt_required()
@swag_from('docs/bookmarks/stats.yml')
def get_stats():
    """Return statistics about URL visits."""
    current_user = get_jwt_identity()
    data = []
    # Get all the user's bookmarks and save statistics into the list
    items = Bookmark.query.filter_by(user_id=current_user).all()
    for item in items:
        new_link = {
            'visits': item.visits,
            'url': item.url,
            'id': item.id,
            'short_url': item.short_url
        }
        data.append(new_link)
    return jsonify({'data': data}), HTTP_200_OK
