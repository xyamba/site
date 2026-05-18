import os

# URL FastAPI-бэкенда (тот же, что у мобильного приложения)
API_BASE_URL = os.environ.get("INKBOOK_API_URL", "http://api.inkbook.ru")


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "inkbook-site-secret-change-me")
    API_BASE_URL = API_BASE_URL
    UPLOAD_FOLDER = "static/uploads"
    THUMBNAIL_FOLDER = "static/thumbnails"
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024