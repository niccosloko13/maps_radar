"""Print credentials for your secret manager; never redirect into tracked files."""
import getpass
import secrets
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from admin_auth import hash_password

if __name__=='__main__':
    password=getpass.getpass('New Admin password: ')
    if len(password)<12:raise SystemExit('Use at least 12 characters')
    print('ADMIN_PASSWORD_HASH='+hash_password(password))
    print('SESSION_SECRET='+secrets.token_urlsafe(48))
