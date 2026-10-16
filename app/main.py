import sys
import os

os.environ["LANGSMITH_TRACING"] = "false"
os.environ["LANGCHAIN_TRACING_V2"] = "false"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Job Finder CV",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

from app.config import setup_langsmith, ANTHROPIC_API_KEY
from app.profile_manager import (
    save_profile,
    load_profile,
    list_profiles,
    get_selected,
    set_selected,
    delete_profile,
)
from app.chains.cv_extraction_chain import create_cv_extraction_chain
from app.chains.job_matching_chain import create_job_matching_chain
from app.job_search import search_jobs

setup_langsmith()

# ── Helpers ───────────────────────────────────────────────────────────────────
_WORK_COLS = ["company", "title", "start_date", "end_date", "description"]
_EDU_COLS  = ["institution", "degree", "start_date", "end_date", "description"]
_WORK_LABELS = {"company": "Empresa", "title": "Puesto", "start_date": "Inicio", "end_date": "Fin", "description": "Descripción"}
_EDU_LABELS  = {"institution": "Centro", "degree": "Titulación", "start_date": "Inicio", "end_date": "Fin", "description": "Descripción"}

def _to_df(entries: list, cols: list) -> pd.DataFrame:
    if not entries:
        return pd.DataFrame([{c: "" for c in cols}])
    rows = [{c: e.get(c, "") for c in cols} for e in entries]
    return pd.DataFrame(rows)

def _from_df(df: pd.DataFrame) -> list:
    return [
        {k: str(v) if v is not None else "" for k, v in row.items()}
        for _, row in df.iterrows()
        if any(str(v).strip() for v in row.values)
    ]

def _parse_list(text: str) -> list:
    items = [i.strip() for i in text.replace(",", "\n").splitlines()]
    return [i for i in items if i]

def _recent_experience_summary(profile: dict) -> str:
    jobs = profile.get("work_experience", [])[:3]
    if not jobs:
        return "No work experience listed"
    return "; ".join(
        f"{j.get('title', '')} at {j.get('company', '')} ({j.get('start_date', '')}–{j.get('end_date', '')})"
        for j in jobs
    )

# ── Session state ─────────────────────────────────────────────────────────────
if "active_slug" not in st.session_state:
    st.session_state.active_slug = get_selected()
if "profile" not in st.session_state:
    slug = st.session_state.active_slug
    st.session_state.profile = load_profile(slug) if slug else None
if "search_results" not in st.session_state:
    st.session_state.search_results = []
if "matches" not in st.session_state:
    st.session_state.matches = {}
if "pending_profile" not in st.session_state:
    st.session_state.pending_profile = None
if "editing_general" not in st.session_state:
    st.session_state.editing_general = False
if "editing_work" not in st.session_state:
    st.session_state.editing_work = False
if "editing_edu" not in st.session_state:
    st.session_state.editing_edu = False

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🔍 Job Finder CV")
    st.caption("Encuentra trabajos que encajan con tu perfil")
    st.divider()

    if not ANTHROPIC_API_KEY:
        st.error("Configura `ANTHROPIC_API_KEY` en el archivo `.env` para continuar.")

    slugs = list_profiles()

    if slugs:
        st.subheader("👤 Perfiles guardados")

        def _display_name(slug: str) -> str:
            p = load_profile(slug)
            return p.get("name", slug) if p else slug

        options = {_display_name(s): s for s in slugs}
        current_name = (
            _display_name(st.session_state.active_slug)
            if st.session_state.active_slug in slugs
            else list(options.keys())[0]
        )

        selected_name = st.selectbox(
            "Perfil activo",
            options=list(options.keys()),
            index=list(options.keys()).index(current_name) if current_name in options else 0,
            label_visibility="collapsed",
        )
        selected_slug = options[selected_name]

        if selected_slug != st.session_state.active_slug:
            st.session_state.active_slug = selected_slug
            st.session_state.profile = load_profile(selected_slug)
            st.session_state.search_results = []
            st.session_state.matches = {}
            set_selected(selected_slug)
            st.rerun()

        col_edit, col_del = st.columns(2)
        with col_del:
            if st.button("🗑️ Eliminar", width="stretch"):
                delete_profile(selected_slug)
                st.session_state.active_slug = get_selected()
                st.session_state.profile = (
                    load_profile(st.session_state.active_slug)
                    if st.session_state.active_slug else None
                )
                st.session_state.search_results = []
                st.session_state.matches = {}
                st.rerun()

        st.divider()

    with st.expander("➕ Añadir nuevo perfil", expanded=not slugs):
        uploaded_file = st.file_uploader("Sube un CV (PDF)", type=["pdf"], key="cv_uploader")

        if uploaded_file:
            if st.button("Analizar CV", type="primary", width="stretch"):
                with st.spinner("Analizando con Claude…"):
                    try:
                        chain = create_cv_extraction_chain()
                        profile_obj = chain({"pdf_bytes": uploaded_file.read()})
                        st.session_state.pending_profile = profile_obj.model_dump()
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Error al analizar el CV: {exc}")

        if st.session_state.pending_profile:
            st.info("CV analizado. Revisa y guarda en la pestaña **Mi Perfil**.")

    profile = st.session_state.profile
    if profile:
        st.divider()
        st.markdown(f"**{profile.get('name', '—')}**")
        st.markdown(f"*{profile.get('current_title', '')}*")
        st.markdown(f"🕐 {profile.get('years_in_current_role', 0)} años en el puesto actual")
        langs = profile.get("languages", [])
        if langs:
            st.markdown(f"🌍 {' · '.join(langs)}")
        skills = profile.get("technical_skills") or profile.get("skills", [])
        if skills:
            st.markdown("**Habilidades:**")
            st.markdown(" ".join(f"`{s}`" for s in skills[:12]) + (" …" if len(skills) > 12 else ""))

# ── Main ──────────────────────────────────────────────────────────────────────
st.title("Encuentra tu próximo trabajo 🚀")

tab_profile, tab_search = st.tabs(["👤 Mi Perfil", "🔍 Buscar empleos"])

# ══ TAB: MI PERFIL ════════════════════════════════════════════════════════════
with tab_profile:
    working = st.session_state.pending_profile or st.session_state.profile
    is_new = bool(st.session_state.pending_profile)

    if not working:
        st.info("Sube tu CV en el panel lateral para crear tu primer perfil.")
    else:
        if is_new:
            st.success("CV analizado. Revisa los datos, edítalos si es necesario y guarda el perfil.")

        # ── Información general ───────────────────────────────────────────────
        _hcol, _bcol = st.columns([6, 1])
        with _hcol:
            st.subheader("📋 Información general")
        if not is_new:
            with _bcol:
                if not st.session_state.editing_general:
                    if st.button("✏️ Editar", key="edit_general"):
                        st.session_state.editing_general = True
                        st.rerun()
                else:
                    if st.button("✕ Cancelar", key="cancel_general"):
                        st.session_state.editing_general = False
                        st.rerun()

        if is_new or st.session_state.editing_general:
            with st.form("general_form"):
                c1, c2 = st.columns(2)
                with c1:
                    f_name  = st.text_input("Nombre del perfil *", value=working.get("name", ""))
                    f_title = st.text_input("Puesto actual / más reciente", value=working.get("current_title", ""))
                    f_email = st.text_input("Email", value=working.get("email", ""))
                with c2:
                    f_exp = st.number_input(
                        "Años de experiencia en el puesto actual",
                        min_value=0, max_value=50,
                        value=int(working.get("years_in_current_role", 0)),
                    )
                    f_langs = st.text_input(
                        "Idiomas (separados por coma)",
                        value=", ".join(working.get("languages", [])),
                    )
                    f_skills = st.text_area(
                        "Habilidades técnicas (una por línea o separadas por coma)",
                        value="\n".join(working.get("technical_skills") or working.get("skills", [])),
                        height=120,
                    )
                f_summary = st.text_area("Resumen profesional", value=working.get("summary", ""), height=90)
                save_general = st.form_submit_button("💾 Guardar información general", type="primary", width="stretch")

            if save_general:
                if not f_name.strip():
                    st.error("El nombre del perfil es obligatorio.")
                else:
                    updated = {
                        **(working or {}),
                        "name": f_name.strip(),
                        "current_title": f_title.strip(),
                        "email": f_email.strip(),
                        "years_in_current_role": int(f_exp),
                        "languages": _parse_list(f_langs),
                        "technical_skills": _parse_list(f_skills),
                        "summary": f_summary.strip(),
                    }
                    new_slug = save_profile(updated)
                    st.session_state.active_slug = new_slug
                    st.session_state.profile = updated
                    st.session_state.pending_profile = None
                    st.session_state.editing_general = False
                    set_selected(new_slug)
                    st.success(f"Perfil **{updated['name']}** guardado.")
                    st.rerun()
        else:
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"**Nombre:** {working.get('name', '—')}")
                st.markdown(f"**Puesto:** {working.get('current_title', '—')}")
                st.markdown(f"**Email:** {working.get('email', '—') or '—'}")
            with c2:
                st.markdown(f"**Experiencia:** {working.get('years_in_current_role', 0)} años en el puesto actual")
                langs = working.get("languages", [])
                st.markdown(f"**Idiomas:** {', '.join(langs) if langs else '—'}")
                skills = working.get("technical_skills") or working.get("skills", [])
                if skills:
                    st.markdown("**Habilidades:** " + " ".join(f"`{s}`" for s in skills))
            summary = working.get("summary", "")
            if summary:
                st.markdown(f"**Resumen:** {summary}")

        st.divider()

        # ── Experiencia laboral ───────────────────────────────────────────────
        _hcol2, _bcol2 = st.columns([6, 1])
        with _hcol2:
            st.subheader("💼 Experiencia laboral")
        if not is_new:
            with _bcol2:
                if not st.session_state.editing_work:
                    if st.button("✏️ Editar", key="edit_work"):
                        st.session_state.editing_work = True
                        st.rerun()
                else:
                    if st.button("✕ Cancelar", key="cancel_work"):
                        st.session_state.editing_work = False
                        st.rerun()

        work_df = _to_df(working.get("work_experience", []), _WORK_COLS)

        if is_new or st.session_state.editing_work:
            st.caption("Usa el botón + para añadir filas.")
            edited_work = st.data_editor(
                work_df,
                num_rows="dynamic",
                width="stretch",
                column_config={k: st.column_config.TextColumn(v) for k, v in _WORK_LABELS.items()},
                key="work_editor",
            )
            if st.button("💾 Guardar experiencia laboral", type="primary", width="stretch"):
                updated = {
                    **(st.session_state.profile or working or {}),
                    "work_experience": _from_df(edited_work),
                }
                slug = save_profile(updated)
                st.session_state.active_slug = slug
                st.session_state.profile = updated
                st.session_state.pending_profile = None
                st.session_state.editing_work = False
                set_selected(slug)
                st.success("Experiencia laboral guardada.")
                st.rerun()
        else:
            st.dataframe(
                work_df.rename(columns=_WORK_LABELS),
                use_container_width=True,
                hide_index=True,
            )

        st.divider()

        # ── Educación ─────────────────────────────────────────────────────────
        _hcol3, _bcol3 = st.columns([6, 1])
        with _hcol3:
            st.subheader("🎓 Educación")
        if not is_new:
            with _bcol3:
                if not st.session_state.editing_edu:
                    if st.button("✏️ Editar", key="edit_edu"):
                        st.session_state.editing_edu = True
                        st.rerun()
                else:
                    if st.button("✕ Cancelar", key="cancel_edu"):
                        st.session_state.editing_edu = False
                        st.rerun()

        edu_df = _to_df(working.get("education", []), _EDU_COLS)

        if is_new or st.session_state.editing_edu:
            st.caption("Usa el botón + para añadir filas.")
            edited_edu = st.data_editor(
                edu_df,
                num_rows="dynamic",
                width="stretch",
                column_config={k: st.column_config.TextColumn(v) for k, v in _EDU_LABELS.items()},
                key="edu_editor",
            )
            if st.button("💾 Guardar educación", type="primary", width="stretch"):
                updated = {
                    **(st.session_state.profile or working or {}),
                    "education": _from_df(edited_edu),
                }
                slug = save_profile(updated)
                st.session_state.active_slug = slug
                st.session_state.profile = updated
                st.session_state.pending_profile = None
                st.session_state.editing_edu = False
                set_selected(slug)
                st.success("Educación guardada.")
                st.rerun()
        else:
            st.dataframe(
                edu_df.rename(columns=_EDU_LABELS),
                use_container_width=True,
                hide_index=True,
            )

# ══ TAB: BUSCAR EMPLEOS ═══════════════════════════════════════════════════════
with tab_search:
    profile = st.session_state.profile

    if not profile:
        st.info("👈 Sube tu CV en el panel lateral para empezar.")
        st.stop()

    from app.config import ADZUNA_APP_ID, INFOJOBS_CLIENT_ID
    sources = []
    if ADZUNA_APP_ID:
        sources.append("Adzuna")
    if INFOJOBS_CLIENT_ID:
        sources.append("InfoJobs")
    if sources:
        st.caption(f"Buscando en: {' · '.join(sources)} · Solo empleos de Data Science / Analytics")
    else:
        st.caption("Usando datos de demo · Añade claves de Adzuna o InfoJobs al `.env` para ofertas reales")

    col1, col2 = st.columns(2)
    with col1:
        position = st.text_input("💼 Puesto", placeholder="Backend, Python, Data Scientist…")
    with col2:
        location = st.text_input("📍 Ubicación", placeholder="Madrid, Barcelona…")

    col3, col4 = st.columns(2)
    with col3:
        exp_range = st.slider("Años de experiencia requeridos", 0, 20, (0, 10))
    with col4:
        include_remote = st.checkbox("Incluir ofertas en remoto", value=True)

    search_clicked = st.button("🔍 Buscar empleos", type="primary", width="stretch")

    if search_clicked:
        with st.spinner("Buscando ofertas…"):
            results, api_errors = search_jobs(
                position=position,
                location=location,
                include_remote=include_remote,
                min_exp=exp_range[0],
                max_exp=exp_range[1],
            )
            st.session_state.search_results = results
            st.session_state.api_errors = api_errors
            st.session_state.matches = {}

        for err in st.session_state.get("api_errors", []):
            if st.session_state.search_results:
                st.info(f"ℹ️ {err}")
            else:
                st.warning(f"⚠️ {err}")

        if not results:
            st.warning("No se encontraron ofertas con esos filtros. Prueba a ampliarlos.")
        else:
            chain = create_job_matching_chain()
            progress = st.progress(0)
            status = st.empty()
            matches: dict = {}
            skills = profile.get("technical_skills") or profile.get("skills", [])

            for i, job in enumerate(results):
                status.text(f"Analizando: {job['title']} @ {job['company']}…")
                try:
                    match_obj = chain.invoke({
                        "current_title": profile.get("current_title", ""),
                        "years_in_current_role": profile.get("years_in_current_role", 0),
                        "technical_skills": ", ".join(skills),
                        "recent_experience": _recent_experience_summary(profile),
                        "job_title": job["title"],
                        "company": job["company"],
                        "required_skills": ", ".join(job["required_skills"]),
                        "experience_min": job["experience_min"],
                        "experience_max": job["experience_max"],
                        "description": job["description"][:600],
                    })
                    matches[job["id"]] = match_obj.model_dump()
                except Exception as exc:
                    matches[job["id"]] = {
                        "score": 0,
                        "matching_skills": [],
                        "missing_skills": [],
                        "explanation": f"Error: {exc}",
                    }
                progress.progress((i + 1) / len(results))

            status.empty()
            progress.empty()
            st.session_state.matches = matches

    results = st.session_state.search_results
    matches = st.session_state.matches

    if results:
        sorted_results = sorted(
            results,
            key=lambda j: matches.get(j["id"], {}).get("score", 0),
            reverse=True,
        )

        st.divider()
        st.subheader(f"{len(results)} oferta{'s' if len(results) != 1 else ''} encontrada{'s' if len(results) != 1 else ''}")

        for job in sorted_results:
            match = matches.get(job["id"], {})
            score = match.get("score", 0)

            badge = "🟢" if score >= 70 else ("🟡" if score >= 40 else "🔴")
            is_truly_remote = job.get("location", "").lower().strip() == "remote"
            remote_tag = "  🌐 100% Remoto" if is_truly_remote else ("  🏠 Híbrido" if job.get("remote") else "")
            source = job.get("source", "")
            source_badge = f"  `{source}`" if source else ""
            header = f"{badge} {score} %  —  **{job['title']}** · {job['company']} · {job['location']}{remote_tag}{source_badge}"

            with st.expander(header):
                left, right = st.columns([3, 2])

                with left:
                    st.markdown(
                        f"**{job['title']}** — {job['company']}  \n"
                        f"📍 {job['location']}{remote_tag}  \n"
                        f"💰 {job['salary_range']}  ·  📄 {job['contract_type']}  \n"
                        f"🕐 {job['experience_min']}–{job['experience_max']} años de experiencia"
                    )
                    st.markdown(job["description"])
                    st.markdown("**Habilidades requeridas:** " + "  ".join(f"`{s}`" for s in job["required_skills"]))
                    if job.get("nice_to_have"):
                        st.markdown("**Valorables:** " + "  ".join(f"`{s}`" for s in job["nice_to_have"]))
                    st.link_button("Ver oferta completa ↗", job["url"])

                with right:
                    st.metric("Compatibilidad", f"{score} %")
                    st.progress(score / 100)
                    if match.get("explanation"):
                        st.info(match["explanation"])
                    if match.get("matching_skills"):
                        st.markdown("**✅ Coincidencias:**")
                        for s in match["matching_skills"]:
                            st.markdown(f"- {s}")
                    if match.get("missing_skills"):
                        st.markdown("**❌ Te faltan:**")
                        for s in match["missing_skills"]:
                            st.markdown(f"- {s}")
