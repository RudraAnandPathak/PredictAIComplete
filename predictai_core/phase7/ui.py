"""Streamlit interface for the Phase 7 intelligence and reporting modules."""
from __future__ import annotations
import json
from pathlib import Path
import pandas as pd
import streamlit as st
from .reasoning import plan_question
from .root_cause import investigate_metric
from .modelling_lab import compare_models, fit_simulator, simulate
from .research import make_evidence_bundle
from .report_engine import build_report, quality_check, export_txt, export_pdf, export_docx, export_pptx
from predictai_core.phase8.explanations import explain_result


def _json(value):
    return json.dumps(value, ensure_ascii=False, indent=2, default=str)


def render_phase7_page():
    st.title('🚀 PredictAI Phase 7 — Intelligence Engine & Unified Reports')
    st.caption('Experimental modules. Review data, metrics, assumptions, and limitations before relying on conclusions.')
    uploaded = st.file_uploader('Upload a CSV or Excel dataset for Phase 7', type=['csv','xlsx','xls'], key='p7_dataset_upload')
    df = None
    if uploaded:
        try:
            df = pd.read_csv(uploaded) if uploaded.name.lower().endswith('.csv') else pd.read_excel(uploaded)
            if df.empty: st.warning('The uploaded dataset has no rows.'); df = None
            else:
                st.session_state['p7_df'] = df
                st.session_state['p7_filename'] = uploaded.name
        except Exception as exc:
            st.error(f'Could not read dataset: {type(exc).__name__}: {exc}')
    elif isinstance(st.session_state.get('p7_df'), pd.DataFrame):
        df = st.session_state['p7_df']
    if df is not None:
        a,b,c = st.columns(3); a.metric('Rows', f'{len(df):,}'); b.metric('Columns', len(df.columns)); c.metric('Missing cells', f'{int(df.isna().sum().sum()):,}')
        with st.expander('Preview dataset'):
            st.dataframe(df.head(30), use_container_width=True)
    tabs = st.tabs(['🧠 Advanced Reasoning','📊 Modelling Lab','🔍 Root Cause Analysis','🧪 What-If Simulator','🌐 Research & Reports'])
    with tabs[0]:
        st.subheader('Break a complex question into analytical tasks')
        question = st.text_area('What do you want to investigate?', placeholder='Why did the outcome change, and which variables are associated with it?', key='p7_reason_question')
        if st.button('Build analysis plan', key='p7_plan_btn'):
            try: st.session_state['p7_plan'] = plan_question(question, list(df.columns) if df is not None else [])
            except Exception as exc: st.error(str(exc))
        if st.session_state.get('p7_plan'):
            explanation = explain_result(st.session_state['p7_plan'], 'Analysis plan')
            st.markdown('**In plain English**')
            st.write(explanation['overview'])
            for fact in explanation['facts']: st.markdown(f'- {fact}')
            with st.expander('View full plan data'):
                st.json(st.session_state['p7_plan'])
            st.caption('This is a transparent task plan, not proof that every planned analysis has already been executed.')
    with tabs[1]:
        st.subheader('Compare models using the existing AutoML engine')
        if df is None: st.info('Upload a dataset to begin.')
        else:
            target = st.selectbox('Prediction target', list(df.columns), key='p7_target')
            task = st.selectbox('Task type', ['auto','classification','regression'], key='p7_task')
            if st.button('Train and evaluate candidate models', type='primary', key='p7_train_btn'):
                try:
                    with st.spinner('Training models and evaluating held-out data...'):
                        result = compare_models(df, target, task)
                    st.session_state['p7_model_result'] = result
                    # Save a scenario simulator separately; it is explicitly a different fitted model.
                    try: st.session_state['p7_simulator'] = fit_simulator(df, target, task)
                    except Exception as sim_exc: st.session_state['p7_simulator_error'] = str(sim_exc)
                    st.success(f"Completed. Selected model: {result.get('best_model','not reported')}")
                except Exception as exc: st.error(f'Model training failed: {type(exc).__name__}: {exc}')
            result = st.session_state.get('p7_model_result')
            if result:
                st.write('**Leaderboard**')
                rows = [{'Model': m.get('name'), 'Baseline': m.get('is_baseline',False), **m.get('metrics',{})} for m in result.get('leaderboard',[])]
                if rows: st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
                st.write('**Best model metrics (raw)**'); st.json(result.get('best_metrics',{}))
                with st.expander('💡 Explain these results in plain English', expanded=True):
                    explanation = explain_result(result, 'AutoML evaluation')
                    st.write(explanation['overview'])
                    for fact in explanation['facts']: st.markdown(f'- {fact}')
                    st.markdown('**Limitations to keep in mind**')
                    for caution in explanation['limitations']: st.markdown(f'- {caution}')
                st.write('**Evaluation notes and cautions**'); st.write(result.get('cautions', result.get('warnings', [])))
                st.caption('A top-ranked model is not automatically good enough. Check the baseline, validation design, class balance, and real-world cost of errors.')
    with tabs[2]:
        st.subheader('Explore possible contributors to a metric')
        if df is None: st.info('Upload a dataset to begin.')
        else:
            numeric = list(df.select_dtypes(include='number').columns)
            if not numeric: st.warning('No numeric metric columns were detected.')
            else:
                metric = st.selectbox('Numeric metric', numeric, key='p7_rc_metric')
                group_options = ['(none)'] + [str(c) for c in df.columns if c != metric]
                group = st.selectbox('Compare across groups (optional)', group_options, key='p7_rc_group')
                if st.button('Investigate metric', key='p7_rc_btn'):
                    try: st.session_state['p7_root_cause'] = investigate_metric(df, metric, None if group=='(none)' else group)
                    except Exception as exc: st.error(str(exc))
            if st.session_state.get('p7_root_cause'):
                with st.expander('💡 Plain-English explanation', expanded=True):
                    explanation = explain_result(st.session_state['p7_root_cause'], 'Root-cause exploration')
                    st.write(explanation['overview'])
                    for fact in explanation['facts']: st.markdown(f'- {fact}')
                    for caution in explanation['limitations']: st.caption(caution)
                with st.expander('View raw result'):
                    st.json(st.session_state['p7_root_cause'])
    with tabs[3]:
        st.subheader('Explore model predictions under changed inputs')
        simulator = st.session_state.get('p7_simulator')
        if df is None: st.info('Upload a dataset first.')
        elif not simulator:
            st.info('Run the Modelling Lab first to fit a scenario model.')
            if st.session_state.get('p7_simulator_error'): st.caption(st.session_state['p7_simulator_error'])
        else:
            st.caption('Changes are predictive scenarios, not causal interventions. Results may be unreliable outside the training data range.')
            base_index = st.selectbox('Baseline row', list(range(min(len(df), 100))), key='p7_sim_base')
            baseline = df.iloc[int(base_index)].to_dict()
            changes = {}
            for col in simulator['feature_columns']:
                if col not in df.columns: continue
                series = df[col]
                if pd.api.types.is_numeric_dtype(series):
                    baseline_value = pd.to_numeric(pd.Series([baseline.get(col)]), errors='coerce').iloc[0]
                    if pd.isna(baseline_value): baseline_value = pd.to_numeric(series, errors='coerce').median()
                    val = st.number_input(f'Override {col}', value=float(baseline_value) if pd.notna(baseline_value) else 0.0, key=f'p7_sim_{col}')
                    changes[col] = val
                else:
                    vals = series.dropna().astype(str).unique().tolist()[:100]
                    if vals:
                        current = str(baseline.get(col, vals[0]))
                        if current not in vals: current = vals[0]
                        changes[col] = st.selectbox(f'Override {col}', vals, index=vals.index(current), key=f'p7_sim_cat_{col}')
            if st.button('Calculate scenario prediction', key='p7_sim_btn'):
                try: st.session_state['p7_sim_result'] = simulate(simulator, baseline, changes)
                except Exception as exc: st.error(f'Simulation failed: {type(exc).__name__}: {exc}')
            if st.session_state.get('p7_sim_result'):
                with st.expander('💡 Explain this scenario', expanded=True):
                    explanation = explain_result(st.session_state['p7_sim_result'], 'What-if scenario')
                    st.write(explanation['overview'])
                    for fact in explanation['facts']: st.markdown(f'- {fact}')
                    for caution in explanation['limitations']: st.caption(caution)
                with st.expander('View raw result'):
                    st.json(st.session_state['p7_sim_result'])
    with tabs[4]:
        st.subheader('Evidence bundle and unified report builder')
        question = st.text_input('Research question / report context', key='p7_report_question')
        title = st.text_input('Report title', value='PredictAI Intelligence Report', key='p7_report_title')
        include_dataset = st.checkbox('Include dataset profile and summary', value=True, key='p7_report_dataset')
        include_model = st.checkbox('Include latest AutoML evaluation', value=True, key='p7_report_model')
        include_root = st.checkbox('Include latest root-cause exploration', value=True, key='p7_report_root')
        include_plan = st.checkbox('Include latest reasoning plan', value=True, key='p7_report_plan')
        if st.button('Assemble report and run quality checks', type='primary', key='p7_build_report'):
            sections = []
            if question.strip(): sections.append({'heading':'Purpose and question','body':question.strip()})
            if include_dataset and df is not None:
                summary = {'file':st.session_state.get('p7_filename','uploaded dataset'),'rows':len(df),'columns':list(map(str,df.columns)),'missing_cells':int(df.isna().sum().sum()),'duplicate_rows':int(df.duplicated().sum()),'numeric_summary':df.select_dtypes(include='number').describe().round(4).to_dict()}
                sections.append({'heading':'Dataset profile','body':summary})
            if include_plan and st.session_state.get('p7_plan'): sections.append({'heading':'Analysis plan','body':st.session_state['p7_plan']})
            if include_model and st.session_state.get('p7_model_result'):
                r = st.session_state['p7_model_result']; sections.append({'heading':'AutoML evaluation','body':{'task':r.get('task'),'target':r.get('target_column',r.get('target')),'best_model':r.get('best_model'),'selection_metric':r.get('selection_metric'),'best_metrics':r.get('best_metrics'),'leaderboard':r.get('leaderboard'),'cautions':r.get('cautions',r.get('warnings',[])),'interpretation':'Evaluation results depend on the split and data quality; compare against the baseline.'}})
            if include_root and st.session_state.get('p7_root_cause'): sections.append({'heading':'Root cause exploration (associational, not causal)','body':st.session_state['p7_root_cause']})
            if st.session_state.get('p7_sim_result'): sections.append({'heading':'What-if scenario','body':st.session_state['p7_sim_result']})
            if not sections: sections.append({'heading':'Status','body':'No analysis outputs were selected or generated. Upload a dataset or run a module first.'})
            sections.append({'heading':'Limitations and responsible use','body':'These results are decision support, not guarantees. Check source data, assumptions, validation metrics, uncertainty, and representativeness. Statistical associations and feature importance do not prove causation. External research is not included unless sources were actually retrieved and documented.'})
            report = build_report(title, sections, {'question':question, 'dataset':st.session_state.get('p7_filename')})
            st.session_state['p7_report'] = report
            st.session_state['p7_report_quality'] = quality_check(report)
        report = st.session_state.get('p7_report')
        if report:
            st.write('**Report quality check**'); st.json(st.session_state['p7_report_quality'])
            st.write('**Report preview**')
            for section in report['sections']:
                with st.expander(section['heading']): st.text(section['body'][:10000])
            for fmt, func, mime, ext in [
                ('TXT',export_txt,'text/plain','txt'),('PDF',export_pdf,'application/pdf','pdf'),('Word',export_docx,'application/vnd.openxmlformats-officedocument.wordprocessingml.document','docx'),('PowerPoint',export_pptx,'application/vnd.openxmlformats-officedocument.presentationml.presentation','pptx')]:
                try:
                    payload = func(report)
                    st.download_button(f'Download {fmt}', data=payload, file_name='predictai_report.'+ext, mime=mime, key='p7_dl_'+ext)
                except Exception as exc:
                    st.warning(f'{fmt} export is unavailable: {type(exc).__name__}: {exc}')
        st.caption('The research bundle only includes evidence explicitly supplied by the user or retrieved by an enabled source. This first release does not claim to have verified the open web.')
