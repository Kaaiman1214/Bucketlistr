import os
import re
import secrets
import threading
import time

from PIL import Image, ImageOps

from . import IMAGE_DIR, PENDING_DIR

IMAGE_NAME = re.compile(r'[0-9a-f]{32}\.(?:jpg|png|gif|webp)')
PENDING_MAX_AGE = 24 * 60 * 60
DERIVED_SIZES = {'thumb': 720, 'medium': 1920}


def image_extension(storage):
    head = storage.stream.read(12)
    storage.stream.seek(0)
    if head.startswith(b'\xff\xd8\xff'):
        return '.jpg'
    if head.startswith(b'\x89PNG\r\n\x1a\n'):
        return '.png'
    if head.startswith((b'GIF87a', b'GIF89a')):
        return '.gif'
    if head[:4] == b'RIFF' and head[8:12] == b'WEBP':
        return '.webp'
    return None


def pending_exists(name):
    return os.path.isfile(os.path.join(PENDING_DIR, name))


def derived_path(directory, name, size):
    stem = os.path.splitext(name)[0]
    return os.path.join(directory, size, stem + '.jpg')


def wants_derived(name, size):
    if size not in DERIVED_SIZES:
        return False
    return not (size == 'medium' and name.endswith('.gif'))


def make_derived(directory, name, size):
    target = derived_path(directory, name, size)
    if os.path.isfile(target):
        return target

    limit = DERIVED_SIZES[size]
    temp = target + '.' + secrets.token_hex(4) + '.tmp'
    try:
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with Image.open(os.path.join(directory, name)) as image:
            if image.format == 'JPEG':
                image.draft('RGB', (limit, limit))
            image = ImageOps.exif_transpose(image)
            if image.mode in ('RGBA', 'LA') or (image.mode == 'P' and 'transparency' in image.info):
                image = image.convert('RGBA')
                flat = Image.new('RGB', image.size, (255, 255, 255))
                flat.paste(image, mask=image.getchannel('A'))
                image = flat
            else:
                image = image.convert('RGB')
            image.thumbnail((limit, limit))
            image.save(temp, 'JPEG', quality=85, optimize=True, progressive=True)
        os.replace(temp, target)
    except Exception:
        try:
            os.remove(temp)
        except OSError:
            pass
        return None
    return target


def move_pending_image(name):
    os.replace(os.path.join(PENDING_DIR, name), os.path.join(IMAGE_DIR, name))
    for size in DERIVED_SIZES:
        source = derived_path(PENDING_DIR, name, size)
        if os.path.isfile(source):
            target = derived_path(IMAGE_DIR, name, size)
            os.makedirs(os.path.dirname(target), exist_ok=True)
            os.replace(source, target)


def delete_image_files(filenames):
    for filename in filenames:
        paths = [os.path.join(IMAGE_DIR, filename)]
        paths += [derived_path(IMAGE_DIR, filename, size) for size in DERIVED_SIZES]
        for path in paths:
            try:
                os.remove(path)
            except OSError:
                pass


def backfill_derived_images(app):
    def work():
        with app.app_context():
            from .models import Photo
            filenames = [photo.filename for photo in Photo.query.all()]
        for filename in filenames:
            if not os.path.isfile(os.path.join(IMAGE_DIR, filename)):
                continue
            for size in DERIVED_SIZES:
                if wants_derived(filename, size):
                    make_derived(IMAGE_DIR, filename, size)

    threading.Thread(target=work, daemon=True).start()


def remove_stale_pending():
    now = time.time()
    folders = [PENDING_DIR] + [os.path.join(PENDING_DIR, size) for size in DERIVED_SIZES]
    for folder in folders:
        if not os.path.isdir(folder):
            continue
        for name in os.listdir(folder):
            if not IMAGE_NAME.fullmatch(name):
                continue
            path = os.path.join(folder, name)
            try:
                if now - os.path.getmtime(path) > PENDING_MAX_AGE:
                    os.remove(path)
            except OSError:
                pass
