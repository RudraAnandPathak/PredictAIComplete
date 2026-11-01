import pytest

def test_owner_setup_and_special_code_never_grants_owner(monkeypatch, tmp_path):
    from predictai_core.phase8 import accounts
    monkeypatch.setattr(accounts, 'DB_PATH', tmp_path/'accounts.db')
    monkeypatch.setenv('PREDICTAI_OWNER_USERNAME', 'founder')
    monkeypatch.setenv('PREDICTAI_OWNER_SETUP_SECRET', 'private-owner-secret')
    monkeypatch.setenv('PREDICTAI_SPECIAL_ACCESS_CODE', 'special-code')
    with pytest.raises(ValueError):
        accounts.register('founder', 'a-long-password-123', 'special-code', email='founder@example.com', full_legal_name='Test User founder')
    owner = accounts.register('founder', 'a-long-password-123', '', 'private-owner-secret', email='founder@example.com', full_legal_name='Test User founder')
    assert owner['role'] == 'owner'
    normal = accounts.register('regular', 'a-long-password-456', 'special-code', email='regular@example.com', full_legal_name='Test User regular')
    assert normal['role'] == 'regular'
    assert normal['special_access'] is True
    assert accounts.authenticate('founder', 'a-long-password-123')['role'] == 'owner'

def test_non_owner_cannot_grant_special_access(monkeypatch, tmp_path):
    from predictai_core.phase8 import accounts
    monkeypatch.setattr(accounts, 'DB_PATH', tmp_path/'accounts.db')
    monkeypatch.delenv('PREDICTAI_OWNER_USERNAME', raising=False)
    monkeypatch.delenv('PREDICTAI_OWNER_SETUP_SECRET', raising=False)
    accounts.register('normal1', 'a-long-password-123', email='normal1@example.com', full_legal_name='Test User normal1')
    accounts.register('normal2', 'a-long-password-456', email='normal2@example.com', full_legal_name='Test User normal2')
    with pytest.raises(PermissionError):
        accounts.set_special_access({'username':'normal1','role':'regular'}, 'normal2', True)

def test_analytics_require_owner(monkeypatch, tmp_path):
    from predictai_core.phase8 import accounts
    from predictai_core.phase9.admin import require_owner, get_analytics
    monkeypatch.setattr(accounts, 'DB_PATH', tmp_path/'accounts.db')
    with pytest.raises(PermissionError): require_owner({'username':'user','role':'regular'})
    require_owner({'username':'founder','role':'owner'})
    assert get_analytics()['registered_users'] == 0
