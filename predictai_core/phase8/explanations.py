"""Evidence-grounded, plain-language explanations for PredictAI results.

This module deliberately interprets known metrics and structures instead of asking an
LLM to invent meaning. Unknown fields are clearly labelled as raw results.
"""
from __future__ import annotations
from typing import Any
import math

METRIC_HELP = {
    'accuracy': 'The share of test examples the model classified correctly. It can be misleading when one class is much more common than others.',
    'f1_macro': 'A summary of precision and recall averaged equally across classes. It is useful when performance across minority classes matters.',
    'precision': 'Of the cases predicted as positive, the share that really were positive.',
    'recall': 'Of the actual positive cases, the share the model successfully found.',
    'mae': 'The average absolute distance between predictions and actual values, in the target variable’s units. Lower is better.',
    'rmse': 'A prediction-error measure in the target variable’s units that penalises large errors more heavily. Lower is better.',
    'r2': 'How much variation in the target is explained relative to a simple mean prediction on this evaluation data. It can be negative; higher is not always enough to prove a model is useful.',
    'r2_score': 'How much variation in the target is explained relative to a simple mean prediction on this evaluation data. It can be negative; higher is not always enough to prove a model is useful.',
    'mean_squared_error': 'The average squared prediction error. Its units are squared, so RMSE is often easier to interpret.',
}

def _fmt(value: Any) -> str:
    if value is None: return 'not available'
    if isinstance(value, bool): return 'yes' if value else 'no'
    if isinstance(value, (int, float)):
        if isinstance(value, float) and not math.isfinite(value): return 'not finite'
        return f'{value:,.4f}'.rstrip('0').rstrip('.') if isinstance(value, float) else f'{value:,}'
    return str(value)

def explain_metrics(metrics: dict[str, Any], task: str | None = None) -> dict[str, Any]:
    """Return an approachable summary plus precise per-metric explanations."""
    if not isinstance(metrics, dict):
        return {'summary': 'No structured metrics were provided.', 'items': [], 'cautions': ['Check the original output for details.']}
    items = []
    for key, value in metrics.items():
        low = str(key).lower()
        meaning = METRIC_HELP.get(low, 'A metric produced by the model. Its exact meaning depends on the evaluation method.')
        items.append({'name': str(key).replace('_', ' ').upper(), 'value': _fmt(value), 'meaning': meaning})
    summary = 'These numbers describe performance on the evaluation data, not a guarantee about future cases.'
    if task == 'classification' and 'accuracy' in metrics:
        try:
            acc = float(metrics['accuracy'])
            summary = f'The model classified about {acc*100:.1f}% of evaluation examples correctly. Compare this with the most-common-class baseline and check precision, recall, and class balance before judging usefulness.'
        except (TypeError, ValueError): pass
    elif any(k in metrics for k in ('mae', 'rmse', 'r2', 'r2_score')):
        bits = []
        for k in ('mae', 'rmse'):
            if k in metrics:
                bits.append(f'{k.upper()} is {_fmt(metrics[k])} target units')
        if 'r2' in metrics or 'r2_score' in metrics:
            r2 = metrics.get('r2', metrics.get('r2_score'))
            bits.append(f'R² is {_fmt(r2)}')
        summary = 'Regression performance: ' + '; '.join(bits) + '. Compare errors with a simple baseline and the real-world tolerance for mistakes.'
    return {'summary': summary, 'items': items, 'cautions': [
        'Metrics depend on how the data was split and how representative the evaluation data is.',
        'A strong score does not prove causation, fairness, or reliability on new data.',
        'Compare against a simple baseline and inspect errors before using results for decisions.',
        'For classification, check class balance: accuracy alone can hide poor performance on less common classes.'
    ]}

def explain_result(result: Any, title: str = 'Analysis result') -> dict[str, Any]:
    """Create a readable explanation from known Phase 7 output structures."""
    if not isinstance(result, dict):
        return {'title': title, 'overview': 'The feature returned a result, but it is not in a recognised structured format.', 'facts': [], 'limitations': ['Review the raw output for the exact result.'], 'raw_result': result}
    facts = []
    if 'best_model' in result:
        facts.append(f"Selected model: {result.get('best_model') or 'not reported'}.")
        metrics = explain_metrics(result.get('best_metrics', {}), result.get('task'))
        overview = metrics['summary']
        facts.extend([f"{x['name']}: {x['value']} — {x['meaning']}" for x in metrics['items']])
        cautions = metrics['cautions'] + list(result.get('cautions', result.get('warnings', [])) or [])
    elif 'overall_mean' in result and 'metric' in result:
        metric = result.get('metric')
        overview = f"For '{metric}', the average across {result.get('valid_rows', 0):,} usable rows was {_fmt(result.get('overall_mean'))}; the median was {_fmt(result.get('overall_median'))}."
        if result.get('group_by'):
            groups = result.get('groups') or []
            if groups:
                top = groups[0]
                facts.append(f"The largest absolute difference from the overall average among the shown groups was for '{top.get('group')}', with a difference of {_fmt(top.get('difference_from_overall_mean'))}.")
        corr = result.get('numeric_associations') or {}
        if corr:
            name, val = next(iter(corr.items()))
            facts.append(f"The strongest listed numeric association was with '{name}' (correlation {_fmt(val)}). Correlation does not show that one variable causes the other.")
        cautions = [result.get('caution', 'This is exploratory analysis and does not establish causes.')]
    elif 'prediction' in result:
        overview = f"The model's predicted outcome for this scenario is {_fmt(result.get('prediction'))}."
        changes = result.get('changed_features') or {}
        facts = [f"Scenario input changed: {k} = {_fmt(v)}" for k, v in changes.items()]
        probs = result.get('class_probabilities') or {}
        if probs:
            top = sorted(probs.items(), key=lambda kv: kv[1], reverse=True)[:3]
            facts.append('Reported class probabilities: ' + ', '.join(f'{k}: {v*100:.1f}%' for k, v in top) + '.')
        cautions = [result.get('caution', 'Scenario outputs are predictive, not proof of causal effects.'), 'Results may be unreliable for inputs far outside the data used to train the model.']
    elif 'steps' in result and 'question' in result:
        overview = f"PredictAI created an analysis plan for: “{result.get('question')}”. The plan lists work to do; it does not mean each analysis has already been completed."
        facts = [f'Step {i}: {step}' for i, step in enumerate(result.get('steps') or [], 1)]
        cautions = list(result.get('guardrails') or [])
    else:
        overview = 'PredictAI returned a structured result. The fields below are shown as observations, not as conclusions beyond the evidence.'
        facts = [f'{k.replace("_", " ").capitalize()}: {_fmt(v)}' for k, v in result.items() if k not in {'caution','cautions','warnings'}][:30]
        cautions = [str(x) for x in result.get('cautions', result.get('warnings', []))] if isinstance(result.get('cautions', result.get('warnings', [])), list) else []
    return {'title': title, 'overview': overview, 'facts': facts, 'limitations': [str(x) for x in cautions if x]}
