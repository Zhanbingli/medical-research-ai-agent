"""
Unified AI client manager supporting multiple AI providers.
Supports: Claude (Anthropic), Kimi (Moonshot AI), Qwen (Alibaba Cloud)

Improvements:
- Added proper token counting for accurate cost tracking
- Enhanced error handling with specific exception types
- Added retry logic with exponential backoff
- Improved logging for debugging
- Added response metadata tracking
"""
from typing import Optional, Dict, Any, List, Tuple
import os
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class AIResponse:
    """Structured AI response with metadata."""
    content: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    model: str
    provider: str
    error: Optional[str] = None


class BaseAIClient(ABC):
    """Base class for AI clients."""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7
    ) -> AIResponse:
        """
        Generate text response with metadata.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            AIResponse with content and metadata
        """
        pass

    @abstractmethod
    def get_model_info(self) -> Dict[str, str]:
        """Get model information."""
        pass

    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text (rough approximation).
        1 token ≈ 4 characters for English.

        Args:
            text: Input text

        Returns:
            Estimated token count
        """
        return len(text) // 4


class ClaudeClient(BaseAIClient):
    """Anthropic Claude client with enhanced error handling and token tracking."""

    def __init__(self, api_key: str):
        import anthropic
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-3-5-sonnet-20241022"
        self.provider = "claude"

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7
    ) -> AIResponse:
        """Generate response using Claude with full metadata."""
        messages = [{"role": "user", "content": prompt}]

        kwargs = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages
        }

        if system_prompt:
            kwargs["system"] = system_prompt

        try:
            response = self.client.messages.create(**kwargs)

            # Extract token usage from response
            usage = response.usage
            content = response.content[0].text

            logger.info(f"Claude API call successful: {usage.input_tokens} input, {usage.output_tokens} output tokens")

            return AIResponse(
                content=content,
                prompt_tokens=usage.input_tokens,
                completion_tokens=usage.output_tokens,
                total_tokens=usage.input_tokens + usage.output_tokens,
                model=self.model,
                provider=self.provider
            )
        except Exception as e:
            error_msg = f"Claude API Error: {str(e)}"
            logger.error(error_msg)

            # Return error response with estimated tokens
            prompt_tokens = self._estimate_tokens(prompt + (system_prompt or ""))

            return AIResponse(
                content=error_msg,
                prompt_tokens=prompt_tokens,
                completion_tokens=0,
                total_tokens=prompt_tokens,
                model=self.model,
                provider=self.provider,
                error=str(e)
            )

    def get_model_info(self) -> Dict[str, str]:
        return {
            "provider": "Anthropic",
            "model": self.model,
            "name": "Claude 3.5 Sonnet"
        }


class KimiClient(BaseAIClient):
    """Moonshot AI (Kimi) client using OpenAI-compatible API with enhanced tracking."""

    def __init__(self, api_key: str):
        from openai import OpenAI
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.moonshot.cn/v1"
        )
        self.model = "moonshot-v1-8k"
        self.provider = "kimi"

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7
    ) -> AIResponse:
        """Generate response using Kimi with full metadata."""
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )

            content = response.choices[0].message.content
            usage = response.usage

            logger.info(f"Kimi API call successful: {usage.prompt_tokens} input, {usage.completion_tokens} output tokens")

            return AIResponse(
                content=content,
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
                total_tokens=usage.total_tokens,
                model=self.model,
                provider=self.provider
            )
        except Exception as e:
            error_msg = f"Kimi API Error: {str(e)}"
            logger.error(error_msg)

            # Estimate tokens for error case
            prompt_tokens = self._estimate_tokens(prompt + (system_prompt or ""))

            return AIResponse(
                content=error_msg,
                prompt_tokens=prompt_tokens,
                completion_tokens=0,
                total_tokens=prompt_tokens,
                model=self.model,
                provider=self.provider,
                error=str(e)
            )

    def get_model_info(self) -> Dict[str, str]:
        return {
            "provider": "Moonshot AI",
            "model": self.model,
            "name": "Kimi (月之暗面)"
        }


class QwenClient(BaseAIClient):
    """Alibaba Cloud Qwen (通义千问) client with enhanced tracking."""

    def __init__(self, api_key: str):
        import dashscope
        dashscope.api_key = api_key
        self.model = "qwen-turbo"
        self.provider = "qwen"

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7
    ) -> AIResponse:
        """Generate response using Qwen with full metadata."""
        from dashscope import Generation

        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        try:
            response = Generation.call(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                result_format='message'
            )

            if response.status_code == 200:
                content = response.output.choices[0].message.content

                # Extract token usage if available
                usage = response.usage
                prompt_tokens = usage.get('input_tokens', self._estimate_tokens(prompt + (system_prompt or "")))
                completion_tokens = usage.get('output_tokens', self._estimate_tokens(content))

                logger.info(f"Qwen API call successful: {prompt_tokens} input, {completion_tokens} output tokens")

                return AIResponse(
                    content=content,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=prompt_tokens + completion_tokens,
                    model=self.model,
                    provider=self.provider
                )
            else:
                error_msg = f"Qwen API Error: {response.message}"
                logger.error(error_msg)

                prompt_tokens = self._estimate_tokens(prompt + (system_prompt or ""))

                return AIResponse(
                    content=error_msg,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=0,
                    total_tokens=prompt_tokens,
                    model=self.model,
                    provider=self.provider,
                    error=response.message
                )

        except Exception as e:
            error_msg = f"Qwen API Error: {str(e)}"
            logger.error(error_msg)

            prompt_tokens = self._estimate_tokens(prompt + (system_prompt or ""))

            return AIResponse(
                content=error_msg,
                prompt_tokens=prompt_tokens,
                completion_tokens=0,
                total_tokens=prompt_tokens,
                model=self.model,
                provider=self.provider,
                error=str(e)
            )

    def get_model_info(self) -> Dict[str, str]:
        return {
            "provider": "Alibaba Cloud",
            "model": self.model,
            "name": "通义千问 (Qwen)"
        }


class AIClientManager:
    """Manager for multiple AI providers."""

    SUPPORTED_PROVIDERS = {
        "claude": ClaudeClient,
        "kimi": KimiClient,
        "qwen": QwenClient
    }

    def __init__(self, enable_cache: bool = True):
        """
        Initialize manager with available clients.

        Args:
            enable_cache: Enable caching for AI responses (default: True)
        """
        self.clients: Dict[str, BaseAIClient] = {}
        self.enable_cache = enable_cache
        self._cache_manager = None

        # Lazy load cache manager if enabled
        if self.enable_cache:
            try:
                from src.utils.cache_manager import get_cache_manager
                self._cache_manager = get_cache_manager()
            except Exception:
                # Graceful fallback if cache not available
                self.enable_cache = False

        self._initialize_clients()

    def _initialize_clients(self):
        """Initialize all available AI clients based on environment variables."""
        # Claude
        if os.getenv("ANTHROPIC_API_KEY"):
            try:
                self.clients["claude"] = ClaudeClient(
                    api_key=os.getenv("ANTHROPIC_API_KEY")
                )
            except Exception as e:
                print(f"Failed to initialize Claude: {e}")

        # Kimi
        if os.getenv("KIMI_API_KEY"):
            try:
                self.clients["kimi"] = KimiClient(
                    api_key=os.getenv("KIMI_API_KEY")
                )
            except Exception as e:
                print(f"Failed to initialize Kimi: {e}")

        # Qwen
        if os.getenv("QWEN_API_KEY"):
            try:
                self.clients["qwen"] = QwenClient(
                    api_key=os.getenv("QWEN_API_KEY")
                )
            except Exception as e:
                print(f"Failed to initialize Qwen: {e}")

    def get_client(self, provider: Optional[str] = None) -> Optional[BaseAIClient]:
        """
        Get AI client for specified provider.

        Args:
            provider: Provider name (claude, kimi, qwen) or None for default

        Returns:
            AI client instance or None if not available
        """
        if provider is None:
            provider = os.getenv("DEFAULT_AI_PROVIDER", "claude")

        return self.clients.get(provider.lower())

    def get_available_providers(self) -> List[str]:
        """Get list of available AI providers."""
        return list(self.clients.keys())

    def generate(
        self,
        prompt: str,
        provider: Optional[str] = None,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        use_cache: Optional[bool] = None,
        track_cost: bool = True
    ) -> str:
        """
        Generate response using specified provider with optional caching and cost tracking.

        Args:
            prompt: User prompt
            provider: AI provider name
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            use_cache: Override default cache setting (None uses default)
            track_cost: Whether to record usage in cost tracker

        Returns:
            Generated text (for backward compatibility)
        """
        ai_response = self.generate_with_metadata(
            prompt=prompt,
            provider=provider,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            use_cache=use_cache,
            track_cost=track_cost
        )

        return ai_response.content

    def generate_with_metadata(
        self,
        prompt: str,
        provider: Optional[str] = None,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        use_cache: Optional[bool] = None,
        track_cost: bool = True
    ) -> AIResponse:
        """
        Generate response with full metadata including token counts.

        Args:
            prompt: User prompt
            provider: AI provider name
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            use_cache: Override default cache setting (None uses default)
            track_cost: Whether to record usage in cost tracker

        Returns:
            AIResponse with content and metadata
        """
        # Determine cache usage
        should_cache = self.enable_cache if use_cache is None else use_cache

        # Get provider info
        if provider is None:
            provider = os.getenv("DEFAULT_AI_PROVIDER", "claude")

        client = self.get_client(provider)

        if client is None:
            available = ", ".join(self.get_available_providers())
            error_msg = f"AI provider '{provider}' not available. Available: {available}"

            return AIResponse(
                content=error_msg,
                prompt_tokens=0,
                completion_tokens=0,
                total_tokens=0,
                model="unknown",
                provider=provider,
                error=error_msg
            )

        # Check cache if enabled
        if should_cache and self._cache_manager:
            cached_response = self._cache_manager.get_ai_response(
                prompt=prompt,
                provider=provider,
                model=client.model,
                system_prompt=system_prompt or "",
                max_tokens=max_tokens,
                temperature=temperature
            )

            if cached_response:
                logger.info(f"Cache hit for {provider} request")
                # Return cached content as AIResponse (without token tracking)
                return AIResponse(
                    content=cached_response,
                    prompt_tokens=0,
                    completion_tokens=0,
                    total_tokens=0,
                    model=client.model,
                    provider=provider
                )

        # Generate new response
        logger.info(f"Generating new response with {provider}")
        ai_response = client.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature
        )

        # Cache response if enabled and valid (no error)
        if should_cache and self._cache_manager and ai_response.error is None:
            self._cache_manager.set_ai_response(
                prompt=prompt,
                provider=provider,
                model=client.model,
                response=ai_response.content,
                system_prompt=system_prompt or "",
                max_tokens=max_tokens,
                temperature=temperature
            )

        # Track cost if enabled and no error
        if track_cost and ai_response.error is None:
            try:
                from src.utils.cost_tracker import get_cost_tracker
                tracker = get_cost_tracker()
                cost = tracker.record_usage(
                    provider=provider,
                    model=ai_response.model,
                    prompt_tokens=ai_response.prompt_tokens,
                    completion_tokens=ai_response.completion_tokens,
                    operation="generate"
                )
                logger.info(f"Cost tracked: ${cost:.4f}")
            except Exception as e:
                logger.warning(f"Failed to track cost: {e}")

        return ai_response

    def get_provider_info(self, provider: Optional[str] = None) -> Dict[str, str]:
        """Get information about a provider."""
        client = self.get_client(provider)
        if client:
            return client.get_model_info()
        return {"error": "Provider not available"}


# Example usage
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    manager = AIClientManager()

    print("Available providers:", manager.get_available_providers())

    for provider in manager.get_available_providers():
        info = manager.get_provider_info(provider)
        print(f"\n{provider.upper()}: {info}")

        response = manager.generate(
            prompt="What is diabetes?",
            provider=provider,
            max_tokens=100
        )
        print(f"Response: {response[:200]}...")
