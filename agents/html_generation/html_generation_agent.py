from agents.html_generation.tools.html_generation_tools import get_previous_html, validate_html
from agents.html_generation.html_generation_system_prompt import html_prompt
from pydantic import BaseModel, Field
from strands import Agent
from utils.aws_config import create_bedrock_model

class HTMLGenerationResult(BaseModel):
    """Model that defines result of HTML generation"""
    success: bool = Field(description="True if HTML generated and validated successfully")
    html: str = Field(description="Valid generated HTML")
    error_message: str | None = Field(
        default=None,
        description="Error message if HTML generation unsuccessful. If successful, this is empty"
    )

def create_html_generation_agent() -> Agent:
    """
    Factory function to create instance of HTML generation agent.
    """
    return Agent(
        name="HTMLGenerationAgent",
        system_prompt=html_prompt,
        model=create_bedrock_model(),
        tools=[get_previous_html, validate_html]
    )