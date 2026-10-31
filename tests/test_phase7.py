import pandas as pd
import pytest
from predictai_core.phase7 import plan_question, investigate_metric, build_report, quality_check, export_txt


def test_reasoning_plan_has_guardrails():
    result = plan_question('Why did sales decrease?', ['sales','region'])
    assert result['steps']
    assert any('causation' in item.lower() for item in result['guardrails'])


def test_root_cause_grouped_descriptive_stats():
    df = pd.DataFrame({'sales':[10,20,30,40], 'region':['A','A','B','B']})
    result = investigate_metric(df, 'sales', 'region')
    assert result['valid_rows'] == 4
    assert len(result['groups']) == 2
    assert 'do not establish causes' in result['interpretation']


def test_report_quality_and_text_export():
    report = build_report('Test', [{'heading':'Findings','body':'Observed results and limitations.'}])
    assert quality_check(report)['passed']
    assert b'Observed results' in export_txt(report)


def test_report_flags_empty_section():
    report = build_report('Test', [{'heading':'Empty','body':''}])
    assert not quality_check(report)['passed']
