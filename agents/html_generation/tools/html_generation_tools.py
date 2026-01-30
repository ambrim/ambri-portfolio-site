from lxml import html as lxml_html
import json
from strands import tool

# Global reference to current HTML cache (set per request)
_current_html_cache = None

def set_html_cache(cache):
    """Set the HTML cache for the current request"""
    global _current_html_cache
    _current_html_cache = cache

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
            "error_message": f"Invalid HTML structure: {str(e)}" 
        })

@tool
def get_previous_html() -> str:
    """
    Gets the most recently generated HTML from the HTML cache.
    """
    global _current_html_cache
    
    if _current_html_cache is None:
        return json.dumps({
            "success": False,
            "error_message": "HTML cache not available. Generate brand new HTML instead."
        })
    
    latest = _current_html_cache.latest()
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