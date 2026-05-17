"""
llm_client.py
LLM client for IBM Granite (watsonx.ai)
"""

import streamlit as st
from typing import Optional

# ── IBM Granite (watsonx.ai) ───────────────────────────────────────────────
def _call_granite(prompt: str, system: Optional[str] = None,
                  history: Optional[list] = None) -> str:
    try:
        from ibm_watsonx_ai import APIClient, Credentials
        from ibm_watsonx_ai.foundation_models import ModelInference
        from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as Params
    except ImportError:
        raise ImportError(
            "ibm-watsonx-ai not installed. Run: pip install ibm-watsonx-ai"
        )

    credentials = Credentials(
        api_key=st.secrets["IBM_API_KEY"],
        url=st.secrets.get("IBM_URL", "https://us-south.ml.cloud.ibm.com")
    )
    project_id = st.secrets["IBM_PROJECT_ID"]

    model = ModelInference(
        model_id="ibm/granite-4-h-small",
        credentials=credentials,
        project_id=project_id,
        params={
            Params.MAX_NEW_TOKENS: 1024,
            Params.TEMPERATURE: 0.3,
            Params.TOP_P: 0.9,
            Params.REPETITION_PENALTY: 1.1,
        }
    )

    # Build the prompt using Granite's instruct format
    formatted = _format_granite_prompt(prompt, system, history)
    response = model.generate_text(prompt=formatted)
    return response

def _format_granite_prompt(prompt: str, system: Optional[str],
                            history: Optional[list]) -> str:
    """
    IBM Granite-4 instruct format:
    <|system|>
    {system}
    <|user|>
    {message}
    <|assistant|>
    """
    parts = []

    if system:
        # Add Granite-specific tuning to system message
        enhanced_system = "You are a helpful, precise assistant. Respond in clear structured markdown. Be thorough but avoid repetition.\n\n" + system
        parts.append(f"<|system|>\n{enhanced_system}")

    if history:
        for msg in history:
            role_tag = "<|user|>" if msg["role"] == "user" else "<|assistant|>"
            parts.append(f"{role_tag}\n{msg['content']}")

    parts.append(f"<|user|>\n{prompt}")
    parts.append("<|assistant|>")

    return "\n".join(parts)

# ── Public interface ───────────────────────────────────────────────────────────
def llm_call(
    prompt: str,
    system: Optional[str] = None,
    history: Optional[list] = None,
    provider: Optional[str] = None
) -> str:
    """
    Main entry point for all LLM calls in DevOnboard.
    Uses IBM Granite (watsonx.ai) for all AI operations.
    
    Args:
        prompt:   The user/task prompt
        system:   Optional system instruction
        history:  Optional list of {role, content} dicts for chat
        provider: Ignored (kept for compatibility)
    
    Returns:
        Response text string
    
    Usage:
        from llm_client import llm_call
        result = llm_call("Summarise this file", system="You are a code analyst")
    """
    try:
        return _call_granite(prompt, system, history)

    except Exception as e:
        error_msg = str(e)
        
        # Helpful error messages
        if "API key" in error_msg or "401" in error_msg:
            raise RuntimeError(
                "IBM watsonx API key invalid. Check IBM_API_KEY in secrets.toml"
            )
        if "project" in error_msg.lower():
            raise RuntimeError(
                "IBM Project ID invalid. Check IBM_PROJECT_ID in secrets.toml"
            )
        
        raise RuntimeError(f"LLM call failed: {error_msg}")


def get_provider_badge(provider: Optional[str] = None) -> str:
    """Returns an HTML badge showing IBM Granite is active."""
    return '''<span style="background:#1a3a8f;color:white;border-radius:20px;
              padding:3px 10px;font-size:11px;font-weight:600">
              🔷 IBM Granite</span>'''

# Made with Bob
