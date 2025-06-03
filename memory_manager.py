#!/usr/bin/env python3
"""
Enhanced Memory System for Claude-to-Claude Conversations
Provides conversation summarization, knowledge graphs, and context retrieval
"""

import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import logging
import hashlib
import re

logger = logging.getLogger(__name__)

@dataclass
class ConversationChunk:
    """Represents a chunk of conversation for processing"""
    id: str
    start_time: datetime
    end_time: datetime
    messages: List[Dict[str, Any]]
    topics: List[str] = None
    summary: str = None
    importance_score: float = 0.0
    code_changes: List[str] = None

@dataclass 
class KnowledgeNode:
    """Represents a node in our knowledge graph"""
    id: str
    topic: str
    description: str
    related_chunks: List[str]
    connections: List[str] = None
    last_updated: datetime = None

class ConversationSummarizer:
    """Handles chunking and summarizing conversations"""
    
    def __init__(self, chunk_size: int = 10):
        self.chunk_size = chunk_size
        self.current_chunk = []
        
    def add_message(self, message: Dict[str, Any]) -> Optional[ConversationChunk]:
        """Add message to current chunk, return completed chunk if ready"""
        self.current_chunk.append(message)
        
        if len(self.current_chunk) >= self.chunk_size:
            chunk = self._create_chunk(self.current_chunk)
            self.current_chunk = []
            return chunk
        return None
    
    def _create_chunk(self, messages: List[Dict[str, Any]]) -> ConversationChunk:
        """Create a conversation chunk from messages"""
        chunk_id = hashlib.md5(str(messages[0]).encode()).hexdigest()[:8]
        start_time = datetime.now()  # TODO: extract from messages
        end_time = datetime.now()
        
        return ConversationChunk(
            id=chunk_id,
            start_time=start_time, 
            end_time=end_time,
            messages=messages,
            topics=self._extract_topics(messages),
            summary=self._generate_summary(messages),
            importance_score=self._calculate_importance(messages),
            code_changes=self._extract_code_changes(messages)
        )
    
    def _extract_topics(self, messages: List[Dict[str, Any]]) -> List[str]:
        """Extract key topics from messages"""
        # Simple keyword extraction for now - can be enhanced with NLP
        text = ' '.join([msg.get('content', '') for msg in messages])
        
        # Look for common programming and improvement topics
        topic_patterns = [
            r'\b(memory|context|management)\b',
            r'\b(improvement|enhance|optimize)\b', 
            r'\b(conversation|dialogue|chat)\b',
            r'\b(code|programming|implementation)\b',
            r'\b(git|commit|push|repository)\b',
            r'\b(testing|debug|error|fix)\b'
        ]
        
        topics = []
        for pattern in topic_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                topics.append(pattern.strip('\\b()'))
                
        return list(set(topics))  # Remove duplicates
    
    def _generate_summary(self, messages: List[Dict[str, Any]]) -> str:
        """Generate summary of conversation chunk"""
        # Basic summary - extract key sentences
        content = ' '.join([msg.get('content', '') for msg in messages])
        sentences = content.split('.')
        
        # Take first and last sentences as basic summary
        if len(sentences) > 2:
            return f"{sentences[0].strip()}. ... {sentences[-2].strip()}."
        return content[:200] + '...' if len(content) > 200 else content
    
    def _calculate_importance(self, messages: List[Dict[str, Any]]) -> float:
        """Calculate importance score for chunk"""
        content = ' '.join([msg.get('content', '') for msg in messages])
        
        # Higher scores for implementation, decisions, errors
        importance_keywords = {
            'implement': 2.0,
            'decision': 1.5, 
            'error': 1.5,
            'bug': 1.5,
            'fix': 1.2,
            'improve': 1.0,
            'create': 1.0
        }
        
        score = 0.0
        for keyword, weight in importance_keywords.items():
            score += content.lower().count(keyword) * weight
            
        return min(score, 10.0)  # Cap at 10
    
    def _extract_code_changes(self, messages: List[Dict[str, Any]]) -> List[str]:
        """Extract mentions of code changes"""
        changes = []
        for msg in messages:
            content = msg.get('content', '')
            # Look for file mentions, function names, etc.
            file_matches = re.findall(r'(\w+\.py|\w+\.md|\w+\.sh)', content)
            changes.extend(file_matches)
        return list(set(changes))


