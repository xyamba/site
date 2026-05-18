import os
from PIL import Image
from flask import current_app
import uuid

def save_picture(form_picture, thumbnail=False):
    """Сохраняет изображение и возвращает имя файла и миниатюры"""
    ext = form_picture.filename.rsplit('.', 1)[1].lower()
    unique_name = str(uuid.uuid4())[:8] + '.' + ext
    thumb_name = 'thumb_' + unique_name

    upload_folder = current_app.config['UPLOAD_FOLDER']
    thumb_folder = current_app.config['THUMBNAIL_FOLDER']
    os.makedirs(upload_folder, exist_ok=True)
    os.makedirs(thumb_folder, exist_ok=True)

    orig_path = os.path.join(upload_folder, unique_name)
    thumb_path = os.path.join(thumb_folder, thumb_name)

    # Оригинал
    img = Image.open(form_picture)
    if img.width > 1200:
        ratio = 1200 / img.width
        new_height = int(img.height * ratio)
        img = img.resize((1200, new_height), Image.Resampling.LANCZOS)
    img.save(orig_path, quality=85, optimize=True)

    # Миниатюра
    thumb = Image.open(form_picture)
    thumb.thumbnail((300, 300), Image.Resampling.LANCZOS)
    thumb.save(thumb_path, quality=85, optimize=True)

    return unique_name, thumb_name