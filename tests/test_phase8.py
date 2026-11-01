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

def test_accounts_password_hashing_and_persistent_special_access(monkeypatch, tmp_path):
    from predictai_core.phase8 import accounts
    monkeypatch.setattr(accounts, 'DB_PATH', tmp_path / 'accounts.db')
    monkeypatch.setenv('PREDICTAI_SPECIAL_ACCESS_CODE', 'unit-test-special-code')
    user = accounts.register('test_user', 'long-test-password', 'unit-test-special-code', email='test_user@example.com', full_legal_name='Test User test_user')
    assert user['special_access'] is True
    assert accounts.authenticate('test_user', 'long-test-password')['special_access'] is True
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


def test_new_account_requires_legal_name_and_email(monkeypatch, tmp_path):
    from predictai_core.phase8 import accounts
    monkeypatch.setattr(accounts, 'DB_PATH', tmp_path / 'accounts.db')
    with pytest.raises(ValueError):
        accounts.register('newuser', 'long-password-123', email='', full_legal_name='New User')
    with pytest.raises(ValueError):
        accounts.register('newuser', 'long-password-123', email='bad-email', full_legal_name='New User')
    account = accounts.register('newuser', 'long-password-123', email='new@example.com', full_legal_name='New User')
    assert account['email'] == 'new@example.com'
    assert account['full_legal_name'] == 'New User'

def test_owner_can_block_regular_user_and_blocked_user_cannot_authenticate(monkeypatch, tmp_path):
    from predictai_core.phase8 import accounts
    monkeypatch.setattr(accounts, 'DB_PATH', tmp_path / 'accounts.db')
    monkeypatch.setenv('PREDICTAI_OWNER_USERNAME', 'founder')
    monkeypatch.setenv('PREDICTAI_OWNER_SETUP_SECRET', 'owner-setup-secret-long')
    owner = accounts.register('founder', 'owner-password-long', owner_setup_secret='owner-setup-secret-long', email='owner@example.com', full_legal_name='Owner Example')
    accounts.register('member', 'member-password-long', email='member@example.com', full_legal_name='Member Example')
    accounts.set_blocked(owner, 'member', True)
    assert accounts.authenticate('member', 'member-password-long') is None
    with pytest.raises(ValueError):
        accounts.set_blocked(owner, 'founder', True)
    accounts.set_blocked(owner, 'member', False)
    assert accounts.authenticate('member', 'member-password-long') is not None
