from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import get_redoc_html
from contextlib import asynccontextmanager
from pathlib import Path
from app.config import settings
from app.database import engine, Base
from app.exceptions import LuminaException
from app.schemas.common import ErrorResponse, ErrorDetail
from app.utils.log_cleanup import log_cleanup_task
from app.utils.logger import logger, get_log_size_info

# Create database tables
Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("应用启动中...")

    # 显示日志目录信息
    log_info = get_log_size_info()
    logger.info(f"日志目录信息: {log_info['file_count']} 个文件, 总大小 {log_info['total_size_mb']} MB")

    # 启动日志清理任务
    if settings.log_cleanup_enabled:
        await log_cleanup_task.start()
    else:
        logger.info("日志清理功能已禁用")

    yield

    # 关闭时执行
    logger.info("应用关闭中...")
    await log_cleanup_task.stop()


app = FastAPI(
    title="Lumina AI API",
    description="Lumina AI 图片处理应用后端API文档\n\n认证方式：使用Bearer Token认证，在Header中添加 `Authorization: Bearer {token}`",
    version="1.0.0",
    docs_url="/docs",
    redoc_url=None,  # 禁用默认 redoc，使用自定义路由
    lifespan=lifespan,
)


def custom_openapi():
    """自定义 OpenAPI schema，添加 Bearer 认证配置"""
    if app.openapi_schema:
        return app.openapi_schema
    
    from fastapi.openapi.utils import get_openapi
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # 确保 components 存在
    if "components" not in openapi_schema:
        openapi_schema["components"] = {}
    
    # 添加或更新 security schemes
    if "securitySchemes" not in openapi_schema["components"]:
        openapi_schema["components"]["securitySchemes"] = {}
    
    openapi_schema["components"]["securitySchemes"]["bearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
        "description": "使用JWT Token进行认证，格式：Bearer {token}"
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

# CORS middleware
# Configure allowed origins based on environment
allowed_origins = ["*"]  # Default: allow all (for development)
if settings.api_domain:
    # In production, allow API domain and common frontend domains
    allowed_origins = [
        f"https://{settings.api_domain}",
        f"https://www.{settings.api_domain.split('.', 1)[-1] if '.' in settings.api_domain else settings.api_domain}",
        "https://localhost:3000",  # For local development
        "http://localhost:3000",
        "http://localhost:8000",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(LuminaException)
async def lumina_exception_handler(request: Request, exc: LuminaException):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=ErrorDetail(
                code=exc.error_code,
                message=exc.detail,
                details=exc.details
            )
        ).dict()
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=ErrorResponse(
            error=ErrorDetail(
                code="VALIDATION_ERROR",
                message="请求参数验证失败",
                details={"errors": exc.errors()}
            )
        ).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error=ErrorDetail(
                code="INTERNAL_ERROR",
                message="服务器内部错误",
                details={}
            )
        ).dict()
    )


# Include API routers
from app.api.v1 import auth, user, ai, images, works, subscription, scenes, settings as settings_api

app.include_router(auth.router, prefix=settings.api_v1_prefix, tags=["Authentication"])
app.include_router(user.router, prefix=settings.api_v1_prefix, tags=["User"])
app.include_router(ai.router, prefix=settings.api_v1_prefix, tags=["AI"])
app.include_router(images.router, prefix=settings.api_v1_prefix, tags=["Images"])
app.include_router(works.router, prefix=settings.api_v1_prefix, tags=["Works"])
app.include_router(subscription.router, prefix=settings.api_v1_prefix, tags=["Subscription"])
app.include_router(scenes.router, prefix=settings.api_v1_prefix, tags=["Scenes"])
app.include_router(settings_api.router, prefix=settings.api_v1_prefix, tags=["Settings"])

# Custom ReDoc route with reliable CDN
@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    """自定义 ReDoc 页面，使用可靠的 CDN"""
    # 使用多个 CDN 备选方案，确保至少一个可用
    redoc_cdns = [
        "https://unpkg.com/redoc@2.1.3/bundles/redoc.standalone.js",  # unpkg CDN
        "https://cdn.jsdelivr.net/npm/redoc@2.1.3/bundles/redoc.standalone.js",  # jsDelivr CDN
        "https://cdn.redoc.ly/redoc/latest/bundles/redoc.standalone.js",  # Redocly CDN
    ]
    
    # 使用第一个 CDN（通常最可靠）
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=app.title + " - ReDoc",
        redoc_js_url=redoc_cdns[0],
    )


# Mount static files for local storage (mock mode)
if settings.oss_mock_mode or not (settings.oss_access_key_id and settings.oss_access_key_secret):
    uploads_dir = Path(settings.oss_local_storage_path)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    app.mount(f"/{settings.oss_local_storage_path}", StaticFiles(directory=str(uploads_dir)), name="uploads")


@app.get("/")
async def root():
    return {
        "message": "Lumina AI API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}

