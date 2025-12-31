import random
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.user import VerificationCode
from app.config import settings


def generate_verification_code() -> str:
    """Generate a 6-digit verification code"""
    return str(random.randint(100000, 999999))


def send_verification_code(phone_number: str, db: Session) -> tuple[str, int]:
    """
    Send verification code to phone number
    Returns: (code, expires_in_seconds)
    """
    if settings.sms_mock_mode:
        # Mock mode: return fixed code for development
        code = settings.sms_mock_code
    else:
        # Real SMS service integration would go here
        code = generate_verification_code()
        # TODO: Integrate with real SMS service (Aliyun SMS, Tencent SMS, etc.)
    
    # Save verification code to database
    expires_at = datetime.utcnow() + timedelta(minutes=5)
    verification_code = VerificationCode(
        phone_number=phone_number,
        code=code,
        expires_at=expires_at
    )
    db.add(verification_code)
    db.commit()
    
    expires_in = int((expires_at - datetime.utcnow()).total_seconds())
    return code, expires_in


def verify_code(phone_number: str, code: str, db: Session) -> bool:
    """
    Verify the code for phone number
    """
    verification = db.query(VerificationCode).filter(
        VerificationCode.phone_number == phone_number,
        VerificationCode.code == code,
        VerificationCode.used == False,
        VerificationCode.expires_at > datetime.utcnow()
    ).first()
    
    if verification:
        verification.used = True
        db.commit()
        return True
    
    return False

