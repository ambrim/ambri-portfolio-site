from utils.html_cache import html_cache
from lxml import html as lxml_html
import json
from strands import tool

@tool
def validate_html(html: str) -> str:
    """
    Validates generated HTML, otherwise returns error message

    Args:
        html: Generated HTML string to validate
    """
    try:
        lxml_html.fromstring(html)
        return json.dumps({
            "success": True,
            "html": html
        })
    except Exception as e:
        return json.dumps({
            "success": False,
            "error_message": "Invalid HTML structure: {str(e)}" 
        })

@tool
def get_previous_html() -> str:
    """
    Gets the most recently generated HTML from the HTML cache.
    """
    latest = html_cache.latest()
    if latest:
        return json.dumps({
            "success": True,
            "html": latest.html
        })
    else:
        return json.dumps({
            "success": False,
            "error_message": "No items in HTML Cache. Generate brand new HTML instead." 
        })
