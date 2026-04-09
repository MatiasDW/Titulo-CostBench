"""User model for authentication, risk profile, KYC, and onboarding preferences."""

import bcrypt
from datetime import datetime, date
from sqlalchemy.dialects.postgresql import ARRAY
from app.extensiones import db

VALID_RISK_PROFILES = ("conservative", "moderate", "aggressive")
VALID_ROLES = ("admin", "user")
VALID_EXPERIENCE = ("beginner", "intermediate", "advanced")
VALID_INCOME = ("0-1M", "1M-3M", "3M-5M", "5M-10M", "10M+")


class User(db.Model):
    """User account with hashed password and optional risk profile."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="user")
    first_name = db.Column(db.String(100), nullable=True)
    last_name = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(30), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    # KYC fields
    rut = db.Column(db.String(12), nullable=True, unique=True)
    date_of_birth = db.Column(db.Date, nullable=True)
    nationality = db.Column(db.String(60), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    city = db.Column(db.String(80), nullable=True)
    occupation = db.Column(db.String(100), nullable=True)
    income_range = db.Column(db.String(40), nullable=True)
    investment_experience = db.Column(db.String(20), nullable=True)
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
        return bcrypt.checkpw(plain.encode("utf-8"), self.password_hash.encode("utf-8"))

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
            "first_name": self.first_name,
            "last_name": self.last_name,
            "phone": self.phone,
            "bio": self.bio,
            "rut": self.rut,
            "date_of_birth": (
                self.date_of_birth.isoformat() if self.date_of_birth else None
            ),
            "nationality": self.nationality,
            "address": self.address,
            "city": self.city,
            "occupation": self.occupation,
            "income_range": self.income_range,
            "investment_experience": self.investment_experience,
            "risk_profile": self.risk_profile,
            "interests": self.interests or [],
            "onboarding_completed": self.onboarding_completed,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email}>"
