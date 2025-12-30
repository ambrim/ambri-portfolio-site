from agents.orchestrator.orchestrator_system_prompt import orchestrator_system_prompt
from agents.orchestrator.tools.orchestrator_tools import generate_html_from_request
from pydantic import BaseModel, Field
from strands import Agent
from utils.aws_config import create_bedrock_model

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

def create_orchestrator_agent() -> Agent:
    """
    Factory function to create instance of orchestrator agent.
    """
    return Agent(
        name="PortfolioAgent",
        system_prompt=orchestrator_system_prompt,
        model=create_bedrock_model(),
        tools=[generate_html_from_request]
    )