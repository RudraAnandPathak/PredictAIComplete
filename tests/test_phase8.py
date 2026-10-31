import pytest
import json
import os
import tempfile
from pathlib import Path

from predictai_core.phase8.explanations import explain_metrics, explain_result

def test_classification_metrics_explained_in_plain_language():
    out = explain_metrics({'accuracy': 0.85, 'f1_macro': 0.42}, 'classification')
    assert '85.0%' in out['summary']
    assert any('class balance' in item for item in out['cautions'])
    assert len(out['items']) == 2

def test_regression_explains_error_units():
    out = explain_metrics({'mae': 8.32, 'rmse': 12.47, 'r2': 0.873}, 'regression')
    assert 'target units' in out['summary']
    assert any('penalises large errors' in x['meaning'] for x in out['items'] if x['name'] == 'RMSE')

def test_root_cause_output_avoids_causal_claim():
    out = explain_result({'metric':'sales','valid_rows':10,'overall_mean':100,'overall_median':95,'numeric_associations':{'price':-0.7},'caution':'Association only.'})
    assert 'average' in out['overview']
    assert any('does not show' in fact for fact in out['facts'])

def test_simulation_output_explained():
    out = explain_result({'prediction': 23.5, 'task':'regression','changed_features':{'price':5},'caution':'Predictive only.'})
    assert '23.5' in out['overview']
    assert any('price' in fact for fact in out['facts'])

def test_unknown_result_is_not_fabricated():
    out = explain_result({'mystery_field': 'value'})
    assert 'not recognised' not in out['overview']
    assert any('Mystery field' in fact for fact in out['facts'])

def test_accounts_password_hashing_and_special_access_must_be_owner_granted(monkeypatch, tmp_path):
    from predictai_core.phase8 import accounts
    monkeypatch.setattr(accounts, 'DB_PATH', tmp_path / 'accounts.db')
    with pytest.raises(ValueError, match='granted by the owner'):
        accounts.register('test_user', 'long-test-password', 'unit-test-special-code', email='test_user@example.com', full_legal_name='Test User test_user')
    user = accounts.register('test_user', 'long-test-password', email='test_user@example.com', full_legal_name='Test User test_user')
    assert user['special_access'] is False
    assert accounts.authenticate('test_user', 'long-test-password')['special_access'] is False
    assert accounts.authenticate('test_user', 'wrong-password') is None

def test_accounts_reject_short_password(monkeypatch, tmp_path):
    from predictai_core.phase8 import accounts
    monkeypatch.setattr(accounts, 'DB_PATH', tmp_path / 'accounts.db')
    try:
        accounts.register('shorty', '123', email='shorty@example.com', full_legal_name='Test User shorty')
    except ValueError as exc:
        assert '12 characters' in str(exc)
    else:
        raise AssertionError('Expected short password to be rejected')


def test_registration_and_login_work_without_email_or_legal_name(monkeypatch, tmp_path):
    from predictai_core.phase8 import accounts
    monkeypatch.setattr(accounts, 'DB_PATH', tmp_path / 'accounts.db')
    account = accounts.register('newuser', 'long-password-123')
    assert account['email'] == ''
    assert accounts.authenticate('NEWUSER', 'long-password-123')['username'] == 'newuser'
    with pytest.raises(ValueError):
        accounts.register('bademail', 'long-password-123', email='bad-email')

def test_owner_can_block_regular_user_and_blocked_user_cannot_authenticate(monkeypatch, tmp_path):
    from predictai_core.phase8 import accounts
    monkeypatch.setattr(accounts, 'DB_PATH', tmp_path / 'accounts.db')
    monkeypatch.setenv('PREDICTAI_OWNER_SETUP_SECRET', 'owner-setup-secret-long-enough-0123456789')
    monkeypatch.setenv('PREDICTAI_OWNER_USERNAME', 'founder')
    owner = accounts.register('founder', 'owner-password-long', owner_setup_secret='owner-setup-secret-long-enough-0123456789', email='owner@example.com', full_legal_name='Owner Example')
    accounts.register('member', 'member-password-long', email='member@example.com', full_legal_name='Member Example')
    accounts.set_blocked(owner, 'member', True)
    assert accounts.authenticate('member', 'member-password-long') is None
    with pytest.raises(ValueError):
        accounts.set_blocked(owner, 'founder', True)
    accounts.set_blocked(owner, 'member', False)
    assert accounts.authenticate('member', 'member-password-long') is not None


def test_owner_bootstrap_is_limited_to_configured_username_and_one_use(monkeypatch, tmp_path):
    from predictai_core.phase8 import accounts
    monkeypatch.setattr(accounts, 'DB_PATH', tmp_path / 'accounts.db')
    code = 'owner-setup-secret-long-enough-0123456789'
    monkeypatch.setenv('PREDICTAI_OWNER_SETUP_SECRET', code)
    monkeypatch.setenv('PREDICTAI_OWNER_USERNAME', 'only_owner')
    with pytest.raises(ValueError, match='configured owner username'):
        accounts.register('attacker', 'long-password-123', owner_setup_secret=code)
    owner = accounts.register('ONLY_OWNER', 'owner-password-long', owner_setup_secret=code)
    assert owner['role'] == 'owner'
    assert accounts.authenticate('only_owner', 'owner-password-long')['role'] == 'owner'
    with pytest.raises(ValueError, match='already been completed'):
        accounts.register('only_owner', 'another-password-long', owner_setup_secret=code)
    with pytest.raises(ValueError):
        accounts.register('second_owner', 'another-password-long', owner_setup_secret=code)


def test_login_page_has_three_authentication_tabs():
    from pathlib import Path
    app_source = Path(__file__).resolve().parents[1].joinpath('app.py').read_text()
    assert 'st.tabs(["Sign in", "Create account", "Special Owner Access Code"])' in app_source
