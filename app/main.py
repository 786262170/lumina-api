from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.config import settings
from app.database import engine, Base
from app.exceptions import LuminaException
from app.schemas.common import ErrorResponse, ErrorDetail

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Lumina AI API",
    description="Lumina AI 图片处理应用后端API文档",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
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
from app.api.v1 import auth, user, ai, images, works, subscription, scenes, settings_api

app.include_router(auth.router, prefix=settings.api_v1_prefix, tags=["Authentication"])
app.include_router(user.router, prefix=settings.api_v1_prefix, tags=["User"])
app.include_router(ai.router, prefix=settings.api_v1_prefix, tags=["AI"])
app.include_router(images.router, prefix=settings.api_v1_prefix, tags=["Images"])
app.include_router(works.router, prefix=settings.api_v1_prefix, tags=["Works"])
app.include_router(subscription.router, prefix=settings.api_v1_prefix, tags=["Subscription"])
app.include_router(scenes.router, prefix=settings.api_v1_prefix, tags=["Scenes"])
app.include_router(settings_api.router, prefix=settings.api_v1_prefix, tags=["Settings"])


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

