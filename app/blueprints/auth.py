"""
Auth Blueprint – /api/v1/auth

Endpoints:
  POST /register   – create account
  POST /login      – authenticate and set JWT cookie
  POST /logout     – clear JWT cookie
  GET  /me         – return current user from cookie
  PUT  /profile    – update risk_profile
"""

from functools import wraps

from flask import Blueprint, g, jsonify, request, make_response, current_app
from sqlalchemy.orm import joinedload, selectinload

from app.extensiones import db
from app.models.user import User, VALID_ROLES
from app.services.auth_service import (
    register_user,
    authenticate_user,
    generate_token,
    decode_token,
    update_risk_profile,
)
from app.ml.logging_utils import get_logger

logger = get_logger("auth.api")

auth_bp = Blueprint("auth", __name__, url_prefix="/api/v1/auth")

# Cookie name
TOKEN_COOKIE = "access_token"


# ------------------------------------------------------------------
# Decorator: require_auth
# ------------------------------------------------------------------


def require_auth(fn):
    """Extract JWT from HttpOnly cookie and inject ``g.current_user``."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        token = request.cookies.get(TOKEN_COOKIE)

        if not token:
            return jsonify({"error": "Autenticación requerida."}), 401

        payload = decode_token(token)
        if payload is None:
            return jsonify({"error": "Sesión expirada o inválida."}), 401

        user = User.query.get(int(payload["sub"]))
        if user is None or not user.is_active:
            return jsonify({"error": "Usuario no encontrado."}), 401

        g.current_user = user
        return fn(*args, **kwargs)

    return wrapper


# ------------------------------------------------------------------
# Decorator: require_admin (must be used AFTER require_auth)
# ------------------------------------------------------------------


def require_admin(fn):
    """Reject non-admin users with 403."""

    @wraps(fn)
    @require_auth
    def wrapper(*args, **kwargs):
        if not g.current_user.is_admin:
            return jsonify({"error": "Acceso restringido a administradores."}), 403
        return fn(*args, **kwargs)

    return wrapper


# ------------------------------------------------------------------
# Helper: set JWT cookie on response
# ------------------------------------------------------------------


def _set_token_cookie(response, user_id: int):
    """Attach an HttpOnly JWT cookie to *response*."""
    token = generate_token(user_id)
    is_prod = current_app.config.get("FLASK_ENV") == "production"
    expiry_hours = current_app.config.get("JWT_EXPIRY_HOURS", 24)

    response.set_cookie(
        TOKEN_COOKIE,
        value=token,
        httponly=True,
        secure=is_prod,
        samesite="Lax",
        max_age=expiry_hours * 3600,
        path="/",
    )
    return response


def _serialize_admin_user(user: User) -> dict:
    """Extended user payload for admin operations."""
    wallet = getattr(user, "wallet", None)
    return {
        **user.to_dict(),
        "has_wallet": wallet is not None,
        "wallet_balance": float(wallet.balance) if wallet is not None else None,
        "trace_count": len(getattr(user, "scloda_traces", []) or []),
        "review_count": len(getattr(user, "scloda_review_items", []) or []),
        "assigned_review_count": len(getattr(user, "assigned_scloda_reviews", []) or []),
    }


# ------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------


@auth_bp.route("/register", methods=["POST"])
def register():
    """POST /api/v1/auth/register"""
    data = request.get_json(silent=True) or {}
    body, status = register_user(
        data.get("email", ""),
        data.get("password", ""),
        data.get("risk_profile"),
    )

    response = make_response(jsonify(body), status)

    # Set cookie on successful registration
    if status == 201:
        _set_token_cookie(response, body["user"]["id"])

    return response


@auth_bp.route("/login", methods=["POST"])
def login():
    """POST /api/v1/auth/login"""
    data = request.get_json(silent=True) or {}
    body, status = authenticate_user(data.get("email", ""), data.get("password", ""))

    response = make_response(jsonify(body), status)

    if status == 200:
        _set_token_cookie(response, body["user"]["id"])

    return response


@auth_bp.route("/logout", methods=["POST"])
def logout():
    """POST /api/v1/auth/logout – clear the JWT cookie."""
    response = make_response(jsonify({"message": "Sesión cerrada."}), 200)
    response.delete_cookie(TOKEN_COOKIE, path="/")
    return response


@auth_bp.route("/me", methods=["GET"])
@require_auth
def me():
    """GET /api/v1/auth/me – return current user data."""
    return jsonify({"user": g.current_user.to_dict()})


@auth_bp.route("/admin/users", methods=["GET"])
@require_admin
def admin_users():
    """GET /api/v1/auth/admin/users – list accounts and admin-facing counts."""
    users = (
        User.query.options(
            joinedload(User.wallet),
            selectinload(User.scloda_traces),
            selectinload(User.scloda_review_items),
            selectinload(User.assigned_scloda_reviews),
        )
        .order_by(User.created_at.desc())
        .all()
    )

    payload = [_serialize_admin_user(user) for user in users]
    summary = {
        "total_users": len(payload),
        "active_users": sum(1 for user in payload if user["is_active"]),
        "admin_users": sum(1 for user in payload if user["is_admin"]),
        "onboarded_users": sum(1 for user in payload if user["onboarding_completed"]),
        "wallet_users": sum(1 for user in payload if user["has_wallet"]),
    }
    return jsonify({"users": payload, "summary": summary})


@auth_bp.route("/admin/users/<int:user_id>", methods=["PATCH"])
@require_admin
def admin_update_user(user_id: int):
    """PATCH /api/v1/auth/admin/users/<id> – toggle role/active state for operators."""
    target = db.session.get(User, user_id)
    if target is None:
        return jsonify({"error": "Usuario no encontrado."}), 404

    data = request.get_json(silent=True) or {}

    next_role = data.get("role", target.role)
    next_active = data.get("is_active", target.is_active)

    if next_role not in VALID_ROLES:
        return jsonify({"error": "Rol inválido."}), 400

    if target.id == g.current_user.id and next_role != "admin":
        return jsonify({"error": "No puedes quitarte permisos de admin a ti mismo."}), 400

    if target.id == g.current_user.id and not bool(next_active):
        return jsonify({"error": "No puedes desactivar tu propia cuenta."}), 400

    if target.role == "admin" and next_role != "admin":
        remaining_admins = User.query.filter(
            User.role == "admin",
            User.id != target.id,
            User.is_active.is_(True),
        ).count()
        if remaining_admins == 0:
            return jsonify({"error": "Debe existir al menos un admin activo."}), 400

    if target.role == "admin" and target.is_active and not bool(next_active):
        remaining_admins = User.query.filter(
            User.role == "admin",
            User.id != target.id,
            User.is_active.is_(True),
        ).count()
        if remaining_admins == 0:
            return jsonify({"error": "Debe existir al menos un admin activo."}), 400

    target.role = next_role
    target.is_active = bool(next_active)
    db.session.commit()

    refreshed = (
        User.query.options(
            joinedload(User.wallet),
            selectinload(User.scloda_traces),
            selectinload(User.scloda_review_items),
            selectinload(User.assigned_scloda_reviews),
        )
        .filter(User.id == target.id)
        .first()
    )
    return jsonify({"user": _serialize_admin_user(refreshed)})


@auth_bp.route("/profile", methods=["PUT"])
@require_auth
def profile():
    """PUT /api/v1/auth/profile – update user profile (personal info + preferences)."""
    from app.extensiones import db
    from app.models.user import VALID_RISK_PROFILES

    data = request.get_json(silent=True) or {}
    user = g.current_user

    # Personal info + KYC fields (all optional, trimmed strings)
    STRING_FIELDS = (
        "first_name",
        "last_name",
        "phone",
        "bio",
        "rut",
        "nationality",
        "address",
        "city",
        "occupation",
        "income_range",
        "investment_experience",
    )
    for field in STRING_FIELDS:
        if field in data:
            val = (data[field] or "").strip() or None
            setattr(user, field, val)

    # Date of birth (special handling)
    if "date_of_birth" in data:
        dob = data["date_of_birth"]
        if dob:
            try:
                from datetime import date

                user.date_of_birth = date.fromisoformat(dob)
            except (ValueError, TypeError):
                return (
                    jsonify({"error": "Invalid date_of_birth format. Use YYYY-MM-DD."}),
                    400,
                )
        else:
            user.date_of_birth = None

    # Risk profile (optional, validated)
    risk = data.get("risk_profile")
    if risk is not None:
        if risk and risk not in VALID_RISK_PROFILES:
            return (
                jsonify(
                    {
                        "error": f"Invalid risk profile. Options: {', '.join(VALID_RISK_PROFILES)}"
                    }
                ),
                400,
            )
        user.risk_profile = risk or None

    # Interests (optional, must be list)
    if "interests" in data:
        interests = data["interests"]
        if not isinstance(interests, list):
            return jsonify({"error": "Interests must be a list."}), 400
        user.interests = interests

    try:
        db.session.commit()
        logger.info("profile_updated", user_id=user.id)
        return jsonify({"user": user.to_dict()}), 200
    except Exception:
        db.session.rollback()
        logger.error("profile_update_failed", exc_info=True)
        return jsonify({"error": "Internal server error."}), 500


@auth_bp.route("/onboarding", methods=["PUT"])
@require_auth
def onboarding():
    """PUT /api/v1/auth/onboarding – save preferences and mark onboarding done."""
    from app.extensiones import db
    from app.models.user import VALID_RISK_PROFILES

    data = request.get_json(silent=True) or {}

    risk_profile = data.get("risk_profile")
    interests = data.get("interests", [])

    # Validate
    if risk_profile and risk_profile not in VALID_RISK_PROFILES:
        return jsonify({"error": "Invalid risk profile."}), 400

    if not isinstance(interests, list):
        return jsonify({"error": "Interests must be a list."}), 400

    try:
        user = g.current_user
        if risk_profile:
            user.risk_profile = risk_profile
        user.interests = interests
        user.onboarding_completed = True
        db.session.commit()

        logger.info("onboarding_completed", user_id=user.id)
        return jsonify({"user": user.to_dict()}), 200

    except Exception:
        db.session.rollback()
        logger.error("onboarding_failed", exc_info=True)
        return jsonify({"error": "Internal server error."}), 500
