"""OpenAI integration for LLM-based extraction."""

import asyncio
import json
import logging
from typing import Optional
from uuid import uuid4

import openai

from shared.contracts.objects import ExtractionResult, LLMServiceError
from shared.contracts.protocols import LLMServiceProtocol, EventStoreProtocol
from shared.contracts.events import ArtifactRecordedEvent, ArtifactType
from services.extraction.prompts import build_prompts

logger = logging.getLogger(__name__)


# OpenAI pricing per 1000 tokens (as of Dec 2024)
# TODO - get latest model list and pricing as per Feb 2026
PRICING = {
    "gpt-4o-mini": {"prompt": 0.00015, "completion": 0.0006},
    "gpt-4o": {"prompt": 0.0025, "completion": 0.01},
}


def calculate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """
    Calculate USD cost for an API call.

    Args:
        model: Model name (e.g., "gpt-4o-mini")
        prompt_tokens: Number of tokens in prompt
        completion_tokens: Number of tokens in completion

    Returns:
        Cost in USD
    """
    rates = PRICING.get(model, PRICING["gpt-4o-mini"])
    prompt_cost = (prompt_tokens / 1000) * rates["prompt"]
    completion_cost = (completion_tokens / 1000) * rates["completion"]
    return prompt_cost + completion_cost


class OpenAILLMService(LLMServiceProtocol):
    """OpenAI-based LLM service with retry, rate limiting, and cost tracking."""

    def __init__(
        self,
        event_store: EventStoreProtocol,
        api_key: str,
        model: str = "gpt-4o-mini",
        max_tokens: int = 1000,
        temperature: float = 0.7,
        max_retries: int = 3,
        retry_base_delay: float = 1.0,
    ):
        """
        Initialize OpenAI LLM service.

        Args:
            event_store: Event store for recording artifacts
            api_key: OpenAI API key
            model: Model name (default: gpt-4o-mini)
            max_tokens: Maximum tokens in completion
            temperature: Sampling temperature (0-2)
            max_retries: Maximum retry attempts on failures
            retry_base_delay: Base delay in seconds for exponential backoff
        """
        self.event_store = event_store
        self.client = openai.AsyncOpenAI(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.max_retries = max_retries
        self.retry_base_delay = retry_base_delay

    async def extract_objects(
        self, message: str, context: Optional[dict] = None
    ) -> ExtractionResult:
        """
        Extract structured objects from message using OpenAI.

        Args:
            message: Message text to analyze
            context: Optional context (conversation history, preferences)

        Returns:
            ExtractionResult with extracted objects and metadata

        Raises:
            LLMServiceError: On unrecoverable API errors
        """
        system_prompt, user_prompt = build_prompts(message, context)

        # Record prompt artifact
        prompt_artifact_id = await self._record_artifact(
            artifact_type=ArtifactType.LLM_PROMPT,
            content=json.dumps({"system": system_prompt, "user": user_prompt}),
            metadata={
                "model": self.model,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
            },
        )

        # Call OpenAI with retry logic
        for attempt in range(self.max_retries):
            try:
                response = await self._call_openai(system_prompt, user_prompt)

                # Parse response
                content = response.choices[0].message.content
                usage = response.usage

                # Record response artifact
                response_artifact_id = await self._record_artifact(
                    artifact_type=ArtifactType.LLM_RESPONSE,
                    content=json.dumps({"raw_response": content}),
                    metadata={
                        "model": response.model,
                        "prompt_tokens": usage.prompt_tokens,
                        "completion_tokens": usage.completion_tokens,
                        "total_tokens": usage.total_tokens,
                        "finish_reason": response.choices[0].finish_reason,
                    },
                )

                # Parse JSON response
                try:
                    parsed = json.loads(content)

                    # Handle different response formats
                    if isinstance(parsed, list):
                        # Direct array format
                        objects = parsed
                    elif isinstance(parsed, dict):
                        # Preferred format (since response_format forces a JSON object)
                        # {"objects": [ ... ]}
                        candidate = (
                            parsed.get("objects")
                            or parsed.get("extracted_items")
                            or parsed.get("items")
                        )

                        if isinstance(candidate, list):
                            objects = candidate
                        elif isinstance(candidate, dict):
                            objects = [candidate]
                        elif candidate is not None:
                            objects = []
                        else:
                            # Some models may still return a single object like:
                            # {"type": "todo", "title": "...", ...}
                            # Treat that as one extracted object.
                            if "type" in parsed and "title" in parsed:
                                objects = [parsed]
                            # Or a wrapper like {"result": [ ... ]} / {"result": { ... }}
                            elif len(parsed) == 1:
                                only_value = next(iter(parsed.values()))
                                if isinstance(only_value, list):
                                    objects = only_value
                                elif isinstance(only_value, dict):
                                    objects = [only_value]
                                else:
                                    objects = []
                            else:
                                objects = []
                    else:
                        objects = []

                    # Final sanity filter: keep dict objects only
                    if not isinstance(objects, list):
                        objects = []
                    objects = [obj for obj in objects if isinstance(obj, dict)]

                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse LLM response as JSON: {e}")
                    objects = []

                # Calculate cost
                cost_usd = calculate_cost(
                    response.model, usage.prompt_tokens, usage.completion_tokens
                )

                logger.info(
                    f"LLM extraction complete: {len(objects)} objects, "
                    f"{usage.total_tokens} tokens, ${cost_usd:.4f}"
                )

                return ExtractionResult(
                    objects=objects,
                    confidence=0.9,  # High confidence for successfully parsed response
                    model_used=response.model,
                    tokens_used=usage.total_tokens,
                    prompt_artifact_id=prompt_artifact_id,
                    response_artifact_id=response_artifact_id,
                    extraction_metadata={
                        "prompt_tokens": usage.prompt_tokens,
                        "completion_tokens": usage.completion_tokens,
                        "cost_usd": cost_usd,
                        "finish_reason": response.choices[0].finish_reason,
                    },
                )

            except openai.AuthenticationError as e:
                # Fail fast - no retry for auth errors
                logger.error(f"OpenAI authentication failed: {e}")
                raise LLMServiceError("Invalid OpenAI API key") from e

            except openai.RateLimitError as e:
                logger.warning(f"Rate limit hit (attempt {attempt + 1}/{self.max_retries})")
                if attempt < self.max_retries - 1:
                    delay = self._get_retry_delay(e, attempt)
                    await asyncio.sleep(delay)
                else:
                    logger.error("Rate limit exceeded after max retries")
                    raise LLMServiceError("Rate limit exceeded") from e

            except openai.APIConnectionError as e:
                logger.warning(f"Connection error (attempt {attempt + 1}/{self.max_retries})")
                if attempt < self.max_retries - 1:
                    delay = self.retry_base_delay * (2**attempt)
                    await asyncio.sleep(delay)
                else:
                    logger.error("Connection failed after max retries")
                    raise LLMServiceError("Connection failed") from e

            except openai.APIError as e:
                logger.warning(f"OpenAI API error (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1 and e.status_code >= 500:
                    # Retry on 5xx server errors
                    delay = self.retry_base_delay * (2**attempt)
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"API error after max retries: {e}")
                    raise LLMServiceError(f"API error: {e}") from e

        # Fallback: return empty result if all retries exhausted
        logger.error("All retry attempts exhausted")
        return ExtractionResult(
            objects=[],
            confidence=0.0,
            model_used="error",
            tokens_used=0,
            prompt_artifact_id=prompt_artifact_id,
            response_artifact_id=uuid4(),  # Placeholder
            extraction_metadata={"error": "max_retries_exceeded"},
        )

    async def _call_openai(self, system_prompt: str, user_prompt: str):
        """
        Make the actual OpenAI API call.

        Args:
            system_prompt: System message
            user_prompt: User message

        Returns:
            OpenAI API response
        """
        return await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            response_format={"type": "json_object"},  # Force JSON output
        )

    async def _record_artifact(
        self, artifact_type: ArtifactType, content: str, metadata: dict
    ) -> uuid4:
        """
        Record an artifact in the event store.

        Args:
            artifact_type: Type of artifact (prompt or response)
            content: Artifact content
            metadata: Artifact metadata

        Returns:
            UUID of the recorded artifact event
        """
        event = ArtifactRecordedEvent(
            artifact_type=artifact_type, content=content, metadata=metadata
        )
        return await self.event_store.append(event)

    def _get_retry_delay(self, error: openai.RateLimitError, attempt: int) -> float:
        """
        Calculate retry delay respecting rate limit headers.

        Args:
            error: Rate limit error with headers
            attempt: Current attempt number

        Returns:
            Delay in seconds
        """
        # Check for retry-after header
        if hasattr(error, "response") and error.response:
            retry_after = error.response.headers.get("retry-after")
            if retry_after:
                try:
                    return float(retry_after)
                except ValueError:
                    pass

        # Fallback to exponential backoff
        return self.retry_base_delay * (2**attempt)
