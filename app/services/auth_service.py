"""
Authentication service – business logic layer.

Responsibilities:
  • User registration and credential validation
  • JWT token generation / verification
  • Anti-enumeration: login errors never reveal whether the email exists
"""
import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional

from flask import current_app
from sqlalchemy.exc import IntegrityError

from app.extensiones import db
from app.models.user import User, VALID_RISK_PROFILES
from app.ml.logging_utils import get_logger

logger = get_logger("auth.service")


# ------------------------------------------------------------------
# Registration
# ------------------------------------------------------------------

def register_user(email: str, password: str, risk_profile: str = None) -> tuple[dict, int]:
    """
    Create a new user.

    Returns:
        (response_body, http_status)
    """
    email = email.strip().lower()

    # Basic validation
    if not email or not password:
        return {"error": "Email y contraseña son requeridos."}, 400

    if len(password) < 8:
        return {"error": "La contraseña debe tener al menos 8 caracteres."}, 400

    # Validate risk_profile if provided
    if risk_profile and risk_profile not in VALID_RISK_PROFILES:
        return {
            "error": f"Perfil inválido.  Opciones: {', '.join(VALID_RISK_PROFILES)}"
        }, 400

    try:
        user = User(email=email)
        user.set_password(password)

        if risk_profile:
            user.risk_profile = risk_profile

        db.session.add(user)
        db.session.commit()

        logger.info("user_registered", user_id=user.id, email=email)

        return {"user": user.to_dict()}, 201

    except IntegrityError:
        db.session.rollback()
        logger.warning("registration_duplicate_email", email=email)
        return {"error": "Este correo ya está registrado."}, 409

    except Exception:
        db.session.rollback()
        logger.error("registration_failed", exc_info=True)
        return {"error": "Error interno del servidor."}, 500


# ------------------------------------------------------------------
# Authentication
# ------------------------------------------------------------------

def authenticate_user(email: str, password: str) -> tuple[dict, int]:
    """
    Validate credentials.  Returns the same generic error message
    regardless of whether the email exists (anti-enumeration).

    Returns:
        (response_body, http_status)
    """
    INVALID_MSG = "Credenciales incorrectas."

    if not email or not password:
        return {"error": INVALID_MSG}, 401

    try:
        user = User.query.filter_by(email=email.strip().lower()).first()

        if user is None or not user.check_password(password):
            logger.info("login_failed", email=email)
            return {"error": INVALID_MSG}, 401

        if not user.is_active:
            logger.info("login_inactive_account", user_id=user.id)
            return {"error": INVALID_MSG}, 401

        logger.info("login_success", user_id=user.id)
        return {"user": user.to_dict()}, 200

    except Exception:
        logger.error("authentication_error", exc_info=True)
        return {"error": "Error interno del servidor."}, 500


# ------------------------------------------------------------------
# JWT helpers
# ------------------------------------------------------------------

def _get_jwt_key() -> str:
    """
    Return a signing key that satisfies PyJWT ≥2.9 minimum length (32 bytes).
    Pads the configured SECRET_KEY if it's too short.
    """
    key = current_app.config["SECRET_KEY"]
    if len(key.encode()) < 32:
        key = key.ljust(32, '0')  # pad to 32 bytes
    return key


def generate_token(user_id: int) -> str:
    """Create a signed JWT for *user_id*."""
    expiry_hours = current_app.config.get("JWT_EXPIRY_HOURS", 24)
    payload = {
        "sub": str(user_id),  # PyJWT ≥2.11 requires 'sub' to be a string
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=expiry_hours),
    }
    return jwt.encode(payload, _get_jwt_key(), algorithm="HS256")


def decode_token(token: str) -> Optional[dict]:
    """
    Decode and validate a JWT.

    Returns:
        The payload dict on success, or None on any failure.
    """
    try:
        return jwt.decode(
            token, _get_jwt_key(), algorithms=["HS256"]
        )
    except jwt.ExpiredSignatureError:
        logger.info("token_expired")
        return None
    except jwt.InvalidTokenError:
        logger.warning("token_invalid")
        return None


# ------------------------------------------------------------------
# Profile update
# ------------------------------------------------------------------

def update_risk_profile(user_id: int, risk_profile: str) -> tuple[dict, int]:
    """
    Set the user's risk profile.

    Returns:
        (response_body, http_status)
    """
    if risk_profile not in VALID_RISK_PROFILES:
        return {
            "error": f"Perfil inválido.  Opciones: {', '.join(VALID_RISK_PROFILES)}"
        }, 400

    try:
        user = db.session.get(User, user_id)

        if user is None:
            return {"error": "Usuario no encontrado."}, 404

        user.risk_profile = risk_profile
        db.session.commit()

        logger.info("profile_updated", user_id=user_id, profile=risk_profile)

        return {"user": user.to_dict()}, 200

    except Exception:
        db.session.rollback()
        logger.error("profile_update_failed", exc_info=True)
        return {"error": "Error interno del servidor."}, 500
