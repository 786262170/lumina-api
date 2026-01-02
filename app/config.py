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

    # Domain Configuration
    api_domain: Optional[str] = None  # API domain, e.g., api.lumina.ai
    static_domain: Optional[str] = None  # Static files domain, e.g., static.lumina.ai
    base_url: str = "http://localhost:8000"  # Base URL for local file access (used in mock mode)
    
    # OSS Configuration
    oss_access_key_id: str = ""
    oss_access_key_secret: str = ""
    oss_bucket_name: str = "lumina-images"
    oss_endpoint: str = "oss-cn-hangzhou.aliyuncs.com"
    oss_region: str = "cn-hangzhou"
    oss_mock_mode: bool = True  # If True, save files to local filesystem instead of OSS
    oss_local_storage_path: str = "uploads"  # Local storage directory for mock mode

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

    # AI Processing Service (Legacy - for external services)
    ai_service_url: Optional[str] = None
    ai_service_api_key: Optional[str] = None
    ai_service_mock_mode: bool = False
    
    # 阿里云视觉智能开放平台配置 (Image Processing)
    viapi_access_key_id: Optional[str] = None  # 阿里云 AccessKey ID (可与 OSS 共用)
    viapi_access_key_secret: Optional[str] = None  # 阿里云 AccessKey Secret (可与 OSS 共用)
    viapi_region: str = "cn-shanghai"  # 服务区域
    viapi_mock_mode: bool = True  # If True, return mock processed image
    
    # Image Understanding Service - Using LiteLLM (unified SDK)
    # Supported providers: openai, azure, anthropic, google, glm, aliyun/dashscope, etc.
    # Model format: "provider/model-name" or just "model-name" (defaults to openai)
    # Examples: 
    #   - OpenAI: "openai/gpt-4o", "openai/gpt-4-vision-preview"
    #   - 阿里云通义千问: "dashscope/qwen-vl-plus", "dashscope/qwen-vl-max", "dashscope/qwen-vl"
    #   - GLM: "zhipuai/glm-4v-plus"
    #   - Azure: "azure/gpt-4o"
    #   - Anthropic: "anthropic/claude-3-opus-20240229"
    llm_provider: str = "openai"  # Provider name: openai, glm, azure, anthropic, google, aliyun/dashscope, etc.
    llm_model: str = "gpt-4o"  # Model name (will be prefixed with provider if needed)
    llm_api_key: Optional[str] = None  # API key for the provider
    llm_base_url: Optional[str] = None  # Custom base URL (for self-hosted or custom endpoints)
    llm_mock_mode: bool = True  # If True, return mock analysis results
    
    # Legacy GLM config (for backward compatibility)
    glm_api_key: Optional[str] = None
    glm_api_url: str = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    glm_model: str = "glm-4v-plus"

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_password: Optional[str] = None
    redis_enabled: bool = False

    # Logging Configuration
    log_max_size_mb: int = 50  # Maximum size of each log file before rotation
    log_backup_count: int = 5  # Number of backup files to keep
    log_cleanup_max_size_mb: int = 50  # Maximum size of individual log file before deletion
    log_cleanup_enabled: bool = True  # Enable automatic log cleanup
    log_cleanup_interval_hours: int = 24  # Run cleanup every N hours

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

