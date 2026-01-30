from agents.html_generation.html_generation_agent import HTMLGenerationResult, create_html_generation_agent
from agents.html_generation.tools.html_generation_tools import set_html_cache
import json
from strands import tool
from utils.aws_config import kb_client_singleton
import threading

_thread_local = threading.local()

def set_progress_callback(callback):
    """Set the progress callback for the current thread"""
    _thread_local.progress_callback = callback

def set_orchestrator_html_cache(cache):
    """Set the HTML cache for the current thread"""
    _thread_local.html_cache = cache

@tool
def generate_html_from_request(
    instruction: str,
    refine_previous: bool,
    requires_external_data: bool
) -> str:
    """
    Generate HTML based on user instruction, optional KB context,
    and optional refinement of previous HTML.
    """
    def send_progress(message: str):
        callback = getattr(_thread_local, 'progress_callback', None)
        if callback:
            callback(message)
    
    def get_html_cache():
        return getattr(_thread_local, 'html_cache', None)
    
    send_progress("Starting HTML generation...")
    
    print(
        "generate_html_from_request\n"
        f"  refine_previous={refine_previous}\n"
        f"  requires_external_data={requires_external_data}\n"
        f"  instruction_len={len(instruction)}"
    )
    
    html_generation_agent = create_html_generation_agent()
    
    # Set the HTML cache for the HTML generation tools
    html_cache = get_html_cache()
    if html_cache:
        set_html_cache(html_cache)
    
    # ----------------------------
    # Retrieve KB context if needed
    # ----------------------------
    kb_context = ""
    if requires_external_data:
        send_progress("Searching knowledge base...")
        kb_chunks = kb_client_singleton.retrieve(query=instruction)
        send_progress(f"Found {len(kb_chunks)} relevant documents")
        kb_context = kb_client_singleton.build_kb_context(kb_chunks)
    
    # ----------------------------
    # Build prompt sections
    # ----------------------------
    send_progress("Preparing context...")
    prompt_sections = []
    
    if kb_context:
        prompt_sections.append(
            "KNOWLEDGE BASE CONTEXT:\n"
            f"{kb_context}"
        )
    
    if refine_previous:
        send_progress("Loading previous HTML...")
        html_cache = get_html_cache()
        if html_cache:
            previous_entry = html_cache.latest()
            if previous_entry:
                prompt_sections.append(
                    "PREVIOUS HTML:\n"
                    f"{previous_entry.html}"
                )
        
        prompt_sections.append(
            "INSTRUCTION:\n"
            f"Refine the previous HTML based on the following request:\n"
            f"{instruction}\n\n"
            "Keep the overall structure unless the instruction explicitly asks for a redesign."
        )
    else:
        prompt_sections.append(
            "INSTRUCTION:\n"
            f"Generate brand new HTML based on the following request:\n"
            f"{instruction}"
        )
    
    html_prompt = "\n\n---\n\n".join(prompt_sections)
    
    # ----------------------------
    # Call HTML generation agent
    # ----------------------------
    send_progress("Generating HTML with AI...")
    result = html_generation_agent(
        html_prompt,
        structured_output_model=HTMLGenerationResult
    )
    
    html_response: HTMLGenerationResult = result.structured_output
    
    if not html_response.success:
        send_progress("Error generating HTML")
        return json.dumps({
            "success": False,
            "error_message": html_response.error_message
        })
    
    send_progress("Validating HTML...")
    return json.dumps({
        "success": True,
        "html": html_response.html
    })