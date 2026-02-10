# ADR: LLM Integration Architecture and Artifact Recording

**Status**: Proposed  
**Date**: February 10, 2026  
**Issue**: #10  
**Milestone**: M1

## Context

Milestone 0 established a keyword-based extraction stub. Milestone 1 requires real LLM-based extraction using OpenAI API to intelligently identify and extract todos, notes, and tracks from conversational text.

### Requirements
- Replace keyword stub with OpenAI API integration
- Record all LLM interactions as artifacts (system invariant)
- Handle API failures gracefully (network, rate limits, quota)
- Enable prompt iteration without code changes
- Maintain human authority principle
- Support testing without live API calls

### Constraints
- Event log remains immutable source of truth
- Must preserve append-only semantics
- OpenAI only for M1 (no multi-provider support)
- Single-user system (no tenant isolation)

---

## Decision

### 1. LLM Client Abstraction

Introduce `LLMServiceProtocol` as a contract, with two implementations:

**Protocol:** `shared/contracts/protocols.py`
```python
class LLMServiceProtocol(ABC):
    """Contract for LLM-based extraction operations."""
    
    @abstractmethod
    async def extract_objects(
        self,
        message: str,
        context: Optional[dict] = None
    ) -> ExtractionResult:
        """
        Extract structured objects from message using LLM.
        
        Args:
            message: Message text to analyze
            context: Optional context (conversation history, user prefs)
            
        Returns:
            ExtractionResult with extracted objects and metadata
            
        Raises:
            LLMServiceError: On unrecoverable API errors
        """
        pass
```

**Implementations:**
- `OpenAILLMService` - Production implementation using OpenAI SDK
- `MockLLMService` - Test implementation with predictable responses

**Rationale**: Abstraction enables testing, future provider flexibility, and clear service boundaries.

---

### 2. Extraction Result Contract

New dataclass in `shared/contracts/objects.py`:

```python
@dataclass
class ExtractionResult:
    """Result of LLM extraction operation."""
    
    objects: list[dict]              # Raw extracted object dicts
    confidence: Optional[float]      # Overall extraction confidence (0-1)
    model_used: str                  # e.g. "gpt-4o-mini"
    tokens_used: int                 # Total tokens consumed
    prompt_artifact_id: UUID         # Event ID of prompt artifact
    response_artifact_id: UUID       # Event ID of response artifact
    extraction_metadata: dict        # Additional LLM-specific data
```

**Rationale**: Explicit contract ensures all LLM interactions are tracked and provides cost/usage visibility.

---

### 3. Artifact Recording Pattern

**Flow:**
```
1. Extract requested → Record prompt as ArtifactRecordedEvent
2. Call OpenAI API
3. Record response as ArtifactRecordedEvent
4. Parse response and extract objects
5. Record each object as ObjectExtractedEvent
```

**Artifact Events:**
```python
# Before API call
prompt_event = ArtifactRecordedEvent(
    artifact_type=ArtifactType.LLM_PROMPT,
    content=full_prompt_text,
    related_event_id=message_event_id,
    metadata={
        "model": "gpt-4o-mini",
        "temperature": 0.7,
        "max_tokens": 1000
    }
)

# After API call
response_event = ArtifactRecordedEvent(
    artifact_type=ArtifactType.LLM_RESPONSE,
    content=full_response_text,
    related_event_id=prompt_event.event_id,
    metadata={
        "model": response.model,
        "tokens_used": response.usage.total_tokens,
        "prompt_tokens": response.usage.prompt_tokens,
        "completion_tokens": response.usage.completion_tokens,
        "cost_usd": calculate_cost(response),
        "finish_reason": response.choices[0].finish_reason
    }
)
```

**Rationale**: Full traceability of LLM interactions, enables prompt debugging, cost analysis, and audit trail.

---

### 4. Prompt Management Strategy

**Approach**: Prompts in Python code with template variables.

**Location**: `services/extraction/prompts.py`

```python
SYSTEM_PROMPT = """You are an extraction assistant for a personal decision support system.

Your role is to analyze user messages and extract structured objects.

Object Types:
- Todo: Explicit actions, commitments, or tasks to complete
- Note: Information worth retaining, facts, references, ideas  
- Track: Intentions to monitor something over time

Rules:
- Extract all relevant objects from the message
- Assign appropriate priority to todos (urgent, high, medium, low)
- Infer due dates if mentioned ("by Friday", "tomorrow", "next week")
- Add relevant tags to help with categorization
- Be conservative: only extract clear, unambiguous objects
- Return ONLY valid JSON array of objects

Output Format:
[
  {
    "type": "todo",
    "title": "Brief action statement",
    "description": "Optional longer description",
    "priority": "medium",
    "due_date": "2026-02-15",
    "tags": ["work", "urgent"]
  }
]
"""

USER_PROMPT_TEMPLATE = """Message: "{message}"
Author: {author}
Timestamp: {timestamp}
{context_section}

Extract all todos, notes, and tracks from this message.
Return only valid JSON array."""

def build_extraction_prompt(
    message: str,
    author: str,
    timestamp: datetime,
    context: Optional[dict] = None
) -> tuple[str, str]:
    """Build system and user prompts for extraction."""
    
    context_section = ""
    if context:
        context_section = f"\nConversation context: {context.get('summary', '')}"
    
    user_prompt = USER_PROMPT_TEMPLATE.format(
        message=message,
        author=author,
        timestamp=timestamp.isoformat(),
        context_section=context_section
    )
    
    return SYSTEM_PROMPT, user_prompt
```

**Rationale**: 
- Simple to iterate during development
- Version controlled with code
- Can migrate to files or DB later if needed
- Clear separation from business logic

**Future Evolution**: If prompt iteration becomes frequent, migrate to YAML/JSON files or event log.

---

### 5. Error Handling Strategy

**Error Categories and Responses:**

| Error Type | HTTP Code | Strategy | User Impact |
|------------|-----------|----------|-------------|
| Network timeout | - | Retry 3x with exponential backoff (1s, 2s, 4s) | Delayed extraction |
| Rate limit | 429 | Respect `retry-after` header, queue request | Delayed extraction |
| Quota exceeded | 429 | Log error, return empty result, notify user | No extraction |
| Invalid API key | 401 | Fail fast, clear error message | System halt |
| Malformed JSON response | - | Log, record artifact, return empty | Extraction fails gracefully |
| API service error | 500+ | Retry 1x after 5s, then fail | Extraction fails gracefully |

**Implementation:**
```python
class OpenAILLMService:
    MAX_RETRIES = 3
    RETRY_BASE_DELAY = 1.0
    
    async def extract_objects(self, message: str, context=None) -> ExtractionResult:
        for attempt in range(self.MAX_RETRIES):
            try:
                response = await self._call_openai(message, context)
                return self._parse_response(response)
                
            except openai.RateLimitError as e:
                if attempt < self.MAX_RETRIES - 1:
                    delay = self._get_retry_delay(e, attempt)
                    await asyncio.sleep(delay)
                else:
                    raise LLMServiceError("Rate limit exceeded") from e
                    
            except openai.APIConnectionError as e:
                if attempt < self.MAX_RETRIES - 1:
                    delay = self.RETRY_BASE_DELAY * (2 ** attempt)
                    await asyncio.sleep(delay)
                else:
                    raise LLMServiceError("Connection failed") from e
                    
            except openai.AuthenticationError as e:
                # Fail fast - no retry
                raise LLMServiceError("Invalid API key") from e
        
        # Fallback: return empty result with error metadata
        return ExtractionResult(
            objects=[],
            confidence=0.0,
            model_used="error",
            tokens_used=0,
            extraction_metadata={"error": "max_retries_exceeded"}
        )
```

**Rationale**: Graceful degradation maintains system stability, artifact recording ensures debugging capability.

---

### 6. Rate Limiting

**Strategy**: Client-side rate limiting with token bucket algorithm.

**Configuration:**
```bash
OPENAI_RATE_LIMIT_RPM=10          # Requests per minute
OPENAI_RATE_LIMIT_TPM=150000      # Tokens per minute
```

**Implementation:**
```python
class RateLimiter:
    def __init__(self, requests_per_minute: int, tokens_per_minute: int):
        self.rpm_bucket = TokenBucket(requests_per_minute, refill_rate=rpm/60)
        self.tpm_bucket = TokenBucket(tokens_per_minute, refill_rate=tpm/60)
    
    async def acquire(self, estimated_tokens: int):
        """Block until both request and token capacity available."""
        await self.rpm_bucket.acquire(1)
        await self.tpm_bucket.acquire(estimated_tokens)
```

**Rationale**: Prevents API quota exhaustion, provides backpressure for batch operations.

---

### 7. Cost Tracking

**Mechanism**: Record token usage in artifact metadata, provide query interface.

**Cost Calculation:**
```python
PRICING = {
    "gpt-4o-mini": {
        "prompt": 0.00015 / 1000,      # per token
        "completion": 0.0006 / 1000
    },
    "gpt-4o": {
        "prompt": 0.0025 / 1000,
        "completion": 0.01 / 1000
    }
}

def calculate_cost(model: str, usage: dict) -> float:
    """Calculate USD cost for API call."""
    rates = PRICING.get(model, PRICING["gpt-4o-mini"])
    prompt_cost = usage["prompt_tokens"] * rates["prompt"]
    completion_cost = usage["completion_tokens"] * rates["completion"]
    return prompt_cost + completion_cost
```

**Monitoring:**
- Daily cost warnings via `QueryService.get_stats()`
- Cumulative cost in projection stats
- Per-extraction cost in artifact metadata

**Configuration:**
```bash
LLM_DAILY_COST_WARNING_USD=1.0
LLM_DAILY_COST_LIMIT_USD=10.0
```

**Rationale**: Cost visibility prevents unexpected bills, enables informed decisions about model selection.

---

### 8. Configuration

**Environment Variables:**
```bash
# API Configuration
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
OPENAI_MAX_TOKENS=1000
OPENAI_TEMPERATURE=0.7

# Rate Limiting
OPENAI_RATE_LIMIT_RPM=10
OPENAI_RATE_LIMIT_TPM=150000

# Error Handling
LLM_MAX_RETRIES=3
LLM_RETRY_BASE_DELAY=1.0

# Cost Control
LLM_DAILY_COST_WARNING_USD=1.0
LLM_DAILY_COST_LIMIT_USD=10.0
```

**Defaults**: Use `gpt-4o-mini` for cost efficiency, conservative rate limits.

---

### 9. Testing Strategy

**Mock LLM Service:**
```python
class MockLLMService(LLMServiceProtocol):
    """Predictable LLM for testing."""
    
    def __init__(self, responses: Optional[dict] = None):
        self.responses = responses or self._default_responses()
        self.call_count = 0
    
    async def extract_objects(self, message: str, context=None) -> ExtractionResult:
        self.call_count += 1
        
        # Pattern matching on message keywords
        objects = []
        if "todo" in message.lower():
            objects.append({"type": "todo", "title": message})
        if "note" in message.lower():
            objects.append({"type": "note", "title": message, "content": message})
        
        # Generate fake artifact IDs
        prompt_id = uuid4()
        response_id = uuid4()
        
        return ExtractionResult(
            objects=objects,
            confidence=0.95,
            model_used="mock-model",
            tokens_used=100,
            prompt_artifact_id=prompt_id,
            response_artifact_id=response_id,
            extraction_metadata={"mock": True}
        )
```

**Test Coverage:**
- Unit tests: All error paths, rate limiting, cost calculation
- Integration tests: Real API calls with test key (gated by env var)
- Mock tests: All business logic without API dependency

---

## Consequences

### Positive
- ✅ Complete LLM interaction traceability via artifacts
- ✅ Testability without API dependencies
- ✅ Cost visibility and control
- ✅ Graceful degradation on failures
- ✅ Clear service boundaries enable parallel development

### Negative
- ⚠️ Additional events per extraction (prompt + response artifacts)
- ⚠️ Token bucket adds complexity (but necessary)
- ⚠️ Prompt in code requires code change to iterate (acceptable for M1)

### Risks
- **Prompt quality**: Initial prompts may need tuning
  - Mitigation: Start conservative, iterate based on real usage
- **API costs**: Unexpected usage spikes
  - Mitigation: Daily limits, monitoring, warnings
- **Rate limiting**: May delay bulk operations
  - Mitigation: Configure limits appropriately, add batch processing later

---

## Implementation Checklist

- [ ] Add `LLMServiceProtocol` to `shared/contracts/protocols.py`
- [ ] Add `ExtractionResult` to `shared/contracts/objects.py`  
- [ ] Create `services/extraction/prompts.py` with templates
- [ ] Create `services/extraction/llm_client.py` with abstraction
- [ ] Create `services/extraction/openai_client.py` with OpenAI implementation
- [ ] Create `services/extraction/mock_llm.py` for testing
- [ ] Refactor `services/extraction/service.py` to use LLM client
- [ ] Add rate limiting implementation
- [ ] Add cost tracking utilities
- [ ] Update `.env.example` with LLM configuration
- [ ] Document in `docs/ARCHITECTURE.md`
- [ ] Create tests for all error scenarios

---

## Related Issues

- **Blocks**: #13 (Implement OpenAI Extraction Service)
- **Related**: #9 (Milestone 1 Meta-Issue)

---

## Approval

- [ ] Architect reviewed
- [ ] Contracts validated
- [ ] Ready for developer implementation

