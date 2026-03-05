"""Keyword management API controller with authentication and input validation."""
import logging
from flask import Blueprint, request, jsonify
from api.keyword_management.keyword_service import KeywordService
from backend.auth import login_required
from backend.validators import KeywordSchema, KeywordUpdateSchema
from marshmallow import ValidationError

logger = logging.getLogger(__name__)

keyword_blueprint = Blueprint('keywords', __name__)
keyword_service = KeywordService()

keyword_schema = KeywordSchema()
keyword_update_schema = KeywordUpdateSchema()


@keyword_blueprint.route('/get_keywords', methods=['GET'])
@login_required
def get_keywords():
    try:
        keywords = keyword_service.get_all_keywords()
        return jsonify([
            {
                "id": k.id,
                "keyword": k.keyword,
                "added_by": k.added_by if k.added_by is not None else "N/A"
            } for k in keywords
        ]), 200
    except Exception as e:
        logger.exception("Error fetching keywords")
        return jsonify({"success": False, "error": "Failed to fetch keywords"}), 500


@keyword_blueprint.route('/add_keyword', methods=['POST'])
@login_required
def add_keyword():
    try:
        if request.content_type != 'application/json':
            return jsonify({"success": False, "error": "Content-Type must be application/json"}), 415

        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Request body required"}), 400

        # Validate input with marshmallow
        try:
            validated = keyword_schema.load(data)
        except ValidationError as err:
            return jsonify({"success": False, "error": err.messages}), 400

        response = keyword_service.add_keyword(validated['keyword'])
        return jsonify(response), 201 if response.get('success') else 400
    except Exception as e:
        logger.exception("Error adding keyword")
        return jsonify({"success": False, "error": "Failed to add keyword"}), 500


@keyword_blueprint.route('/update_keyword/<int:keyword_id>', methods=['PUT'])
@login_required
def update_keyword(keyword_id):
    try:
        if request.content_type != 'application/json':
            return jsonify({"success": False, "error": "Content-Type must be application/json"}), 415

        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Request body required"}), 400

        try:
            validated = keyword_update_schema.load(data)
        except ValidationError as err:
            return jsonify({"success": False, "error": err.messages}), 400

        response = keyword_service.update_keyword(keyword_id, validated['new_name'])
        return jsonify(response), 200 if response.get('success') else 400
    except Exception as e:
        logger.exception("Error updating keyword %s", keyword_id)
        return jsonify({"success": False, "error": "Failed to update keyword"}), 500


@keyword_blueprint.route('/delete_keyword/<int:keyword_id>', methods=['DELETE'])
@login_required
def delete_keyword(keyword_id):
    try:
        response = keyword_service.delete_keyword(keyword_id)
        return jsonify(response), 200 if response.get('success') else 400
    except Exception as e:
        logger.exception("Error deleting keyword %s", keyword_id)
        return jsonify({"success": False, "error": "Failed to delete keyword"}), 500
