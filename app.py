import nest_asyncio
nest_asyncio.apply()

import asyncio
from flask import Flask, render_template, request, jsonify, Response, stream_with_context
from datetime import datetime
import json
import queue
import threading
import os
from markupsafe import Markup

from agents.orchestrator.orchestrator_agent import PortfolioAgentResult, create_orchestrator_agent
from agents.orchestrator.tools.orchestrator_tools import set_progress_callback
from utils.chat_message_store import chat_store
from utils.html_cache import html_cache

app = Flask(__name__)
portfolio_agent = create_orchestrator_agent()

progress_updates = {}

@app.route("/")
def index():
    return render_template(
        "index.html",
        current_year=datetime.now().year
    )

app = Flask(__name__)
portfolio_agent = create_orchestrator_agent()

@app.route("/")
def index():
    return render_template(
        "index.html",
        current_year=datetime.now().year
    )

@app.route("/chat/stream", methods=["POST"])
def handle_chat_stream():
    """Streaming endpoint that sends progress updates"""
    user_action = request.json.get("instruction", "")
    
    progress_queue = queue.Queue()
    
    def progress_callback(message: str):
        """Callback function that puts messages in the queue"""
        progress_queue.put({"type": "progress", "message": message})
    
    set_progress_callback(progress_callback)
    
    @stream_with_context
    def generate():
        try:
            yield f"data: {json.dumps({'status': 'started', 'message': 'Processing request...'})}\n\n"
            
            chat_store.add("user", user_action)
            
            yield f"data: {json.dumps({'status': 'orchestrating', 'message': 'Analyzing request...'})}\n\n"
            
            result_container = {}
            error_container = {}
            
            def run_agent():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    result = portfolio_agent(
                        f"User chat request: {user_action}",
                        structured_output_model=PortfolioAgentResult
                    )
                    result_container['result'] = result
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    error_container['error'] = e
                finally:
                    progress_queue.put({"type": "done"})
                    loop.close()
            
            agent_thread = threading.Thread(target=run_agent)
            agent_thread.start()
            
            while True:
                try:
                    msg = progress_queue.get(timeout=0.1)
                    if msg["type"] == "done":
                        break
                    elif msg["type"] == "progress":
                        yield f"data: {json.dumps({'status': 'progress', 'message': msg['message']})}\n\n"
                
                except queue.Empty:
                    yield ": heartbeat\n\n" 
            
            agent_thread.join()
            
            if 'error' in error_container:
                raise error_container['error']
            
            portfolio_agent_response: PortfolioAgentResult = result_container['result'].structured_output
            
            chat_message = portfolio_agent_response.chat_message
            agent_html = portfolio_agent_response.html
            success = portfolio_agent_response.success
            error_message = portfolio_agent_response.error_message
            
            chat_store.add("agent", chat_message)
            
            if not success:
                yield f"data: {json.dumps({'status': 'error', 'message': error_message})}\n\n"
                return
            
            yield f"data: {json.dumps({'status': 'finalizing', 'message': 'Finalizing...'})}\n\n"
            
            safe_html = Markup(agent_html) if agent_html else ""
            if agent_html:
                html_cache.add(user_action, agent_html)
            
            final_data = {
                "status": "complete",
                "success": success,
                "chat_message": chat_message,
                "html": str(safe_html),
                "history": chat_store.format_messages()
            }
            yield f"data: {json.dumps(final_data)}\n\n"
            
        except Exception as e:
            print(f"Error in stream: {e}")
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'status': 'error', 'message': str(e)})}\n\n"
        finally:
            set_progress_callback(None)
    
    return Response(generate(), mimetype='text/event-stream')

@app.route("/chat", methods=["POST"])
def handle_chat_request():
    """Fallback non-streaming endpoint"""
    user_action = request.json.get("instruction", "")
    
    chat_store.add("user", user_action)
    
    try:
        result = portfolio_agent(
            f"User chat request: {user_action}",
            structured_output_model=PortfolioAgentResult
        )
        
        portfolio_agent_response: PortfolioAgentResult = result.structured_output
        
        chat_message = portfolio_agent_response.chat_message
        agent_html = portfolio_agent_response.html
        success = portfolio_agent_response.success
        error_message = portfolio_agent_response.error_message
        
        chat_store.add("agent", chat_message)
        
        if not success:
            print(f"Error found: {error_message}")
            return jsonify({
                "success": success,
                "chat_message": chat_message,
            })
        
        safe_html = Markup(agent_html) if agent_html else ""
        if agent_html:
            html_cache.add(user_action, agent_html)
        return jsonify({
            "success": success,
            "chat_message": chat_message,
            "html": str(safe_html),
            "history": chat_store.format_messages()
        })
    except Exception as e:
        print(e)
        return jsonify({
            "success": False,
            "chat_message": str(e),
            "history": chat_store.format_messages()
        })
    
@app.route("/chat/history", methods=["GET"])
def get_chat_history():
    return jsonify({
        "success": True,
        "entries": chat_store.format_messages()
    })
    
@app.route("/ui/history", methods=["GET"])
def get_ui_history():
    entries = []

    for idx, entry in enumerate(html_cache.all()):
        entries.append({
            "id": idx,
            "query": entry.query,
            "timestamp": entry.timestamp
        })

    return jsonify({
        "success": True,
        "entries": entries
    })

@app.route("/ui/history/<int:entry_id>", methods=["GET"])
def restore_ui_from_history(entry_id: int):
    entries = html_cache.all()

    if entry_id < 0 or entry_id >= len(entries):
        print("HTML cache entry not found")
        return jsonify({
            "success": False,
        })

    entry = entries[entry_id]
    html_cache.promote(entry)

    return jsonify({
        "html": entry.html,
        "query": entry.query,
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)