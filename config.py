import os
from dotenv import load_dotenv
from datetime import timedelta


load_dotenv()
class Config:
    SECRET_KEY=os.getenv("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS=False

    JWT_SECRET_KEY=os.getenv("JWT_SECRET_KEY")
    JWT_TOKEN_LOCATION = ['cookies']
    
    JWT_ACCESS_TOKEN_EXPIRES=timedelta(minutes=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", 15)))
    JWT_REFRESH_TOKEN_EXPIRES=timedelta(days=int(os.getenv("JWT_REFRESH_TOKEN_EXPIRES", 30)))
    
    JWT_COOKIE_SECURE=False
    JWT_COOKIE_CSRF_PROTECT=True
    JWT_LOGOUT_CSRF_PROTECT=False
    JWT_COOKIE_SAMESITE='Lax'