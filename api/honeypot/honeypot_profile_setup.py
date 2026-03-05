"""Honeypot profile management with password hashing, auth, and input validation."""
import logging
import bcrypt
from flask import Blueprint, jsonify, request
from backend.auth import admin_required
from backend.validators import HoneypotProfileSchema
from marshmallow import ValidationError

logger = logging.getLogger(__name__)
honeypot_schema = HoneypotProfileSchema()


def _hash_password(plain_password: str) -> str:
    """Hash a password with bcrypt. Never store plaintext passwords."""
    return bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


class HoneypotProfileSetup:
    def __init__(self):
        self.honeypot_profiles = {}
        self._next_id = 1

    def create_profile(self, platform, username, password, email):
        try:
            # Check for duplicate
            for pid, profile in self.honeypot_profiles.items():
                if profile["platform"] == platform and profile["username"] == username:
                    return {"status": "error", "message": "Profile already exists for this platform/username"}

            profile_id = self._next_id
            self._next_id += 1
            profile_data = {
                "platform": platform,
                "username": username,
                "password_hash": _hash_password(password),  # NEVER store plaintext
                "email": email,
            }
            self.honeypot_profiles[profile_id] = profile_data
            logger.info("Honeypot profile created: %s on %s", username, platform)
            return {"status": "success", "message": f"Honeypot profile for {platform} created", "profile_id": profile_id}
        except Exception as e:
            logger.exception("Error creating honeypot profile")
            return {"status": "error", "message": "Failed to create profile"}

    def view_all_profiles(self):
        try:
            # NEVER return password hashes in API responses
            profiles = []
            for pid, data in self.honeypot_profiles.items():
                profiles.append({
                    "id": pid,
                    "platform": data.get("platform", ""),
                    "username": data.get("username", ""),
                    "email": data.get("email", ""),
                })
            return profiles
        except Exception as e:
            logger.exception("Error viewing profiles")
            return []

    def update_profile(self, profile_id, updates):
        try:
            if profile_id not in self.honeypot_profiles:
                return {"status": "error", "message": "Profile not found"}
            # If updating password, hash it
            if "password" in updates:
                updates["password_hash"] = _hash_password(updates.pop("password"))
            # Never allow direct password_hash injection
            updates.pop("password_hash", None) if "password" not in updates else None
            self.honeypot_profiles[profile_id].update(updates)
            logger.info("Honeypot profile %s updated", profile_id)
            return {"status": "success", "message": "Profile updated"}
        except Exception as e:
            logger.exception("Error updating profile %s", profile_id)
            return {"status": "error", "message": "Failed to update profile"}

    def delete_profile(self, profile_id):
        try:
            if profile_id not in self.honeypot_profiles:
                return {"status": "error", "message": "Profile not found"}
            del self.honeypot_profiles[profile_id]
            logger.info("Honeypot profile %s deleted", profile_id)
            return {"status": "success", "message": "Profile deleted"}
        except Exception as e:
            logger.exception("Error deleting profile %s", profile_id)
            return {"status": "error", "message": "Failed to delete profile"}


# Initialize the manager
honeypot_manager = HoneypotProfileSetup()

# Define the Blueprint
honeypot_blueprint = Blueprint('honeypot', __name__)


@honeypot_blueprint.route('/view_honeypot_profiles', methods=['GET'])
@admin_required
def view_honeypot_profiles():
    profiles = honeypot_manager.view_all_profiles()
    return jsonify(profiles)


@honeypot_blueprint.route('/create_honeypot_profile', methods=['POST'])
@admin_required
def create_honeypot_profile():
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "JSON body required"}), 400

    # Validate with marshmallow
    try:
        validated = honeypot_schema.load(data)
    except ValidationError as err:
        return jsonify({"status": "error", "message": err.messages}), 400

    result = honeypot_manager.create_profile(
        validated["platform"],
        validated["username"],
        validated["password"],
        validated["email"],
    )
    status_code = 201 if result.get("status") == "success" else 400
    return jsonify(result), status_code


@honeypot_blueprint.route('/update_honeypot_profile', methods=['PUT'])
@admin_required
def update_honeypot_profile():
    data = request.json
    profile_id = data.get('profile_id') if data else None
    updates = data.get('updates', {}) if data else {}

    if not profile_id or not updates:
        return jsonify({"status": "error", "message": "Profile ID and updates are required"}), 400

    result = honeypot_manager.update_profile(profile_id, updates)
    return jsonify(result)


@honeypot_blueprint.route('/delete_honeypot_profile', methods=['DELETE'])
@admin_required
def delete_honeypot_profile():
    data = request.json
    profile_id = data.get('profile_id') if data else None

    if not profile_id:
        return jsonify({"status": "error", "message": "Profile ID is required"}), 400

    result = honeypot_manager.delete_profile(profile_id)
    return jsonify(result)
