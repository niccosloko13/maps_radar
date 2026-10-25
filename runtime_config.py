"""Environment loading without overwriting platform-injected configuration."""
import os
from pathlib import Path


def load_environment():
    from dotenv import load_dotenv
    root = Path(__file__).resolve().parent
    load_dotenv(root / '.env.local', override=False)
    load_dotenv(root / '.env', override=False)


def hosted():
    return os.environ.get('VERCEL') == '1' or os.environ.get('RELAS_ENV') in ('production', 'preview')


def environment():
    return os.environ.get('VERCEL_ENV') or os.environ.get('RELAS_ENV', 'development')
