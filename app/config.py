from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Environment
    environment: str = "development"
    debug: bool = True
    api_v1_prefix: str = "/v1"

    # Database
    database_url: str = "mysql+pymysql://user:password@localhost:3306/lumina_db"

    # JWT
    jwt_secret_key: str = "your-secret-key-here-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 120
    jwt_refresh_token_expire_days: int = 30

    # OSS Configuration
    oss_access_key_id: str = ""
    oss_access_key_secret: str = ""
    oss_bucket_name: str = "lumina-images"
    oss_endpoint: str = "oss-cn-hangzhou.aliyuncs.com"
    oss_region: str = "cn-hangzhou"

    # SMS Configuration
    sms_mock_mode: bool = True
    sms_mock_code: str = "123456"

    # WeChat Configuration
    wechat_app_id: Optional[str] = None
    wechat_app_secret: Optional[str] = None
    wechat_mock_mode: bool = True

    # Payment Configuration
    payment_mock_mode: bool = True
    wechat_pay_app_id: Optional[str] = None
    wechat_pay_mch_id: Optional[str] = None
    wechat_pay_api_key: Optional[str] = None
    alipay_app_id: Optional[str] = None
    alipay_private_key: Optional[str] = None
    alipay_public_key: Optional[str] = None

    # AI Processing Service
    ai_service_url: Optional[str] = None
    ai_service_api_key: Optional[str] = None
    ai_service_mock_mode: bool = False

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_password: Optional[str] = None
    redis_enabled: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

