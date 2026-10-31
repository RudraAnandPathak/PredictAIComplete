"""Run locally once to create the first Owner account."""
import getpass, re
from auth_security import init_auth_db, create_owner_account
init_auth_db()
print('PredictAI Owner setup (run this on your own computer; do not share the password).')
name=input('Owner full name: ').strip()
email=input('Owner email: ').strip()
username=input('Owner username (3-32 chars): ').strip()
password=getpass.getpass('Owner password (minimum 12 characters): ')
confirm=getpass.getpass('Confirm password: ')
if password != confirm:
    raise SystemExit('Passwords do not match.')
if not re.fullmatch(r'[A-Za-z0-9_.-]{3,32}',username):
    raise SystemExit('Invalid username format.')
ok,message=create_owner_account(name,email,username,password)
print(message)
if not ok: raise SystemExit(1)
