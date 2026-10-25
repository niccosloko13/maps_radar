"""Portable Admin sessions: signed tokens, no per-process session registry."""
import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import time
from pathlib import Path
from runtime_config import hosted


def hash_password(password, salt=None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 600000).hex()
    return 'pbkdf2_sha256$600000$'+salt+'$'+digest


def verify_hash(password, encoded):
    try:
        algorithm, count, salt, digest = encoded.split('$')
        if algorithm != 'pbkdf2_sha256' or not 600000 <= int(count) <= 2000000: return False
        actual = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), int(count)).hex()
        return hmac.compare_digest(actual, digest)
    except (ValueError, TypeError): return False


class AdminAuth:
    def __init__(self, data_dir):
        self.data_dir = Path(data_dir)
    @property
    def username(self): return os.environ.get('ADMIN_USERNAME', 'admin' if not hosted() else '')
    def configuration_errors(self):
        if not hosted(): return []
        missing = [k for k in ('ADMIN_USERNAME', 'ADMIN_PASSWORD_HASH', 'SESSION_SECRET') if not os.environ.get(k)]
        if len(os.environ.get('SESSION_SECRET', '')) < 32: missing.append('SESSION_SECRET must contain at least 32 characters')
        encoded=os.environ.get('ADMIN_PASSWORD_HASH','')
        if not re.fullmatch(r'pbkdf2_sha256\$600000\$[a-f0-9]{32}\$[a-f0-9]{64}',encoded): missing.append('ADMIN_PASSWORD_HASH format')
        return missing
    def local_value(self, name, factory):
        self.data_dir.mkdir(parents=True, exist_ok=True)
        path = self.data_dir / name
        try: return path.read_text(encoding='utf8').strip()
        except FileNotFoundError:
            try:
                with path.open('x', encoding='utf8') as f: f.write(factory())
            except FileExistsError: pass
            return path.read_text(encoding='utf8').strip()
    def password_valid(self, username, password):
        if self.configuration_errors(): return False
        if not hmac.compare_digest(str(username).encode(), self.username.encode()): return False
        if os.environ.get('ADMIN_PASSWORD_HASH'): return verify_hash(str(password), os.environ['ADMIN_PASSWORD_HASH'])
        if hosted(): return False
        local = os.environ.get('RELAS_ADMIN_PASSWORD') or self.local_value('admin_password.txt', lambda: secrets.token_urlsafe(24))
        return hmac.compare_digest(str(password).encode(), local.encode())
    def secret(self):
        if self.configuration_errors(): raise RuntimeError('Admin environment is incomplete')
        return os.environ.get('SESSION_SECRET') or self.local_value('session_secret.txt', lambda: secrets.token_urlsafe(48))
    def issue(self):
        payload = base64.urlsafe_b64encode(json.dumps({'user': self.username, 'exp': int(time.time())+28800, 'nonce': secrets.token_hex(16)}, separators=(',', ':')).encode()).decode().rstrip('=')
        signature = hmac.new(self.secret().encode(), payload.encode(), hashlib.sha256).hexdigest()
        return payload+'.'+signature
    def valid(self, token):
        try:
            if not token or self.configuration_errors(): return False
            payload, signature = token.split('.')
            if not hmac.compare_digest(signature, hmac.new(self.secret().encode(), payload.encode(), hashlib.sha256).hexdigest()): return False
            claims = json.loads(base64.urlsafe_b64decode(payload+'='*(-len(payload)%4)))
            return claims['user'] == self.username and claims['exp'] > time.time()
        except (ValueError, KeyError, TypeError): return False
    def cookie(self, token='', logout=False):
        return f'radar_admin={token}; Path=/; Max-Age={0 if logout else 28800}; HttpOnly; SameSite=Lax'+('; Secure' if hosted() else '')
