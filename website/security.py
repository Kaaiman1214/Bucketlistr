import math
import os
import threading
import time

from flask import request
from werkzeug.middleware.proxy_fix import ProxyFix


def env_flag(name):
    return os.environ.get(name, '').strip().lower() in ('1', 'true', 'yes', 'on')


class FailureLimiter:
    def __init__(self, limit, window, clock=time.monotonic):
        self.limit = limit
        self.window = window
        self.clock = clock
        self._failures = {}
        self._lock = threading.Lock()

    def _recent(self, key, now):
        stamps = [stamp for stamp in self._failures.get(key, []) if now - stamp < self.window]
        if stamps:
            self._failures[key] = stamps
        else:
            self._failures.pop(key, None)
        return stamps

    def retry_after(self, key):
        now = self.clock()
        with self._lock:
            stamps = self._recent(key, now)
            if len(stamps) >= self.limit:
                oldest_that_counts = stamps[len(stamps) - self.limit]
                return int(self.window - (now - oldest_that_counts)) + 1
        return 0

    def record(self, key):
        now = self.clock()
        with self._lock:
            stamps = self._recent(key, now)
            stamps.append(now)
            self._failures[key] = stamps
            if len(self._failures) > 10000:
                for stale in list(self._failures):
                    self._recent(stale, now)

    def reset(self, key):
        with self._lock:
            self._failures.pop(key, None)


login_ip_limiter = FailureLimiter(limit=5, window=15 * 60)
login_user_limiter = FailureLimiter(limit=20, window=15 * 60)
password_limiter = FailureLimiter(limit=5, window=15 * 60)


def client_ip():
    return request.remote_addr or 'unknown'


def wait_message(seconds):
    minutes = max(1, math.ceil(seconds / 60))
    return f"Too many failed attempts. Try again in about {minutes} minute{'' if minutes == 1 else 's'}."


def init_security(app):
    secure = env_flag('BUCKETLIST_SECURE_COOKIES')
    app.config.update(
        SESSION_COOKIE_SECURE=secure,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        REMEMBER_COOKIE_SECURE=secure,
        REMEMBER_COOKIE_HTTPONLY=True,
        REMEMBER_COOKIE_SAMESITE='Lax',
    )

    try:
        proxies = int(os.environ.get('BUCKETLIST_TRUSTED_PROXIES') or 0)
    except ValueError:
        proxies = 0
    if proxies > 0:
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=proxies, x_proto=proxies, x_host=proxies)
