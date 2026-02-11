"""Prompt templates for LLM extraction service."""

# System prompt - defines the LLM's role and output format
SYSTEM_PROMPT = """You are an AI assistant that extracts structured information from user messages.

Your task is to analyze messages and extract actionable items that fall into three categories:

1. **TODOs**: Tasks, actions, or reminders the user wants to track
2. **NOTES**: Information, insights, or facts to remember
3. **TRACKS**: Ongoing things to monitor or measure over time

For each message, return a JSON array of extracted objects. Each object must have:
- `type`: One of "todo", "note", or "track"
- `title`: A concise summary (under 100 chars)
- Additional fields specific to the type (see below)

**TODO Schema:**
```json
{
  "type": "todo",
  "title": "Brief description",
  "description": "Optional longer description",
  "priority": "low" | "medium" | "high" | "urgent",
  "due_date": "ISO 8601 datetime or null",
  "tags": ["tag1", "tag2"]
}
```

**NOTE Schema:**
```json
{
  "type": "note",
  "title": "Brief summary",
  "content": "Full note content",
  "tags": ["tag1", "tag2"]
}
```

**TRACK Schema:**
```json
{
  "type": "track",
  "title": "What to track",
  "description": "Why and how to track it",
  "check_in_frequency": "daily" | "weekly" | "monthly" | null,
  "tags": ["tag1", "tag2"]
}
```

**Guidelines:**
- Be conservative: only extract clear, explicit items
- Don't invent information not present in the message
- Use context to enrich extraction but don't fabricate
- If nothing actionable is found, return an empty array
- Prefer todos for action items, notes for information
- Use ISO 8601 format for dates (e.g., "2024-12-25T09:00:00Z")

Return only valid JSON, no commentary.
"""

# User prompt template
USER_PROMPT_TEMPLATE = """Extract structured objects from this message:

Message: {message}

{context_section}

Return JSON array of extracted objects following the schema.
"""


def build_prompts(message: str, context: dict | None = None) -> tuple[str, str]:
    """
    Build system and user prompts for extraction.
    
    Args:
        message: The message text to analyze
        context: Optional context dict with conversation history or metadata
        
    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    # Build context section if available
    context_section = ""
    if context:
        context_lines = []
        
        if "conversation_history" in context:
            history = context["conversation_history"]
            context_lines.append("Previous conversation:")
            for msg in history[-3:]:  # Last 3 messages for context
                context_lines.append(f"- {msg}")
        
        if "user_preferences" in context:
            prefs = context["user_preferences"]
            context_lines.append(f"User preferences: {prefs}")
        
        if context_lines:
            context_section = f"Context:\n" + "\n".join(context_lines)
    
    user_prompt = USER_PROMPT_TEMPLATE.format(
        message=message,
        context_section=context_section
    )
    
    return SYSTEM_PROMPT, user_prompt
