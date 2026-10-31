"""Transparent task decomposition for complex analytics questions."""
from __future__ import annotations
import re
from typing import Any


def plan_question(question: str, columns: list[str] | None = None) -> dict[str, Any]:
    q = str(question or '').strip()
    if not q:
        raise ValueError('Enter a question to plan.')
    lower = q.lower()
    tasks = []
    if any(w in lower for w in ('why', 'cause', 'caused', 'driver', 'changed', 'change', 'drop', 'increase', 'decrease')):
        tasks += ['Define the outcome and comparison period/groups.', 'Check data quality, missingness, and relevant segment differences.', 'Quantify associations and compare plausible contributing variables.', 'Separate supported associations from causal claims.']
    if any(w in lower for w in ('predict', 'forecast', 'future', 'will', 'model')):
        tasks += ['Identify the target variable and prediction horizon.', 'Choose a suitable validation design and baseline.', 'Compare candidate models using task-appropriate metrics.', 'Report uncertainty, limitations, and whether performance is adequate.']
    if any(w in lower for w in ('compare', 'difference', 'versus', ' vs ', 'between')):
        tasks += ['Confirm that the groups and measures are comparable.', 'Calculate effect sizes and uncertainty where possible.', 'Check whether the observed difference is practically meaningful.']
    if any(w in lower for w in ('summar', 'report', 'insight', 'analyse', 'analyze', 'relationship', 'correlation')) or not tasks:
        tasks += ['Profile the dataset and validate key fields.', 'Run relevant descriptive statistics and visualisations.', 'Summarise findings with supporting evidence and caveats.']
    tasks = list(dict.fromkeys(tasks))
    return {'question': q, 'steps': tasks, 'available_columns': list(columns or []), 'guardrails': ['Use computed results as the source of truth.', 'Do not treat correlation or feature importance as proof of causation.', 'State when evidence is insufficient.']}
