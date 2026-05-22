# 🧭 DevOnboard
AI-Powered Developer Onboarding Copilot

DevOnboard is an intelligent AI copilot that analyzes any GitHub repository and creates a personalized onboarding experience for developers. By leveraging **IBM Granite 4H Small** via watsonx.ai, it combines enterprise-grade AI code analysis, interactive visualizations, and conversational assistance to help developers understand and contribute to new codebases faster.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)
![IBM Granite](https://img.shields.io/badge/IBM-Granite_4H_Small-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

---

## 🎯 Problem Statement

Onboarding to a new codebase is one of the most painful experiences in software development:

- **Information Overload**: Large repositories with hundreds of files are overwhelming
- **No Onboarding Path**: Most projects have no structured guide for new developers
- **Context Switching**: Developers spend days navigating code just to understand the basics
- **Role Blindness**: A frontend developer and a DevOps engineer need completely different starting points
- **Knowledge Gaps**: Understanding key flows and module relationships takes significant time

DevOnboard solves this by providing instant, AI-powered, role-specific onboarding — reducing ramp-up time from days to hours.

---

## ✨ Key Features

- 🤖 **IBM Granite AI** - Powered by IBM Granite 4H Small via watsonx.ai for enterprise-grade code analysis
- 🗺️ **Personalized Onboarding Paths** - Role-specific learning journeys (Frontend, Backend, DevOps, etc.)
- 🕸️ **Interactive Graphs** - Visual dependency maps and function call graphs
- 💬 **Chat Copilot** - Ask questions about the codebase and get intelligent answers
- 📊 **Progress Tracking** - Track your onboarding journey with checklists
- 🎯 **Smart File Prioritization** - Know which files to read first based on your role

---

## 🖼️ Screenshots

### 📖 Overview — Project Summary & Key Metrics
![Overview Tab](screenshots/overview.png)
> Analysis complete banner, project summary powered by IBM Granite, key metrics and files to read first prioritized by role.

---

### 🗺️ Onboarding Path — Personalized Learning Journey
![Onboarding Path Tab](screenshots/onboarding_path.png)
> 4-phase onboarding journey tailored to your role and experience level, with interactive checklists and "Why this matters" explanations.

---

### 🕸️ Codebase Graph — Interactive Dependency Visualization
![Codebase Graph Tab](screenshots/graph.png)
> Function call graph and file dependency graph with hub files, isolated files, and graph insights powered by NetworkX + PyVis.

---

### 💬 Chat Copilot — Ask Anything About the Codebase
![Chat Copilot Tab](screenshots/chat.png)
> IBM Granite-powered chat that knows every file, function, and pattern in the repository — with detailed, grounded answers.

---

## 🤖 AI Model

DevOnboard uses **IBM Granite 4H Small** from IBM watsonx.ai — an enterprise-grade, code-optimized language model specifically designed for software development tasks.

### Why IBM Granite?

- ✅ **Enterprise-grade** - Built for production use
- ✅ **Code-optimized** - Trained specifically on code and technical documentation
- ✅ **Cost-efficient** - $0.06/1M input tokens · $0.25/1M output tokens
- ✅ **Secure** - IBM watsonx.ai provides enterprise security and compliance
- ✅ **Accurate** - Superior performance on code analysis tasks

---

## 🛠️ Tech Stack

### Backend
- **Streamlit** — UI framework and application server
- **GitPython** — Repository cloning and file extraction
- **python-dotenv** — Environment variable management

### AI/ML
- **IBM watsonx.ai** — Enterprise AI platform
- **IBM Granite 4H Small** — Latest, most cost-efficient Granite model
  - Model ID: `ibm/granite-4-h-small`
  - Price: $0.06/1M input tokens · $0.25/1M output tokens

### Code Analysis
- **Python AST** — Function, class, and import extraction
- **NetworkX + PyVis** — Graph construction and interactive visualization
- **Regex Patterns** — Import extraction for JS, TS, Go, Java, and more

---

## 🚀 Setup Instructions

### Prerequisites
- Python 3.10 or higher
- Git installed on your system
- IBM Cloud account with watsonx.ai access

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/devonboard.git
cd devonboard
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Credentials

Create `.streamlit/secrets.toml` in the project root:

```toml
IBM_API_KEY = "your_ibm_cloud_api_key"
IBM_PROJECT_ID = "your_watsonx_project_id"
IBM_URL = "https://eu-de.ml.cloud.ibm.com"
```

To get your credentials:

1. Sign up at [IBM watsonx](https://www.ibm.com/watsonx)
2. Go to `dataplatform.cloud.ibm.com/wx/home?context=wx`
3. Create a project → **Manage** tab → copy the **Project ID**
4. Go to `cloud.ibm.com/iam/apikeys` → create and copy your **API Key**
5. Set the **URL** based on your region:

| Region | URL |
|--------|-----|
| US (Dallas) | `https://us-south.ml.cloud.ibm.com` |
| EU (Frankfurt) | `https://eu-de.ml.cloud.ibm.com` |
| UK (London) | `https://eu-gb.ml.cloud.ibm.com` |
| Asia Pacific (Tokyo) | `https://jp-tok.ml.cloud.ibm.com` |

> ⚠️ **Important**: Your `IBM_URL` region must match the region of your watsonx.ai Runtime service. Mismatched regions cause 404 errors.

### 4. Run the Application
```bash
streamlit run app.py
```

The app will be available at `http://localhost:8501`

---

## 📖 How to Use

### Step 1: Enter Repository Details
1. Paste a **public GitHub repository URL** in the sidebar
2. Select your **developer role** (Frontend, Backend, Full-Stack, DevOps, ML/Data, or General)
3. Choose your **experience level** (Junior, Mid, or Senior)
4. Click **"🚀 Start Onboarding"**

### Step 2: Explore the Analysis

DevOnboard will analyze the repository using IBM Granite and present four interactive tabs:

#### 📖 Overview Tab
- Project summary and architecture overview
- Key metrics (files, lines of code, complexity)
- Technology stack breakdown
- Files to read first — prioritized for your role

#### 🗺️ Onboarding Path Tab
- 4-phase personalized learning journey
- Interactive checklist with progress tracking
- "Why this matters" explanations per task
- Estimated time for each task
- Generate custom tasks for anything extra you want to learn

#### 🕸️ Codebase Graph Tab
- Switch between File Dependency and Function Call graphs
- Hub files and isolated files analysis
- Circular dependency warnings
- Graph insights panel

#### 💬 Chat Copilot Tab
- Ask anything about the codebase
- IBM Granite-powered answers with file references
- Starter questions to get you going
- Full conversation history maintained

### Step 3: Track Your Progress
- Check off tasks as you complete them
- Watch your progress percentage update in the sidebar
- Use the chat to ask follow-up questions at any time

---

## 🤖 How IBM Bob Was Used in Development

DevOnboard was built with the assistance of IBM Bob, an AI-powered development copilot. Bob helped accelerate development through:

### 1. Architecture Planning
- Designed the agentic multi-agent architecture (repo analyst, path planner, code guide, chat agent)
- Planned the role-aware file prioritization system for efficient repository analysis
- Structured the watsonx.ai integration strategy with IBM Granite 4H Small

### 2. Code Implementation
- `agents.py`: Implemented all AI agent functions for summarization, onboarding path generation, and chat
- `llm_client.py`: Created the unified LLM abstraction layer routing calls to IBM Granite
- `graph_builder.py`: Built the NetworkX + PyVis graph logic for file and function visualization
- `ast_parser.py`: Developed AST-based code structure extraction for Python files
- `app.py`: Built the complete Streamlit UI with 4 tabs, sidebar controls, and session state management

### 3. Best Practices
- Implemented comprehensive error handling across all modules
- Added `@st.cache_data` decorators for performance optimization
- Created modular, maintainable agent-based code structure
- Included proper type hints and documentation throughout

### 4. Problem Solving
- Debugged IBM watsonx 404 project errors caused by region mismatch between project and service
- Fixed PyVis HTML rendering inside Streamlit iframes
- Resolved session state persistence issues across tab switches
- Optimized IBM Granite API usage by batching small file summaries

### 5. Documentation
- Generated detailed docstrings for all agent functions
- Created this comprehensive README
- Documented the secrets configuration for IBM watsonx credentials

Development Sessions: All Bob interactions are documented in the `bob_sessions/` directory, providing a complete audit trail of the development process.

---

## 📁 Project Structure

```
devonboard/
├── app.py                  # Main Streamlit application and UI
├── agents.py               # AI agent functions (cloning, parsing, analysis)
├── llm_client.py           # Unified LLM client (IBM Granite)
├── graph_builder.py        # NetworkX + PyVis graph visualization
├── ast_parser.py           # Python AST parsing utilities
├── utils.py                # Helper functions and utilities
├── requirements.txt        # Python dependencies
├── screenshots/            # App screenshots for README
├── .streamlit/
│   ├── config.toml         # Streamlit theme configuration
│   └── secrets.toml        # API credentials (not in git)
├── bob_sessions/           # Development session logs with IBM Bob
└── README.md               # This file
```

---

## 🔒 Security Notes
- Never commit your `.streamlit/secrets.toml` file with API keys
- Add `secrets.toml` to your `.gitignore`
- The `.bobignore` file prevents sensitive files from being shared with Bob
- API keys should be rotated regularly
- DevOnboard only works with **public repositories**
- Cloned repos are stored temporarily in `/tmp/` and are never persisted

---

## 🎨 Features in Action

1. Paste any public GitHub URL into the sidebar input
2. Select your role and experience level
3. Click **Start Onboarding** to begin IBM Granite-powered analysis
4. Explore the Overview, Onboarding Path, Graph, and Chat tabs
5. Check off tasks as you complete them and track your progress
6. Ask questions using the Chat Copilot powered by IBM Granite 4H Small

---

## 📝 Try These Repositories

- **Streamlit Example**: `https://github.com/streamlit/streamlit-example`
- **Flask**: `https://github.com/pallets/flask`
- **FastAPI**: `https://github.com/tiangolo/fastapi`
- **React**: `https://github.com/facebook/react`

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## 📄 License

This project is licensed under the MIT License.

---

## 🙏 Acknowledgments
- [IBM watsonx.ai](https://www.ibm.com/watsonx) for providing the enterprise AI infrastructure
- [IBM Granite 4H Small](https://www.ibm.com/granite) for powerful, cost-efficient code analysis
- [IBM Bob](https://www.ibm.com/products/watsonx-code-assistant) for accelerating the development process
- [Streamlit](https://streamlit.io) for the excellent app framework
- [PyVis](https://pyvis.readthedocs.io) for interactive graph visualization
- [GitPython](https://gitpython.readthedocs.io) for seamless Git integration

---

## 📞 Support

For issues, questions, or suggestions, please open an issue on GitHub.

---

**Built with ❤️ using IBM watsonx.ai and IBM Bob**
