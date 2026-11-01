import os
import re
import time

from . import IMAGE_DIR, PENDING_DIR

IMAGE_NAME = re.compile(r'[0-9a-f]{32}\.(?:jpg|png|gif|webp)')
PENDING_MAX_AGE = 24 * 60 * 60


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


def move_pending_image(name):
    os.replace(os.path.join(PENDING_DIR, name), os.path.join(IMAGE_DIR, name))


def delete_image_files(filenames):
    for filename in filenames:
        try:
            os.remove(os.path.join(IMAGE_DIR, filename))
        except OSError:
            pass


def remove_stale_pending():
    now = time.time()
    for name in os.listdir(PENDING_DIR):
        if not IMAGE_NAME.fullmatch(name):
            continue
        path = os.path.join(PENDING_DIR, name)
        try:
            if now - os.path.getmtime(path) > PENDING_MAX_AGE:
                os.remove(path)
        except OSError:
            pass
