import pytest

def test_owner_setup_is_one_time_and_special_access_is_separate(monkeypatch, tmp_path):
    from predictai_core.phase8 import accounts
    monkeypatch.setattr(accounts, 'DB_PATH', tmp_path/'accounts.db')
    monkeypatch.setenv('PREDICTAI_OWNER_SETUP_SECRET', 'private-owner-secret-at-least-32-characters')
    monkeypatch.setenv('PREDICTAI_OWNER_USERNAME', 'chosen_owner')
    with pytest.raises(ValueError):
        accounts.register('founder', 'a-long-password-123', 'special-code', 'wrong', email='founder@example.com', full_legal_name='Test User founder')
    with pytest.raises(ValueError, match='granted by the owner'):
        accounts.register('regular', 'a-long-password-123', 'special-code', email='regular@example.com', full_legal_name='Test User regular')
    owner = accounts.register('chosen_owner', 'a-long-password-123', '', 'private-owner-secret-at-least-32-characters', email='founder@example.com', full_legal_name='Test User founder')
    assert owner['role'] == 'owner'
    normal = accounts.register('regular', 'a-long-password-456', email='regular@example.com', full_legal_name='Test User regular')
    assert normal['role'] == 'regular'
    assert normal['special_access'] is False
    accounts.set_special_access(owner, 'regular', True)
    assert accounts.authenticate('regular', 'a-long-password-456')['special_access'] is True
    assert accounts.authenticate('chosen_owner', 'a-long-password-123')['role'] == 'owner'
    with pytest.raises(ValueError, match='already been completed'):
        accounts.register('chosen_owner', 'a-long-password-789', '', 'private-owner-secret-at-least-32-characters', email='second@example.com', full_legal_name='Second Owner')

def test_non_owner_cannot_grant_special_access(monkeypatch, tmp_path):
    from predictai_core.phase8 import accounts
    monkeypatch.setattr(accounts, 'DB_PATH', tmp_path/'accounts.db')
    monkeypatch.delenv('PREDICTAI_OWNER_SETUP_SECRET', raising=False)
    accounts.register('normal1', 'a-long-password-123', email='normal1@example.com', full_legal_name='Test User normal1')
    accounts.register('normal2', 'a-long-password-456', email='normal2@example.com', full_legal_name='Test User normal2')
    with pytest.raises(PermissionError):
        accounts.set_special_access({'username':'normal1','role':'regular'}, 'normal2', True)
    with pytest.raises(PermissionError):
        accounts.set_special_access({'username':'normal1','role':'owner'}, 'normal2', True)

def test_analytics_require_owner(monkeypatch, tmp_path):
    from predictai_core.phase8 import accounts
    from predictai_core.phase9.admin import require_owner, get_analytics
    monkeypatch.setattr(accounts, 'DB_PATH', tmp_path/'accounts.db')
    with pytest.raises(PermissionError): require_owner({'username':'user','role':'regular'})
    require_owner({'username':'founder','role':'owner'})
    with pytest.raises(PermissionError): get_analytics()

def test_owner_can_revoke_special_access(monkeypatch, tmp_path):
    from predictai_core.phase8 import accounts
    monkeypatch.setattr(accounts, 'DB_PATH', tmp_path/'accounts.db')
    monkeypatch.setenv('PREDICTAI_OWNER_SETUP_SECRET', 'private-owner-secret-at-least-32-characters')
    monkeypatch.setenv('PREDICTAI_OWNER_USERNAME', 'owner')
    owner = accounts.register('owner', 'a-long-owner-password', owner_setup_secret='private-owner-secret-at-least-32-characters', email='owner@example.com', full_legal_name='Test Owner')
    member = accounts.register('member', 'a-long-member-password', email='member@example.com', full_legal_name='Test Member')
    accounts.set_special_access(owner, 'member', True)
    assert accounts.authenticate('member', 'a-long-member-password')['special_access'] is True
    accounts.set_special_access(owner, 'member', False)
    assert accounts.authenticate('member', 'a-long-member-password')['special_access'] is False
