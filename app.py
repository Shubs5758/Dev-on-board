"""
DevOnboard - AI-powered developer onboarding copilot
Main Streamlit application
"""

import os
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List

import streamlit as st

import utils
import agents
import graph_builder
from llm_client import get_provider_badge


# Page configuration
st.set_page_config(
    page_title="DevOnboard",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Global CSS styles
st.markdown("""
<style>
/* Card component */
.dob-card {
    background: white;
    border: 1px solid #e8e6f0;
    border-radius: 16px;
    padding: 20px 24px;
    margin-bottom: 16px;
    box-shadow: 0 2px 8px rgba(127,119,221,0.07);
}

/* Metric card */
.dob-metric {
    background: linear-gradient(135deg, #f8f7ff 0%, #f0eeff 100%);
    border: 1px solid #d4d0f5;
    border-radius: 12px;
    padding: 16px 20px;
    text-align: center;
}
.dob-metric .label {
    font-size: 12px;
    color: #888780;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 4px;
}
.dob-metric .value {
    font-size: 28px;
    font-weight: 700;
    color: #3C3489;
}
.dob-metric .sub {
    font-size: 12px;
    color: #7F77DD;
}

/* Phase badge */
.phase-badge {
    display: inline-block;
    background: #7F77DD;
    color: white;
    border-radius: 20px;
    padding: 4px 14px;
    font-size: 12px;
    font-weight: 600;
    margin-bottom: 8px;
}

/* File pill */
.file-pill {
    display: inline-block;
    background: #f0eeff;
    color: #534AB7;
    border-radius: 6px;
    padding: 2px 10px;
    font-size: 12px;
    font-family: monospace;
    margin: 2px;
}

/* Tech badge */
.tech-badge {
    display: inline-block;
    background: #e8f4fd;
    color: #185FA5;
    border: 1px solid #b5d4f4;
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 13px;
    margin: 3px;
}

/* Starter question button */
.stButton > button {
    border-radius: 12px !important;
    border: 1px solid #d4d0f5 !important;
    background: white !important;
    color: #3C3489 !important;
    text-align: left !important;
    padding: 12px 16px !important;
    font-size: 14px !important;
    width: 100% !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    background: #f0eeff !important;
    border-color: #7F77DD !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(127,119,221,0.15) !important;
}

/* Progress bar override */
.stProgress > div > div > div { background-color: #7F77DD; }

/* Tab styling */
.stTabs [data-baseweb="tab"] {
    font-size: 14px;
    font-weight: 500;
}
.stTabs [aria-selected="true"] {
    color: #7F77DD;
}

/* Sidebar card */
.sidebar-card {
    background: #f8f7ff;
    border: 1px solid #d4d0f5;
    border-radius: 12px;
    padding: 14px 16px;
    margin: 8px 0;
}

/* Success banner */
.success-banner {
    background: linear-gradient(135deg, #7F77DD 0%, #534AB7 100%);
    color: white;
    border-radius: 16px;
    padding: 20px 24px;
    margin-bottom: 24px;
    display: flex;
    align-items: center;
    gap: 16px;
}
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize all session state variables."""
    defaults = {
        "repo_url": "",
        "role": "Full-Stack Developer",
        "experience": "Mid (2–5 yrs)",
        "parsed_files": [],
        "project_summary": {},
        "file_summaries": {},
        "onboarding_phases": [],
        "task_completion": {},
        "graph_html_files": "",
        "graph_html_functions": "",
        "graph_metrics": {},
        "chat_history": [],
        "analysis_complete": False,
        "repo_metadata": {},
        "demo_mode": False
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def validate_secrets() -> tuple:
    """Returns (is_valid, error_message)"""
    missing = []
    for key in ["IBM_API_KEY", "IBM_PROJECT_ID"]:
        if not st.secrets.get(key) or "your-" in st.secrets.get(key, ""):
            missing.append(key)
    if missing:
        return False, f"Missing IBM watsonx credentials: {', '.join(missing)}"
    return True, ""


def render_sidebar():
    """Render sidebar with controls."""
    st.sidebar.title("🧭 DevOnboard")
    st.sidebar.markdown("*AI-powered codebase onboarding*")
    st.sidebar.divider()
    
    # Show AI model info
    st.sidebar.markdown('''
    <div style="background:#f0f4ff;border:1px solid #a0b4f4;border-radius:10px;
                padding:10px 14px;font-size:12px;color:#1a3a8f;margin-bottom:16px">
        <b>🔷 IBM Granite</b><br>
        Enterprise-grade · Code-optimised · IBM watsonx
    </div>
    ''', unsafe_allow_html=True)
    
    # GitHub URL input
    repo_url = st.sidebar.text_input(
        "GitHub Repository URL",
        value=st.session_state.repo_url,
        placeholder="https://github.com/username/repo",
        help="Enter a public GitHub repository URL"
    )
    
    # Role selection
    role = st.sidebar.selectbox(
        "Your Role",
        [
            "Frontend Developer",
            "Backend Developer",
            "Full-Stack Developer",
            "DevOps Engineer",
            "ML/Data Engineer",
            "General / Explore"
        ],
        index=2
    )
    
    # Experience level
    experience = st.sidebar.radio(
        "Experience Level",
        ["Junior (0–2 yrs)", "Mid (2–5 yrs)", "Senior (5+ yrs)"],
        index=1
    )
    
    # Start button
    start_button = st.sidebar.button("🚀 Start Onboarding", type="primary", use_container_width=True)
    
    # Demo mode button
    if not st.session_state.analysis_complete:
        if st.sidebar.button("📺 Load Demo", use_container_width=True):
            load_demo_mode()
    
    st.sidebar.divider()
    
    # Show metadata if analysis complete
    if st.session_state.analysis_complete and st.session_state.repo_metadata:
        render_repo_metadata()
    
    # Handle start button
    if start_button and repo_url:
        st.session_state.repo_url = repo_url
        st.session_state.role = role
        st.session_state.experience = experience
        run_analysis(repo_url, role, experience)


def render_repo_metadata():
    """Render repository metadata card in sidebar."""
    metadata = st.session_state.repo_metadata
    
    st.sidebar.markdown("### 📊 Repository Info")
    
    # Repo name
    st.sidebar.markdown(f"**{metadata.get('repo_name', 'Unknown')}**")
    
    # Metrics
    col1, col2 = st.sidebar.columns(2)
    with col1:
        st.metric("Files", metadata.get('total_files', 0))
    with col2:
        st.metric("Lines", metadata.get('total_lines', 0))
    
    # Primary language
    st.sidebar.markdown(f"**Language:** {metadata.get('primary_language', 'Mixed')}")
    
    # Health badge
    health = metadata.get('health_score', 'Moderate complexity')
    health_colors = {
        'Well-structured': '🟢',
        'Moderate complexity': '🟡',
        'Complex codebase': '🔴'
    }
    badge = health_colors.get(health, '🟡')
    st.sidebar.markdown(f"{badge} {health}")
    
    st.sidebar.divider()
    
    # Progress with styled card
    if st.session_state.onboarding_phases:
        total_tasks = sum(len(phase['tasks']) for phase in st.session_state.onboarding_phases)
        completed_tasks = sum(1 for task_id, done in st.session_state.task_completion.items() if done)
        progress_pct = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        # Styled progress card
        st.sidebar.markdown(f'''
        <div class="sidebar-card">
            <div style="font-size:12px;color:#888;margin-bottom:6px">ONBOARDING PROGRESS</div>
            <div style="font-size:24px;font-weight:700;color:#3C3489">{int(progress_pct)}%</div>
            <div style="font-size:12px;color:#888">{completed_tasks} of {total_tasks} tasks complete</div>
        </div>
        ''', unsafe_allow_html=True)
        
        st.sidebar.progress(progress_pct / 100)
        
        # Phase completion summary
        for i, phase in enumerate(st.session_state.onboarding_phases):
            phase_tasks = phase.get('tasks', [])
            phase_done = sum(1 for t in phase_tasks if st.session_state.task_completion.get(t.get('id', ''), False))
            phase_total = len(phase_tasks)
            bar_pct = phase_done / phase_total if phase_total else 0
            
            st.sidebar.markdown(f'''
            <div style="display:flex;justify-content:space-between;
                        font-size:12px;color:#888;margin:4px 0">
                <span>Phase {i+1}</span>
                <span>{phase_done}/{phase_total}</span>
            </div>
            ''', unsafe_allow_html=True)
            st.sidebar.progress(bar_pct)


def run_analysis(repo_url: str, role: str, experience: str):
    """Run the full analysis pipeline."""
    # Create temp directory
    repo_hash = utils.get_repo_hash(repo_url)
    tmp_dir = os.path.join(tempfile.gettempdir(), f"devonboard_{repo_hash}")
    
    # Progress tracking
    progress_bar = st.sidebar.progress(0)
    status_text = st.sidebar.empty()
    
    try:
        # Step 1: Clone repository
        status_text.text("🔄 Cloning repository...")
        progress_bar.progress(10)
        
        clone_result = agents.agent_clone_repo(repo_url, tmp_dir)
        
        if not clone_result['clone_success']:
            st.error(f"❌ {clone_result['error_message']}")
            return
        
        # Step 2: Parse files
        status_text.text("📂 Parsing files...")
        progress_bar.progress(25)
        
        parsed_files = agents.agent_parse_files(clone_result['local_path'], role)
        
        if not parsed_files:
            st.error("❌ No supported files found in this repository.")
            return
        
        st.session_state.parsed_files = parsed_files
        
        # Step 3: Analyze files with AI (limit to top 30)
        files_to_analyze = parsed_files[:30]
        file_summaries = {}
        
        for i, file_info in enumerate(files_to_analyze):
            status_text.text(f"🤖 Analyzing file {i+1}/{len(files_to_analyze)}...")
            progress_bar.progress(25 + int((i / len(files_to_analyze)) * 40))
            
            summary = agents.agent_summarize_file(
                file_info,
                f"Repository: {clone_result['repo_name']}"
            )
            file_summaries[file_info['path']] = summary
        
        st.session_state.file_summaries = file_summaries
        
        # Step 4: Generate project summary
        status_text.text("📝 Generating project summary...")
        progress_bar.progress(70)
        
        project_summary = agents.agent_generate_project_summary(
            list(file_summaries.values()),
            clone_result['repo_name'],
            role,
            experience
        )
        st.session_state.project_summary = project_summary
        
        # Step 5: Generate onboarding path
        status_text.text("🗺️ Creating onboarding path...")
        progress_bar.progress(80)
        
        onboarding_phases = agents.agent_generate_onboarding_path(
            project_summary,
            parsed_files,
            role,
            experience
        )
        st.session_state.onboarding_phases = onboarding_phases
        
        # Step 6: Build graphs
        status_text.text("📊 Building dependency graphs...")
        progress_bar.progress(90)
        
        graph_html_files = graph_builder.build_file_graph(parsed_files, role)
        graph_html_functions = graph_builder.build_function_graph(parsed_files)
        graph_metrics = graph_builder.analyse_graph_metrics(parsed_files)
        
        st.session_state.graph_html_files = graph_html_files
        st.session_state.graph_html_functions = graph_html_functions
        st.session_state.graph_metrics = graph_metrics
        
        # Step 7: Calculate metadata
        status_text.text("✅ Finalizing...")
        progress_bar.progress(100)
        
        # Calculate language breakdown
        language_counts = {}
        total_lines = 0
        for f in parsed_files:
            lang = f['language']
            lines = f['lines']
            language_counts[lang] = language_counts.get(lang, 0) + lines
            total_lines += lines
        
        primary_language = max(language_counts.items(), key=lambda x: x[1])[0] if language_counts else "Unknown"
        
        st.session_state.repo_metadata = {
            'repo_name': clone_result['repo_name'],
            'total_files': len(parsed_files),
            'total_lines': total_lines,
            'primary_language': primary_language,
            'language_breakdown': language_counts,
            'health_score': project_summary.get('health_score', 'Moderate complexity')
        }
        
        st.session_state.analysis_complete = True
        
        # Clear progress
        progress_bar.empty()
        status_text.empty()
        
        st.sidebar.success("✅ Analysis complete!")
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Error during analysis: {str(e)}")
        progress_bar.empty()
        status_text.empty()


def load_demo_mode():
    """Load demo mode with pre-populated data."""
    st.session_state.demo_mode = True
    st.session_state.repo_url = "https://github.com/streamlit/streamlit-example"
    st.session_state.role = "Full-Stack Developer"
    st.session_state.experience = "Mid (2–5 yrs)"
    
    # Simulate analysis
    run_analysis(
        "https://github.com/streamlit/streamlit-example",
        "Full-Stack Developer",
        "Mid (2–5 yrs)"
    )


def render_overview_tab():
    """Render the Overview tab."""
    if not st.session_state.analysis_complete:
        st.info("👈 Enter a GitHub repository URL in the sidebar to get started!")
        return
    
    summary = st.session_state.project_summary
    metadata = st.session_state.repo_metadata
    
    # Success banner
    repo_name = metadata.get('repo_name', 'Repository')
    total_files = metadata.get('total_files', 0)
    primary_lang = metadata.get('primary_language', 'Unknown')
    health_score = metadata.get('health_score', 'Moderate complexity')
    
    health_badges = {
        'Well-structured': '🟢 Well-structured',
        'Moderate complexity': '🟡 Moderate complexity',
        'Complex codebase': '🔴 Complex codebase'
    }
    health_badge = health_badges.get(health_score, '🟡 Moderate complexity')
    
    st.markdown(f'''
    <div class="success-banner">
        <div style="font-size:36px">✅</div>
        <div>
            <div style="font-size:18px;font-weight:700">Analysis Complete — {repo_name}</div>
            <div style="opacity:0.85;font-size:14px">{total_files} files analysed · {primary_lang} · {health_badge}</div>
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    # Project summary
    st.markdown("## 📖 Project Summary")
    st.markdown(summary.get('project_overview', 'No overview available.'))
    
    st.divider()
    
    # Key metrics with styled cards
    st.markdown("## 📊 Key Metrics")
    col1, col2, col3, col4 = st.columns(4)
    
    total_lines = metadata.get('total_lines', 0)
    avg_complexity = sum(f.get('complexity_score', 1) for f in st.session_state.parsed_files) / len(st.session_state.parsed_files) if st.session_state.parsed_files else 0
    
    with col1:
        st.markdown(f'''
        <div class="dob-metric">
            <div class="label">Total Files</div>
            <div class="value">{total_files}</div>
            <div class="sub">Analyzed</div>
        </div>
        ''', unsafe_allow_html=True)
    
    with col2:
        st.markdown(f'''
        <div class="dob-metric">
            <div class="label">Total Lines</div>
            <div class="value">{total_lines:,}</div>
            <div class="sub">Of Code</div>
        </div>
        ''', unsafe_allow_html=True)
    
    with col3:
        st.markdown(f'''
        <div class="dob-metric">
            <div class="label">Primary Language</div>
            <div class="value" style="font-size:22px">{primary_lang}</div>
            <div class="sub">Main Tech</div>
        </div>
        ''', unsafe_allow_html=True)
    
    with col4:
        st.markdown(f'''
        <div class="dob-metric">
            <div class="label">Avg Complexity</div>
            <div class="value">{avg_complexity:.1f}<span style="font-size:18px">/5</span></div>
            <div class="sub">Difficulty</div>
        </div>
        ''', unsafe_allow_html=True)
    
    st.divider()
    
    # Tech stack with badges
    tech_stack = summary.get('tech_stack', [])
    if tech_stack:
        st.markdown("## 💻 Tech Stack")
        tech_badges_html = ''.join([f'<span class="tech-badge">{tech}</span>' for tech in tech_stack])
        st.markdown(tech_badges_html, unsafe_allow_html=True)
        st.divider()
    
    # Files to read first with styled cards
    st.markdown("## 📚 Files to Read First")
    files_to_read = summary.get('files_to_read_first', [])
    
    if files_to_read:
        for i, file_info in enumerate(files_to_read[:5], 1):
            file_name = file_info.get('file', 'Unknown')
            reason = file_info.get('reason', 'Important file')
            
            col_left, col_right = st.columns([0.4, 0.6])
            
            with col_left:
                st.markdown(f'''
                <div class="dob-card" style="display:flex;align-items:center;gap:12px">
                    <div style="font-size:24px;font-weight:700;color:#7F77DD">{i}</div>
                    <div>
                        <span class="file-pill">{file_name}</span>
                    </div>
                </div>
                ''', unsafe_allow_html=True)
            
            with col_right:
                st.markdown(f'''
                <div class="dob-card">
                    <div style="font-size:13px;color:#555">{reason}</div>
                </div>
                ''', unsafe_allow_html=True)
    else:
        st.info("No specific files recommended yet.")
    
    st.divider()
    
    # Architecture observations with styled cards
    st.markdown("## 🏗️ Architecture at a Glance")
    observations = summary.get('key_observations', [])
    if observations:
        for obs in observations:
            st.markdown(f'''
            <div class="dob-card" style="border-left:4px solid #7F77DD">
                <div style="font-size:14px;color:#2C2C2A">{obs}</div>
            </div>
            ''', unsafe_allow_html=True)
    else:
        st.info("No architecture observations available.")


def render_onboarding_tab():
    """Render the Onboarding Path tab."""
    if not st.session_state.analysis_complete:
        st.info("👈 Start analysis to see your personalized onboarding path!")
        return
    
    st.markdown("## 🗺️ Your Personalized Onboarding Journey")
    st.markdown(f"*Tailored for: {st.session_state.role} • {st.session_state.experience}*")
    
    st.divider()
    
    phases = st.session_state.onboarding_phases
    
    if not phases:
        st.warning("No onboarding path generated yet.")
        return
    
    # Phase progress stepper
    phases_labels = ["🧭 Orientation", "🔍 Core Understanding", "🏊 Deep Dive", "🚀 First Contribution"]
    cols = st.columns(4)
    
    for i, (col, label) in enumerate(zip(cols, phases_labels)):
        if i < len(phases):
            phase_tasks = phases[i].get('tasks', [])
            completed = sum(1 for t in phase_tasks if st.session_state.task_completion.get(t.get('id', ''), False))
            total = len(phase_tasks)
            is_active = completed > 0 and completed < total
            is_done = completed == total
            
            bg = "#7F77DD" if is_done else ("#f0eeff" if is_active else "#f8f8f8")
            color = "white" if is_done else ("#3C3489" if is_active else "#888")
            border_color = "#7F77DD" if (is_active or is_done) else "#eee"
            
            col.markdown(f'''
            <div style="background:{bg};color:{color};border-radius:12px;padding:12px;text-align:center;
                        border:1px solid {border_color}">
                <div style="font-size:18px">{label.split()[0]}</div>
                <div style="font-size:12px;font-weight:500">{" ".join(label.split()[1:])}</div>
                <div style="font-size:11px;margin-top:4px">{completed}/{total} done</div>
            </div>
            ''', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Render phases with styled headers
    for i, phase in enumerate(phases):
        phase_name = phase.get('phase_name', 'Phase')
        phase_subtitle = phase.get('phase_subtitle', '')
        
        # Styled phase header
        st.markdown(f'''
        <div style="display:flex;align-items:center;gap:12px;margin:24px 0 8px">
            <span class="phase-badge">Phase {i+1}</span>
            <span style="font-size:20px;font-weight:700;color:#2C2C2A">{phase_name}</span>
            <span style="font-size:13px;color:#888;margin-left:auto">{phase_subtitle}</span>
        </div>
        ''', unsafe_allow_html=True)
        
        tasks = phase.get('tasks', [])
        
        for task in tasks:
            task_id = task.get('id', '')
            task_text = task.get('task', '')
            why = task.get('why', '')
            file_ref = task.get('file_ref', '')
            minutes = task.get('estimated_minutes', 0)
            
            # Checkbox for task completion
            is_complete = st.session_state.task_completion.get(task_id, False)
            
            col1, col2 = st.columns([0.05, 0.95])
            
            with col1:
                if st.checkbox("✓", value=is_complete, key=f"check_{task_id}", label_visibility="hidden"):
                    st.session_state.task_completion[task_id] = True
                else:
                    st.session_state.task_completion[task_id] = False
            
            with col2:
                st.markdown(f"**{task_text}**")
                if file_ref:
                    st.caption(f"📄 `{file_ref}` • ⏱️ ~{minutes} min")
                else:
                    st.caption(f"⏱️ ~{minutes} min")
                
                # Why this matters
                with st.expander("💡 Why this matters"):
                    st.markdown(why)
        
        st.divider()
    
    # Custom task generator
    st.markdown("### ➕ Generate Custom Task")
    custom_task = st.text_input("What would you like to learn or do?", placeholder="e.g., Understand the authentication flow")
    
    if st.button("Generate Task") and custom_task:
        st.info("🤖 Custom task generation coming soon!")


def render_graph_tab():
    """Render the Codebase Graph tab."""
    if not st.session_state.analysis_complete:
        st.info("👈 Start analysis to visualize the codebase structure!")
        return
    
    st.markdown("## 🕸️ Interactive Codebase Visualization")
    
    # Graph selector
    graph_type = st.radio(
        "Select Graph Type",
        ["File Dependency Graph", "Function Call Graph"],
        horizontal=True
    )
    
    st.divider()
    
    # Render selected graph
    if graph_type == "File Dependency Graph":
        st.markdown("### 📁 File Dependency Graph")
        
        # Color legend with styled badges
        st.markdown('''
        <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px">
            <span style="background:#1D9E75;color:white;border-radius:20px;padding:3px 12px;font-size:12px">⬤ Entry points</span>
            <span style="background:#378ADD;color:white;border-radius:20px;padding:3px 12px;font-size:12px">⬤ Core modules</span>
            <span style="background:#EF9F27;color:white;border-radius:20px;padding:3px 12px;font-size:12px">⬤ Utilities</span>
            <span style="background:#E24B4A;color:white;border-radius:20px;padding:3px 12px;font-size:12px">⬤ Config</span>
            <span style="background:#888780;color:white;border-radius:20px;padding:3px 12px;font-size:12px">⬤ Tests</span>
        </div>
        ''', unsafe_allow_html=True)
        
        if st.session_state.graph_html_files:
            # Use components.html for backward compatibility
            import streamlit.components.v1 as components
            components.html(st.session_state.graph_html_files, height=600, scrolling=True)
        else:
            st.warning("Graph not available.")
    
    else:
        st.markdown("### ⚙️ Function Call Graph")
        st.caption("Shows function-level dependencies • 🟡 Amber = most-called functions")
        
        if st.session_state.graph_html_functions:
            # Use components.html for backward compatibility
            import streamlit.components.v1 as components
            components.html(st.session_state.graph_html_functions, height=600, scrolling=True)
        else:
            st.warning("Graph not available.")
    
    st.divider()
    
    # Graph insights with styled cards
    st.markdown("### 🔍 Graph Insights")
    metrics = st.session_state.graph_metrics
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="dob-card">', unsafe_allow_html=True)
        st.markdown("**🔗 Hub Files** (Most Imported)")
        hub_files = metrics.get('hub_files', [])
        if hub_files:
            for hub in hub_files[:3]:
                st.markdown(f'''
                <div style="background:#f8f7ff;border-radius:8px;padding:10px;margin:8px 0">
                    <div style="font-family:monospace;font-size:13px;color:#534AB7;font-weight:600">{hub['name']}</div>
                    <div style="font-size:12px;color:#7F77DD;margin-top:4px">{hub['import_count']} imports</div>
                    <div style="font-size:12px;color:#666;margin-top:4px">{hub['reason']}</div>
                </div>
                ''', unsafe_allow_html=True)
        else:
            st.caption("No hub files detected.")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="dob-card">', unsafe_allow_html=True)
        st.markdown("**⚠️ Isolated Files** (No Connections)")
        isolated = metrics.get('isolated_files', [])
        if isolated:
            st.markdown('<div style="background:#fff9f0;border-radius:8px;padding:10px;margin:8px 0">', unsafe_allow_html=True)
            for iso in isolated[:5]:
                st.markdown(f'<div style="font-family:monospace;font-size:12px;color:#666;margin:4px 0">• {iso["name"]}</div>', unsafe_allow_html=True)
            if len(isolated) > 5:
                st.caption(f"...and {len(isolated) - 5} more")
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('<div style="font-size:12px;color:#888;margin-top:8px">💡 These files might be entry points, standalone scripts, or need better integration.</div>', unsafe_allow_html=True)
        else:
            st.caption("All files are connected!")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Circular dependencies
    circular = metrics.get('circular_deps', [])
    if circular:
        st.warning("**⚠️ Circular Dependencies Detected**")
        for circ in circular[:3]:
            st.markdown(f"- {circ['description']}")


def render_chat_tab():
    """Render the Chat Copilot tab."""
    if not st.session_state.analysis_complete:
        st.info("👈 Start analysis to chat with your AI copilot!")
        return
    
    st.markdown("## 💬 Chat with Your AI Copilot")
    
    # Copilot ready banner
    st.markdown('''
    <div style="background:#f0eeff;border:1px solid #d4d0f5;border-radius:12px;
                padding:14px 18px;margin-bottom:16px;display:flex;
                align-items:center;gap:12px">
        <span style="font-size:24px">🤖</span>
        <div>
            <div style="font-weight:600;color:#3C3489">Your AI Copilot is ready</div>
            <div style="font-size:13px;color:#888">Ask anything about this codebase —
            I know every file, function, and pattern.</div>
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    # Show starter questions if no chat history
    if not st.session_state.chat_history:
        st.markdown("### 🎯 Starter Questions")
        
        icons = ["🚀", "🔐", "🗄️", "🎯", "📐", "⚠️"]
        starter_questions = [
            "Walk me through how the app starts",
            "How does authentication work here?",
            "What's the database structure?",
            f"Where should I make changes for {st.session_state.role}?",
            "What are the main coding patterns used?",
            "What are the biggest risks or debt in this codebase?"
        ]
        
        cols = st.columns(2)
        for i, (icon, question) in enumerate(zip(icons, starter_questions)):
            with cols[i % 2]:
                if st.button(f"{icon} {question}", key=f"starter_{i}", use_container_width=True):
                    # Add to chat
                    st.session_state.chat_history.append({
                        "role": "user",
                        "content": question
                    })
                    
                    # Get response
                    repo_context = {
                        'repo_name': st.session_state.repo_metadata.get('repo_name', ''),
                        'project_overview': st.session_state.project_summary.get('project_overview', ''),
                        'tech_stack': st.session_state.project_summary.get('tech_stack', []),
                        'file_list': [f['path'] for f in st.session_state.parsed_files[:20]]
                    }
                    
                    response = agents.agent_chat(
                        question,
                        repo_context,
                        st.session_state.chat_history[:-1],
                        st.session_state.role
                    )
                    
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": response
                    })
                    
                    st.rerun()
        
        st.divider()
    
    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if user_input := st.chat_input("Ask about the codebase..."):
        # Add user message
        st.session_state.chat_history.append({
            "role": "user",
            "content": user_input
        })
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(user_input)
        
        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                repo_context = {
                    'repo_name': st.session_state.repo_metadata.get('repo_name', ''),
                    'project_overview': st.session_state.project_summary.get('project_overview', ''),
                    'tech_stack': st.session_state.project_summary.get('tech_stack', []),
                    'file_list': [f['path'] for f in st.session_state.parsed_files[:20]]
                }
                
                response = agents.agent_chat(
                    user_input,
                    repo_context,
                    st.session_state.chat_history[:-1],
                    st.session_state.role
                )
                
                st.markdown(response)
                
                # Add assistant message
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": response
                })


def main():
    """Main application entry point."""
    # Initialize
    initialize_session_state()
    
    # Validate IBM watsonx credentials
    valid, err = validate_secrets()
    if not valid:
        st.sidebar.error(f"🔑 {err}")
        st.stop()
    
    # Render sidebar
    render_sidebar()
    
    # Main content area with provider badge
    st.title("🧭 DevOnboard")
    st.markdown(
        f"*Your AI copilot for intelligent codebase onboarding · {get_provider_badge()}*",
        unsafe_allow_html=True
    )
    
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📖 Overview",
        "🗺️ Onboarding Path",
        "🕸️ Codebase Graph",
        "💬 Chat Copilot"
    ])
    
    with tab1:
        render_overview_tab()
    
    with tab2:
        render_onboarding_tab()
    
    with tab3:
        render_graph_tab()
    
    with tab4:
        render_chat_tab()
    
    # Footer
    st.divider()
    st.markdown(
        "<div style='text-align: center; color: #888; font-size: 0.9em;'>"
        "Powered by IBM Granite · Built for developers"
        "</div>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()

# Made with Bob
