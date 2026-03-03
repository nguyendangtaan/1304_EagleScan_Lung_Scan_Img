from fastapi import APIRouter
from api.endpoint import auth, analysis

api_router = APIRouter()


api_router.include_router(auth.router, prefix="", tags=["Authentication"])
api_router.include_router(analysis.router, prefix="", tags=["Analysis"])