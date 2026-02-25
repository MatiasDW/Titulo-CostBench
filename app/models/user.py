"""User model for authentication, risk profile, and onboarding preferences."""
import bcrypt
from datetime import datetime
from sqlalchemy.dialects.postgresql import ARRAY
from app.extensiones import db


VALID_RISK_PROFILES = ("conservative", "moderate", "aggressive")
VALID_ROLES = ("admin", "user")


class User(db.Model):
    """User account with hashed password and optional risk profile."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="user")
    risk_profile = db.Column(db.String(20), nullable=True)
    interests = db.Column(ARRAY(db.Text), nullable=False, default=list)
    onboarding_completed = db.Column(db.Boolean, nullable=False, default=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    # ------------------------------------------------------------------
    # Password helpers
    # ------------------------------------------------------------------

    def set_password(self, plain: str) -> None:
        """Hash *plain* with bcrypt and store in password_hash."""
        self.password_hash = bcrypt.hashpw(
            plain.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

    def check_password(self, plain: str) -> bool:
        """Return True if *plain* matches the stored hash."""
        return bcrypt.checkpw(
            plain.encode("utf-8"), self.password_hash.encode("utf-8")
        )

    @property
    def is_admin(self) -> bool:
        """Return True if user has admin role."""
        return self.role == "admin"

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        """Safe representation – never includes the password hash."""
        return {
            "id": self.id,
            "email": self.email,
            "role": self.role,
            "is_admin": self.is_admin,
            "risk_profile": self.risk_profile,
            "interests": self.interests or [],
            "onboarding_completed": self.onboarding_completed,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email}>"
