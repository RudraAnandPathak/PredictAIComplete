"""Phase 8 interface: human-friendly explanations and account status."""
import json
import streamlit as st
from .explanations import explain_result

def render_phase8_page():
    st.title('🧭 PredictAI Phase 8 — Clear Explanations & Accounts')
    st.caption('Translate analytical output into plain language while keeping the underlying evidence visible.')
    tabs = st.tabs(['💡 Explain Results', '🔐 Account & Access'])
    with tabs[0]:
        options = {
            'Latest AutoML evaluation': st.session_state.get('p7_model_result'),
            'Latest root-cause exploration': st.session_state.get('p7_root_cause'),
            'Latest What-If prediction': st.session_state.get('p7_sim_result'),
            'Latest reasoning plan': st.session_state.get('p7_plan'),
        }
        available = [k for k,v in options.items() if isinstance(v, dict)]
        if not available:
            st.info('Run an analysis in the Phase 7 workspace first, or paste a structured JSON result below.')
        selected = st.selectbox('Choose a result to explain', available or ['Paste JSON result'])
        raw = options.get(selected) if available else None
        pasted = st.text_area('Or paste a JSON result', height=180, placeholder='Paste the result object here…')
        if st.button('Explain in plain English', type='primary'):
            if pasted.strip():
                try: raw = json.loads(pasted)
                except json.JSONDecodeError as exc:
                    st.error(f'That is not valid JSON: {exc}'); raw = None
            if raw is not None:
                explanation = explain_result(raw, selected)
                st.session_state['p8_explanation'] = explanation
        exp = st.session_state.get('p8_explanation')
        if exp:
            st.subheader(exp.get('title', 'Explanation'))
            st.markdown('### What this means')
            st.write(exp.get('overview', 'No overview available.'))
            if exp.get('facts'):
                st.markdown('### Key findings')
                for fact in exp['facts']: st.markdown(f'- {fact}')
            if exp.get('limitations'):
                st.markdown('### Important limitations')
                for item in exp['limitations']: st.markdown(f'- {item}')
            with st.expander('View underlying result (for transparency)'):
                st.json(raw if raw is not None else exp.get('raw_result', {}))
    with tabs[1]:
        user = st.session_state.get('predictai_user')
        if user:
            st.success(f"Signed in as **{user.get('username')}**")
            st.write('Access level:', 'Owner' if user.get('role') == 'owner' else ('Special access' if user.get('special_access') else 'Standard access'))
            st.caption('Special access is stored on the account and persists across sign-ins. This phase does not yet include the owner analytics dashboard.')
        else:
            st.info('You are currently using PredictAI without a signed-in account. Account sign-in can be enabled from the main app when configured.')
        st.warning('This account store is designed for local testing. Before public deployment, use a managed identity provider, HTTPS, rate limiting, and server-side secret management.')
