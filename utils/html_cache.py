from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
import math
import os
import re
from typing import List, Optional
import json
from clients.redis_client import redis_client


@dataclass
class HTMLCacheEntry:
    query: str
    html: str
    timestamp: str
    
    def to_dict(self):
        return {
            "query": self.query,
            "html": self.html,
            "timestamp": self.timestamp
        }
    
    @staticmethod
    def from_dict(data):
        return HTMLCacheEntry(
            query=data["query"],
            html=data["html"],
            timestamp=data["timestamp"]
        )


class HTMLCache:
    def __init__(self, session_id: str, max_size: int = 10):
        self.session_id = session_id
        self.max_size = max_size
        self.key = f"html_cache:{session_id}"
        self.ttl = 86400  # 24 hours
    
    def _tokenize(self, text: str) -> List[str]:
        text = re.sub(r'[^\w\s]', '', text.lower())
        return text.split()
    
    def _cosine_similarity(self, tokens1: List[str], tokens2: List[str]) -> float:
        vec1 = Counter(tokens1)
        vec2 = Counter(tokens2)
        
        intersection = set(vec1.keys()) & set(vec2.keys())
        
        if not intersection:
            return 0.0
        
        numerator = sum([vec1[x] * vec2[x] for x in intersection])
        
        sum1 = sum([vec1[x]**2 for x in vec1.keys()])
        sum2 = sum([vec2[x]**2 for x in vec2.keys()])
        denominator = math.sqrt(sum1) * math.sqrt(sum2)
        
        if denominator == 0:
            return 0.0
        
        return numerator / denominator
    
    def _jaccard_similarity(self, tokens1: List[str], tokens2: List[str]) -> float:
        set1 = set(tokens1)
        set2 = set(tokens2)
        
        intersection = set1 & set2
        union = set1 | set2
        
        if not union:
            return 0.0
        
        return len(intersection) / len(union)
    
    def find_similar_query(self, new_query: str, threshold: float = 0.8) -> Optional[HTMLCacheEntry]:
        all_entries = self.all()
        
        if not all_entries:
            return None
        
        new_tokens = self._tokenize(new_query)
        
        best_score = -1
        best_entry = None
        
        for entry in all_entries:
            old_tokens = self._tokenize(entry.query)
            
            cosine_sim = self._cosine_similarity(new_tokens, old_tokens)
            jaccard_sim = self._jaccard_similarity(new_tokens, old_tokens)
            combined_score = 0.7 * cosine_sim + 0.3 * jaccard_sim
            print(f"Similarity score: {combined_score}")
            
            if combined_score > threshold and combined_score > best_score:
                best_score = combined_score
                best_entry = entry
        
        return best_entry
    
    def add(self, query: str, html: str) -> None:
        entry = HTMLCacheEntry(
            query=query,
            html=html,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        # Add to Redis list (newest first)
        redis_client.lpush(self.key, json.dumps(entry.to_dict()))
        
        # Trim to max size
        redis_client.ltrim(self.key, 0, self.max_size - 1)
        
        # Reset expiration
        redis_client.expire(self.key, self.ttl)
    
    def all(self) -> List[HTMLCacheEntry]:
        """Get all entries as HTMLCacheEntry objects"""
        entries_json = redis_client.lrange(self.key, 0, -1)
        return [HTMLCacheEntry.from_dict(json.loads(e)) for e in entries_json]
    
    def get(self, index: int) -> Optional[HTMLCacheEntry]:
        """Get entry by index (0 = most recent)"""
        entry_json = redis_client.lindex(self.key, index)
        if entry_json:
            return HTMLCacheEntry.from_dict(json.loads(entry_json))
        return None
    
    def latest(self) -> Optional[HTMLCacheEntry]:
        """Get most recent entry"""
        return self.get(0)
    
    def promote(self, entry: HTMLCacheEntry) -> None:
        """Move entry to the front of the cache"""
        try:
            # Remove the entry
            redis_client.lrem(self.key, 1, json.dumps(entry.to_dict()))
            # Add it back at the front
            redis_client.lpush(self.key, json.dumps(entry.to_dict()))
            # Reset expiration
            redis_client.expire(self.key, self.ttl)
        except Exception:
            # Entry might not exist, that's okay
            pass
    
    def clear(self) -> None:
        redis_client.delete(self.key)
    
    def __len__(self) -> int:
        return redis_client.llen(self.key)
    
# At the bottom of html_cache.py, remove the singleton but keep the HTML:

WELCOME_HTML = '''
<div class="hero-section">
  <h1>Hi, I'm Ambri Ma</h1>
  <p class="tagline">Building at the intersection of ML, software, and AI applications</p>
</div>

<div class="about-site">
  <h2>About This Site</h2>
  <p>
    This dynamic portfolio comes with a confession: <strong>I'm terrible at keeping websites updated.</strong>
    Every time I finish a project or learn something new, I tell myself I'll update my site, but I never do.
  </p>
  <p>
    So instead of manually designing and editing HTML/CSS every time I needed to change something, 
    I decided to leave that job to you! This site is an agentic portfolio that generates 
    whatever content you want to see (about me, at least) on demand. The AI agent on the right has access to
    basically my entire professional life and can create custom pages about anything: projects, experience, education, skills - whatever you want to see.
  </p>
  <p>
    <strong>How it works:</strong> This runs on <a href="https://strandsagents.com/latest/" target="_blank">Strands</a>,
    an agentic framework that takes user instruction, determines correct tools to use, and returns output as desired. Behind the scenes,
    it uses <a href="https://aws.amazon.com/bedrock/knowledge-bases/" target="_blank">AWS Bedrock Knowledge Bases</a>
    for retrieval-augmented generation (RAG) to search through my structured data, find relevant info, and then generate the relevant HTML.
  </p>
  <p>
    The result? A portfolio that's always up-to-date (as long as I update the knowledge base, which is
    way easier than editing HTML). Plus, you get exactly the information you're looking for instead of
    scrolling through a static page hoping to find it.
  </p>
  <div class="how-it-works">
    <h3>What You Can Do</h3>
    <div class="features-grid">
      <div class="feature">
        <svg class="feature-icon" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"
          fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
        </svg>
        <strong>Chat to Explore</strong>
        <p>Ask the AI about my projects, experience, or skills—it'll generate tailored content in real-time.</p>
      </div>
      <div class="feature">
        <svg class="feature-icon" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"
          fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="23 4 23 10 17 10"></polyline>
          <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path>
        </svg>
        <strong>Refine & Iterate</strong>
        <p>Not what you wanted? Just ask for changes and the AI will update the page dynamically.</p>
      </div>
      <div class="feature">
        <svg class="feature-icon" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"
          fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
          <polyline points="14 2 14 8 20 8"></polyline>
          <line x1="16" y1="13" x2="8" y2="13"></line>
          <line x1="16" y1="17" x2="8" y2="17"></line>
        </svg>
        <strong>Browse History</strong>
        <p>Switch to "UI History" tab to revisit previous views you've generated.</p>
      </div>
    </div>
  </div>
  <p class="cta-text">
    Try asking: <em>"Show me your projects"</em> or <em>"Tell me about your experience with machine learning"</em>
  </p>
</div>

<div class="quick-links">
  <h2>Quick Start</h2>
  <div class="link-cards">
    <button class="link-card"
      onclick="document.getElementById('chat-input').value='Show me your projects'; document.getElementById('chat-input').focus();">
      <svg class="card-icon" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none"
        stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
      </svg>
      <span class="card-title">View Projects</span>
    </button>
    
    <button class="link-card"
      onclick="document.getElementById('chat-input').value='Tell me about your work experience'; document.getElementById('chat-input').focus();">
      <svg class="card-icon" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none"
        stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <rect x="2" y="7" width="20" height="14" rx="2" ry="2"></rect>
        <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path>
      </svg>
      <span class="card-title">Experience</span>
    </button>
    
    <button class="link-card"
      onclick="document.getElementById('chat-input').value='Describe your education/coursework'; document.getElementById('chat-input').focus();">
      <svg class="card-icon" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none"
        stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M22 10v6M2 10l10-5 10 5-10 5z"></path>
        <path d="M6 12v5c3 3 9 3 12 0v-5"></path>
      </svg>
      <span class="card-title">Education</span>
    </button>
    
    <button class="link-card"
      onclick="document.getElementById('chat-input').value='What are your technical skills?'; document.getElementById('chat-input').focus();">
      <svg class="card-icon" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none"
        stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
      </svg>
      <span class="card-title">Skills</span>
    </button>
  </div>
</div>
'''