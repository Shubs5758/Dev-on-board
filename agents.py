"""
AI Agent functions for DevOnboard.
Handles repository cloning, parsing, analysis, and conversational AI.
"""

import os
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional
import json

import streamlit as st
from git import Repo, GitCommandError

import utils
import ast_parser
from llm_client import llm_call


def agent_clone_repo(github_url: str, tmp_dir: str) -> Dict:
    """
    Clone a GitHub repository to a temporary directory.
    
    Args:
        github_url: GitHub repository URL
        tmp_dir: Temporary directory path
        
    Returns:
        Dictionary with repo_name, local_path, clone_success, error_message
    """
    result = {
        'repo_name': utils.extract_repo_name(github_url),
        'local_path': '',
        'clone_success': False,
        'error_message': ''
    }
    
    # Validate URL
    if not utils.is_valid_github_url(github_url):
        result['error_message'] = "Invalid GitHub URL format. Please use: https://github.com/username/repo"
        return result
    
    try:
        # If directory exists, remove it first
        if os.path.exists(tmp_dir):
            try:
                shutil.rmtree(tmp_dir)
            except Exception as e:
                # If can't remove, try a different directory
                import time
                tmp_dir = tmp_dir + f"_{int(time.time())}"
        
        # Create temp directory
        os.makedirs(tmp_dir, exist_ok=True)
        
        # Clone with depth=1 for faster cloning
        repo = Repo.clone_from(
            github_url,
            tmp_dir,
            depth=1,
            single_branch=True
        )
        
        result['local_path'] = tmp_dir
        result['clone_success'] = True
        
    except GitCommandError as e:
        if 'Authentication failed' in str(e) or 'Repository not found' in str(e):
            result['error_message'] = "This repository is private or doesn't exist. Please use a public repository."
        else:
            result['error_message'] = f"Failed to clone repository: {str(e)}"
    except Exception as e:
        result['error_message'] = f"Unexpected error: {str(e)}"
    
    return result


def agent_parse_files(repo_path: str, role: str) -> List[Dict]:
    """
    Parse all supported files in the repository.
    
    Args:
        repo_path: Path to the cloned repository
        role: Developer role for relevance scoring
        
    Returns:
        List of file information dictionaries
    """
    parsed_files = []
    total_files_scanned = 0
    skipped_files = 0
    
    # Supported extensions - expanded list
    supported_extensions = {
        '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go', '.rs',
        '.cpp', '.c', '.rb', '.php', '.swift', '.kt', '.cs',
        '.html', '.css', '.json', '.yaml', '.yml', '.md',
        '.sh', '.bash', '.sql', '.r', '.scala', '.vue', '.xml',
        '.txt', '.toml', '.ini', '.cfg', '.conf'
    }
    
    # Walk through repository
    for root, dirs, files in os.walk(repo_path):
        # Skip directories
        dirs[:] = [d for d in dirs if not utils.should_skip_file(os.path.join(root, d))]
        
        for filename in files:
            filepath = os.path.join(root, filename)
            total_files_scanned += 1
            
            # Skip if should be skipped
            if utils.should_skip_file(filepath) or utils.should_skip_extension(filename):
                skipped_files += 1
                continue
            
            # Check extension
            ext = Path(filename).suffix.lower()
            if ext not in supported_extensions:
                skipped_files += 1
                continue
            
            # Check file size (skip > 500KB to be more lenient)
            try:
                file_size = os.path.getsize(filepath)
                if file_size > 500 * 1024:  # 500KB
                    continue
            except:
                continue
            
            # Read file content
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            except Exception as e:
                continue
            
            # Get relative path
            rel_path = os.path.relpath(filepath, repo_path)
            
            # Detect language
            language = utils.detect_language(filename)
            
            # Count lines
            lines = utils.count_lines(content)
            
            # Initialize file info
            file_info = {
                'path': rel_path,
                'name': filename,
                'language': language,
                'lines': lines,
                'content': content,
                'functions': [],
                'classes': [],
                'imports': [],
                'size_kb': file_size / 1024,
                'complexity_score': 1,
                'role_relevance': 0.0
            }
            
            # Extract detailed info for Python files
            if language == 'Python':
                python_info = ast_parser.extract_python_info(content, rel_path)
                file_info['functions'] = python_info.get('functions', [])
                file_info['classes'] = python_info.get('classes', [])
                file_info['imports'] = python_info.get('imports', [])
                file_info['complexity_score'] = python_info.get('complexity_score', 1)
            else:
                # Extract imports using regex
                imports = ast_parser.extract_imports_regex(content, language)
                file_info['imports'] = imports
                
                # Extract functions and classes
                functions = ast_parser.extract_functions_regex(content, language)
                classes = ast_parser.extract_classes_regex(content, language)
                file_info['functions'] = functions
                file_info['classes'] = classes
                
                # Calculate complexity
                file_info['complexity_score'] = ast_parser.calculate_file_complexity(
                    content, language, functions, classes
                )
            
            # Calculate role relevance
            file_info['role_relevance'] = utils.calculate_role_relevance(
                rel_path, content, role
            )
            
            parsed_files.append(file_info)
    
    # Sort by role relevance
    parsed_files.sort(key=lambda x: x['role_relevance'], reverse=True)
    
    # Log statistics for debugging
    print(f"[DEBUG] Files scanned: {total_files_scanned}, Skipped: {skipped_files}, Parsed: {len(parsed_files)}")
    
    return parsed_files


def agent_summarize_file(file_info: Dict, repo_context: str) -> str:
    """
    Generate AI summary for a single file.
    
    Args:
        file_info: File information dictionary
        repo_context: Context about the repository
        
    Returns:
        Markdown-formatted summary string
    """
    filepath = file_info['path']
    content = utils.truncate_for_context(file_info['content'], 2000)
    language = file_info['language']
    
    prompt = f"""Analyze this {language} file from a codebase.

Repository Context: {repo_context}

File: {filepath}
Language: {language}
Lines: {file_info['lines']}

Code:
```{language.lower()}
{content}
```

Provide a structured analysis:

**PURPOSE**: What does this file do? (1-2 sentences)

**KEY_FUNCTIONS**: List 3-5 most important functions/classes with brief descriptions

**DEPENDENCIES**: What does this file depend on? What imports are critical?

**COMPLEXITY**: Rate 1-5 and explain why

**ROLE_RELEVANCE**: How relevant is this for different developer roles?

**GOTCHAS**: Any tricky parts, potential bugs, or important notes?

Keep it concise and practical.

Respond using these exact headers: ## Purpose, ## Key Functions, ## Dependencies, ## Complexity (1-5), ## Issues"""

    try:
        return llm_call(
            prompt=prompt,
            system="You are a senior software engineer analysing a codebase."
        )
    except Exception as e:
        return f"**Error generating summary**: {str(e)}\n\nFile contains {file_info['lines']} lines of {language} code."


def agent_generate_project_summary(
    all_file_summaries: List[str],
    repo_name: str,
    role: str,
    experience: str
) -> Dict:
    """
    Generate comprehensive project summary using AI.
    
    Args:
        all_file_summaries: List of file summary strings
        repo_name: Name of the repository
        role: Developer role
        experience: Experience level
        
    Returns:
        Dictionary with project overview, observations, tech stack, etc.
    """
    # Combine summaries (truncate if too long)
    combined_summaries = "\n\n".join(all_file_summaries[:20])
    if len(combined_summaries) > 15000:
        combined_summaries = combined_summaries[:15000] + "\n\n... [truncated]"
    
    prompt = f"""You are analyzing the codebase: {repo_name}

Developer Profile:
- Role: {role}
- Experience: {experience}

File Summaries:
{combined_summaries}

Generate a comprehensive project analysis in JSON format:

{{
  "project_overview": "2-3 paragraph overview of what this project does, its purpose, and main features",
  "key_observations": [
    "5-7 bullet points about architecture, patterns, entry points, and structure"
  ],
  "tech_stack": [
    "List of technologies, frameworks, and tools used"
  ],
  "architecture_style": "e.g., MVC, microservices, monolith, layered, etc.",
  "health_score": "Well-structured | Moderate complexity | Complex codebase",
  "files_to_read_first": [
    {{"file": "path/to/file", "reason": "why this file is important for a {role}"}},
    // 5 files total
  ]
}}

Be specific and reference actual files from the summaries."""

    try:
        result_text = llm_call(
            prompt=prompt,
            system="You are a senior software architect analyzing a codebase."
        )
        
        # Try to extract JSON
        if '```json' in result_text:
            json_start = result_text.find('```json') + 7
            json_end = result_text.find('```', json_start)
            result_text = result_text[json_start:json_end].strip()
        elif '```' in result_text:
            json_start = result_text.find('```') + 3
            json_end = result_text.find('```', json_start)
            result_text = result_text[json_start:json_end].strip()
        
        result = json.loads(result_text)
        return result
        
    except Exception as e:
        # Fallback if JSON parsing fails
        return {
            'project_overview': f"Repository: {repo_name}\n\nAnalysis in progress...",
            'key_observations': [
                "Project structure being analyzed",
                "Multiple file types detected",
                "Dependencies being mapped"
            ],
            'tech_stack': ["Analysis in progress"],
            'architecture_style': "Unknown",
            'health_score': "Moderate complexity",
            'files_to_read_first': []
        }


def agent_generate_onboarding_path(
    project_summary: Dict,
    parsed_files: List[Dict],
    role: str,
    experience: str
) -> List[Dict]:
    """
    Generate personalized onboarding path with phases and tasks.
    
    Args:
        project_summary: Project summary dictionary
        parsed_files: List of parsed files
        role: Developer role
        experience: Experience level
        
    Returns:
        List of phase dictionaries with tasks
    """
    # Get top files
    top_files = [f['path'] for f in parsed_files[:15]]
    
    # Adjust depth based on experience
    depth_guidance = {
        "Junior (0–2 yrs)": "Provide detailed step-by-step guidance with explanations",
        "Mid (2–5 yrs)": "Balance between guidance and independence",
        "Senior (5+ yrs)": "Focus on architecture and design decisions"
    }
    
    prompt = f"""Create a personalized onboarding path for a {role} with {experience} experience.

Project: {project_summary.get('project_overview', '')}
Architecture: {project_summary.get('architecture_style', '')}
Tech Stack: {', '.join(project_summary.get('tech_stack', [])[:5])}

Key Files Available:
{chr(10).join(f'- {f}' for f in top_files[:10])}

Guidance Level: {depth_guidance.get(experience, '')}

Generate a 4-phase onboarding journey in JSON format:

{{
  "phases": [
    {{
      "phase_name": "Phase 1 — Orientation",
      "phase_subtitle": "Day 1",
      "tasks": [
        {{
          "id": "task_1_1",
          "task": "Read the README and understand project goals",
          "why": "Explanation of why this matters",
          "file_ref": "README.md",
          "estimated_minutes": 15
        }}
        // 4-5 tasks per phase
      ]
    }},
    {{
      "phase_name": "Phase 2 — Core Understanding",
      "phase_subtitle": "Days 2–3",
      "tasks": [
        // Role-specific tasks referencing actual files
      ]
    }},
    {{
      "phase_name": "Phase 3 — Deep Dive",
      "phase_subtitle": "Week 1",
      "tasks": [
        // File-specific deep dives
      ]
    }},
    {{
      "phase_name": "Phase 4 — First Contribution",
      "phase_subtitle": "Week 2",
      "tasks": [
        // Practical contribution tasks
      ]
    }}
  ]
}}

Make tasks specific to the {role} role and reference actual files from the list."""

    try:
        result_text = llm_call(
            prompt=prompt,
            system="You are an experienced engineering manager creating onboarding plans."
        )
        
        # Extract JSON
        if '```json' in result_text:
            json_start = result_text.find('```json') + 7
            json_end = result_text.find('```', json_start)
            result_text = result_text[json_start:json_end].strip()
        elif '```' in result_text:
            json_start = result_text.find('```') + 3
            json_end = result_text.find('```', json_start)
            result_text = result_text[json_start:json_end].strip()
        
        result = json.loads(result_text)
        return result.get('phases', [])
        
    except Exception as e:
        # Fallback phases
        return _get_fallback_phases(role, top_files)


def _get_fallback_phases(role: str, top_files: List[str]) -> List[Dict]:
    """Generate fallback onboarding phases if AI fails."""
    return [
        {
            "phase_name": "Phase 1 — Orientation",
            "phase_subtitle": "Day 1",
            "tasks": [
                {
                    "id": "task_1_1",
                    "task": "Read the README and understand project goals",
                    "why": "Get the big picture before diving into code",
                    "file_ref": "README.md",
                    "estimated_minutes": 15
                },
                {
                    "id": "task_1_2",
                    "task": "Explore the folder structure",
                    "why": "Understand how the codebase is organized",
                    "file_ref": "",
                    "estimated_minutes": 20
                },
                {
                    "id": "task_1_3",
                    "task": "Set up the development environment",
                    "why": "Get ready to run and modify the code",
                    "file_ref": "",
                    "estimated_minutes": 30
                }
            ]
        },
        {
            "phase_name": "Phase 2 — Core Understanding",
            "phase_subtitle": "Days 2–3",
            "tasks": [
                {
                    "id": "task_2_1",
                    "task": f"Read {top_files[0] if top_files else 'main entry point'}",
                    "why": "Understand how the application starts",
                    "file_ref": top_files[0] if top_files else "",
                    "estimated_minutes": 30
                },
                {
                    "id": "task_2_2",
                    "task": "Trace a key user flow",
                    "why": "See how different parts connect",
                    "file_ref": "",
                    "estimated_minutes": 45
                }
            ]
        }
    ]


def agent_chat(
    user_message: str,
    repo_context: Dict,
    chat_history: List[Dict],
    role: str
) -> str:
    """
    Handle conversational Q&A about the repository.
    
    Args:
        user_message: User's question
        repo_context: Repository context dictionary
        chat_history: Previous chat messages
        role: Developer role
        
    Returns:
        AI response as markdown string
    """
    # Build context
    repo_name = repo_context.get('repo_name', 'this repository')
    project_overview = repo_context.get('project_overview', '')
    tech_stack = repo_context.get('tech_stack', [])
    file_list = repo_context.get('file_list', [])[:20]
    
    system_prompt = f"""You are a senior engineer who built {repo_name}. You're pair programming with a {role}.

Project Overview:
{project_overview}

Tech Stack: {', '.join(tech_stack)}

Key Files:
{chr(10).join(f'- {f}' for f in file_list)}

Guidelines:
- Answer as if you deeply know this specific codebase
- Always cite specific files and line ranges when relevant
- Be direct and practical
- If you don't know something, say so
- Suggest follow-up actions or files to explore
- Keep responses concise but complete"""

    try:
        return llm_call(
            prompt=user_message,
            system=system_prompt,
            history=chat_history[-10:] if chat_history else None  # Last 10 messages
        )
        
    except Exception as e:
        return f"I apologize, but I encountered an error: {str(e)}\n\nPlease try rephrasing your question or ask something else about the codebase."

# Made with Bob
