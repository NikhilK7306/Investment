"""LLM Provider abstractions for multi-provider support."""

import os
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type, TypeVar
from enum import Enum

from pydantic import BaseModel, ValidationError

from app.core.config.settings import get_settings

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)


class LLMProviderType(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"


@dataclass
class LLMConfig:
    """Configuration for LLM provider."""
    provider: LLMProviderType
    model: str
    api_key: str
    temperature: float = 0.1
    max_tokens: int = 4000
    timeout: int = 60
    max_retries: int = 3
    organization: Optional[str] = None
    base_url: Optional[str] = None


@dataclass
class LLMResponse:
    """Response from LLM provider."""
    content: str
    model: str
    provider: LLMProviderType
    tokens_used: int = 0
    cost_usd: float = 0.0
    raw_response: Optional[Dict] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, config: LLMConfig):
        self.config = config
        self._client = None

    @property
    @abstractmethod
    def provider_type(self) -> LLMProviderType:
        """Get provider type."""
        pass

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the provider client."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close the provider client."""
        pass

    @abstractmethod
    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_model: Optional[Type[T]] = None,
    ) -> LLMResponse:
        """Complete a prompt with optional structured output."""
        pass

    @abstractmethod
    async def complete_with_json_schema(
        self,
        prompt: str,
        json_schema: Dict[str, Any],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Complete a prompt with JSON schema constrained output."""
        pass

    def _estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost based on token usage. Override in subclasses."""
        return 0.0

    def _parse_structured_output(
        self,
        content: str,
        response_model: Type[T],
    ) -> T:
        """Parse structured output from LLM response."""
        try:
            # Try to extract JSON from content
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = content[json_start:json_end]
                data = json.loads(json_str)
                return response_model(**data)
        except (json.JSONDecodeError, ValidationError) as e:
            logger.warning(f"Failed to parse structured output: {e}")

        # Fallback: try parsing entire content as JSON
        try:
            data = json.loads(content)
            return response_model(**data)
        except (json.JSONDecodeError, ValidationError):
            pass

        raise ValueError(f"Could not parse structured output: {content[:200]}")


class OpenAIProvider(LLMProvider):
    """OpenAI API provider."""

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        # Pricing per 1M tokens (as of 2024)
        self._pricing = {
            "gpt-4o": {"input": 5.00, "output": 15.00},
            "gpt-4o-mini": {"input": 0.15, "output": 0.60},
            "gpt-4-turbo": {"input": 10.00, "output": 30.00},
            "gpt-4": {"input": 30.00, "output": 60.00},
            "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
        }

    @property
    def provider_type(self) -> LLMProviderType:
        return LLMProviderType.OPENAI

    async def initialize(self) -> None:
        try:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(
                api_key=self.config.api_key,
                organization=self.config.organization,
                base_url=self.config.base_url,
                timeout=self.config.timeout,
                max_retries=self.config.max_retries,
            )
        except ImportError:
            raise RuntimeError("openai package not installed. Run: pip install openai")

    async def close(self) -> None:
        if self._client:
            await self._client.close()
            self._client = None

    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_model: Optional[Type[T]] = None,
    ) -> LLMResponse:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # If response_model is provided, use structured output
        if response_model:
            # Add JSON schema instruction to prompt
            schema = response_model.model_json_schema()
            json_instruction = (
                f"\n\nRespond with a valid JSON object matching this schema:\n"
                f"{json.dumps(schema, indent=2)}"
            )
            messages[-1]["content"] += json_instruction

        response = await self._client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            temperature=temperature or self.config.temperature,
            max_tokens=max_tokens or self.config.max_tokens,
            response_format={"type": "json_object"} if response_model else None,
        )

        choice = response.choices[0]
        content = choice.message.content or ""

        # Parse structured output if model provided
        if response_model:
            try:
                parsed = self._parse_structured_output(content, response_model)
                content = parsed.model_dump_json()
            except ValueError:
                # If parsing fails, return raw content
                pass

        return LLMResponse(
            content=content,
            model=self.config.model,
            provider=self.provider_type,
            tokens_used=response.usage.total_tokens if response.usage else 0,
            cost_usd=self._estimate_cost(
                response.usage.prompt_tokens if response.usage else 0,
                response.usage.completion_tokens if response.usage else 0,
            ),
            raw_response=response.model_dump(),
        )

    async def complete_with_json_schema(
        self,
        prompt: str,
        json_schema: Dict[str, Any],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = await self._client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            temperature=temperature or self.config.temperature,
            max_tokens=max_tokens or self.config.max_tokens,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "response",
                    "schema": json_schema,
                    "strict": True,
                },
            },
        )

        choice = response.choices[0]
        content = choice.message.content or ""

        return LLMResponse(
            content=content,
            model=self.config.model,
            provider=self.provider_type,
            tokens_used=response.usage.total_tokens if response.usage else 0,
            cost_usd=self._estimate_cost(
                response.usage.prompt_tokens if response.usage else 0,
                response.usage.completion_tokens if response.usage else 0,
            ),
            raw_response=response.model_dump(),
        )

    def _estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        pricing = self._pricing.get(self.config.model, {"input": 0, "output": 0})
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        return input_cost + output_cost


class AnthropicProvider(LLMProvider):
    """Anthropic/Claude API provider."""

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        # Pricing per 1M tokens (as of 2024)
        self._pricing = {
            "claude-3-5-sonnet-20241022": {"input": 3.00, "output": 15.00},
            "claude-3-5-haiku-20241022": {"input": 0.80, "output": 4.00},
            "claude-3-opus-20240229": {"input": 15.00, "output": 75.00},
            "claude-3-sonnet-20240229": {"input": 3.00, "output": 15.00},
            "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
        }

    @property
    def provider_type(self) -> LLMProviderType:
        return LLMProviderType.ANTHROPIC

    async def initialize(self) -> None:
        try:
            from anthropic import AsyncAnthropic
            self._client = AsyncAnthropic(
                api_key=self.config.api_key,
                timeout=self.config.timeout,
                max_retries=self.config.max_retries,
            )
        except ImportError:
            raise RuntimeError("anthropic package not installed. Run: pip install anthropic")

    async def close(self) -> None:
        if self._client:
            await self._client.close()
            self._client = None

    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_model: Optional[Type[T]] = None,
    ) -> LLMResponse:
        messages = [{"role": "user", "content": prompt}]

        if response_model:
            schema = response_model.model_json_schema()
            json_instruction = (
                f"\n\nRespond with a valid JSON object matching this schema:\n"
                f"{json.dumps(schema, indent=2)}"
            )
            prompt += json_instruction

        response = await self._client.messages.create(
            model=self.config.model,
            messages=messages,
            system=system_prompt or "",
            temperature=temperature or self.config.temperature,
            max_tokens=max_tokens or self.config.max_tokens,
        )

        content = response.content[0].text if response.content else ""

        if response_model:
            try:
                parsed = self._parse_structured_output(content, response_model)
                content = parsed.model_dump_json()
            except ValueError:
                pass

        return LLMResponse(
            content=content,
            model=self.config.model,
            provider=self.provider_type,
            tokens_used=response.usage.input_tokens + response.usage.output_tokens,
            cost_usd=self._estimate_cost(response.usage.input_tokens, response.usage.output_tokens),
            raw_response=response.model_dump(),
        )

    async def complete_with_json_schema(
        self,
        prompt: str,
        json_schema: Dict[str, Any],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        # Anthropic doesn't have native JSON schema support
        # Use tool use or prompt engineering
        schema_prompt = (
            f"\n\nRespond with a valid JSON object matching this schema:\n"
            f"{json.dumps(json_schema, indent=2)}"
        )
        return await self.complete(
            prompt + schema_prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    def _estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        pricing = self._pricing.get(self.config.model, {"input": 0, "output": 0})
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        return input_cost + output_cost


class GoogleProvider(LLMProvider):
    """Google Gemini API provider."""

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        # Pricing per 1M tokens (as of 2024)
        self._pricing = {
            "gemini-1.5-pro": {"input": 3.50, "output": 10.50},
            "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
            "gemini-1.0-pro": {"input": 0.50, "output": 1.50},
        }

    @property
    def provider_type(self) -> LLMProviderType:
        return LLMProviderType.GOOGLE

    async def initialize(self) -> None:
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.config.api_key)
            self._client = genai.GenerativeModel(self.config.model)
        except ImportError:
            raise RuntimeError("google-generativeai package not installed. Run: pip install google-generativeai")

    async def close(self) -> None:
        self._client = None

    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_model: Optional[Type[T]] = None,
    ) -> LLMResponse:
        # Combine system prompt and user prompt
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        if response_model:
            schema = response_model.model_json_schema()
            full_prompt += (
                f"\n\nRespond with a valid JSON object matching this schema:\n"
                f"{json.dumps(schema, indent=2)}"
            )

        generation_config = {
            "temperature": temperature or self.config.temperature,
            "max_output_tokens": max_tokens or self.config.max_tokens,
        }

        response = await self._client.generate_content_async(
            full_prompt,
            generation_config=generation_config,
        )

        content = response.text or ""

        if response_model:
            try:
                parsed = self._parse_structured_output(content, response_model)
                content = parsed.model_dump_json()
            except ValueError:
                pass

        # Estimate tokens (rough approximation)
        input_tokens = len(full_prompt) // 4
        output_tokens = len(content) // 4

        return LLMResponse(
            content=content,
            model=self.config.model,
            provider=self.provider_type,
            tokens_used=input_tokens + output_tokens,
            cost_usd=self._estimate_cost(input_tokens, output_tokens),
            raw_response={"text": content},
        )

    async def complete_with_json_schema(
        self,
        prompt: str,
        json_schema: Dict[str, Any],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        schema_prompt = (
            f"\n\nRespond with a valid JSON object matching this schema:\n"
            f"{json.dumps(json_schema, indent=2)}"
        )
        return await self.complete(
            prompt + schema_prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    def _estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        pricing = self._pricing.get(self.config.model, {"input": 0, "output": 0})
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        return input_cost + output_cost


class LLMProviderFactory:
    """Factory for creating LLM providers from configuration."""

    _providers: Dict[LLMProviderType, Type[LLMProvider]] = {
        LLMProviderType.OPENAI: OpenAIProvider,
        LLMProviderType.ANTHROPIC: AnthropicProvider,
        LLMProviderType.GOOGLE: GoogleProvider,
    }

    @classmethod
    def register_provider(
        cls,
        provider_type: LLMProviderType,
        provider_class: Type[LLMProvider],
    ) -> None:
        """Register a custom provider."""
        cls._providers[provider_type] = provider_class

    @classmethod
    def create(cls, config: LLMConfig) -> LLMProvider:
        """Create provider instance from config."""
        provider_class = cls._providers.get(config.provider)
        if not provider_class:
            raise ValueError(f"Unknown provider: {config.provider}")
        return provider_class(config)

    @classmethod
    def create_from_env(cls, provider: LLMProviderType = None) -> LLMProvider:
        """Create provider from environment variables."""
        settings = get_settings()

        provider = provider or LLMProviderType(settings.default_llm_provider or "openai")

        if provider == LLMProviderType.OPENAI:
            api_key = settings.openai_api_key or os.getenv("OPENAI_API_KEY")
            model = settings.openai_default_model or "gpt-4o"
        elif provider == LLMProviderType.ANTHROPIC:
            api_key = settings.anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
            model = settings.anthropic_default_model or "claude-3-5-sonnet-20241022"
        elif provider == LLMProviderType.GOOGLE:
            api_key = settings.google_ai_api_key or os.getenv("GOOGLE_API_KEY")
            model = settings.google_ai_default_model or "gemini-1.5-pro"
        else:
            raise ValueError(f"Unknown provider: {provider}")

        if not api_key:
            raise ValueError(f"API key not configured for provider: {provider}")

        config = LLMConfig(
            provider=provider,
            model=model,
            api_key=api_key,
            temperature=settings.llm_temperature if hasattr(settings, 'llm_temperature') else 0.1,
            max_tokens=settings.llm_max_tokens if hasattr(settings, 'llm_max_tokens') else 4000,
            timeout=settings.llm_request_timeout if hasattr(settings, 'llm_request_timeout') else 60,
            max_retries=settings.llm_max_retries if hasattr(settings, 'llm_max_retries') else 3,
        )

        return cls.create(config)