from agents.orchestrator.orchestrator_system_prompt import orchestrator_system_prompt
from agents.orchestrator.tools.orchestrator_tools import generate_html_from_request
import json
from pydantic import BaseModel, Field
from strands import Agent
from utils.ai_config import create_model

class PortfolioAgentResult(BaseModel):
    """Model that defines output of portfolio orchestator agent"""
    success: bool = Field(description="True if process was successful, otherwise False")
    chat_message: str = Field(description="Chat agent response to user request")
    html: str | None = Field(
        default=None,
        description="Valid generated HTML if neccessary"
    )
    error_message: str | None = Field(
        default=None,
        description="Error message if process unsuccessful. If successful, this is empty"
    )


class OrchestrationDecision(BaseModel):
    """Structured decision for Python-owned portfolio orchestration."""

    success: bool = Field(description="False only when the user request should fail")
    chat_message: str = Field(description="Concise chat response to show to the user")
    needs_ui_change: bool = Field(description="True when new or updated HTML should be generated")
    instruction: str | None = Field(
        default=None,
        description="Specific HTML-generation instruction if needs_ui_change is true"
    )
    refine_previous: bool = Field(description="True when the request should modify the previous HTML")
    requires_external_data: bool = Field(description="True when portfolio facts should be retrieved")
    error_message: str | None = Field(default=None, description="Error message if success is false")


def create_orchestrator_agent() -> Agent:
    """
    Factory function to create an orchestration decision agent.
    """
    return Agent(
        name="PortfolioAgent",
        system_prompt=orchestrator_system_prompt,
        model=create_model(),
        tools=[]
    )


def run_portfolio_request(
    user_action: str,
    html_cache=None,
    progress_callback=None,
    chat_history: list[dict] | None = None,
) -> PortfolioAgentResult:
    def send_progress(message: str):
        if progress_callback:
            progress_callback(message)

    send_progress("Analyzing request...")
    portfolio_agent = create_orchestrator_agent()
    previous_html_available = bool(html_cache and html_cache.latest())
    recent_history = chat_history[-8:] if chat_history else []
    history_lines = [
        f"{entry.get('role', 'unknown')}: {entry.get('content', '')}"
        for entry in recent_history
    ]
    decision_prompt = (
        f"Previous HTML exists: {previous_html_available}\n\n"
        "Recent chat history:\n"
        f"{chr(10).join(history_lines) if history_lines else '(none)'}\n\n"
        f"Current user chat request: {user_action}"
    )
    decision_result = portfolio_agent(
        decision_prompt,
        structured_output_model=OrchestrationDecision
    )
    decision: OrchestrationDecision = decision_result.structured_output

    if not decision.success:
        return PortfolioAgentResult(
            success=False,
            chat_message=decision.chat_message,
            html=None,
            error_message=decision.error_message or decision.chat_message,
        )

    if not decision.needs_ui_change:
        return PortfolioAgentResult(
            success=True,
            chat_message=decision.chat_message,
            html=None,
            error_message=None,
        )

    if not decision.instruction:
        return PortfolioAgentResult(
            success=False,
            chat_message="I could not determine what to display.",
            html=None,
            error_message="Missing HTML generation instruction.",
        )

    from agents.orchestrator.tools.orchestrator_tools import (
        set_orchestrator_html_cache,
        set_progress_callback,
    )

    set_progress_callback(progress_callback)
    set_orchestrator_html_cache(html_cache)

    try:
        html_result_json = generate_html_from_request(
            instruction=decision.instruction,
            refine_previous=decision.refine_previous,
            requires_external_data=decision.requires_external_data,
        )
        html_result = json.loads(html_result_json)
    finally:
        set_progress_callback(None)

    if not html_result.get("success"):
        error_message = html_result.get("error_message") or "HTML generation failed."
        return PortfolioAgentResult(
            success=False,
            chat_message=error_message,
            html=None,
            error_message=error_message,
        )

    return PortfolioAgentResult(
        success=True,
        chat_message=decision.chat_message,
        html=html_result.get("html"),
        error_message=None,
    )
