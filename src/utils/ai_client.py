"""
Unified AI client manager supporting multiple AI providers.
Supports: Claude (Anthropic), Kimi (Moonshot AI), Qwen (Alibaba Cloud)
"""
from typing import Optional, Dict, Any, List
import os
from abc import ABC, abstractmethod


class BaseAIClient(ABC):
    """Base class for AI clients."""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7
    ) -> str:
        """Generate text response."""
        pass

    @abstractmethod
    def get_model_info(self) -> Dict[str, str]:
        """Get model information."""
        pass


class ClaudeClient(BaseAIClient):
    """Anthropic Claude client."""

    def __init__(self, api_key: str):
        import anthropic
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-3-5-sonnet-20241022"

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7
    ) -> str:
        """Generate response using Claude."""
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
            return response.content[0].text
        except Exception as e:
            return f"Claude API Error: {str(e)}"

    def get_model_info(self) -> Dict[str, str]:
        return {
            "provider": "Anthropic",
            "model": self.model,
            "name": "Claude 3.5 Sonnet"
        }


class KimiClient(BaseAIClient):
    """Moonshot AI (Kimi) client using OpenAI-compatible API."""

    def __init__(self, api_key: str):
        from openai import OpenAI
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.moonshot.cn/v1"
        )
        self.model = "moonshot-v1-8k"

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7
    ) -> str:
        """Generate response using Kimi."""
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
            return response.choices[0].message.content
        except Exception as e:
            return f"Kimi API Error: {str(e)}"

    def get_model_info(self) -> Dict[str, str]:
        return {
            "provider": "Moonshot AI",
            "model": self.model,
            "name": "Kimi (月之暗面)"
        }


class QwenClient(BaseAIClient):
    """Alibaba Cloud Qwen (通义千问) client."""

    def __init__(self, api_key: str):
        import dashscope
        dashscope.api_key = api_key
        self.model = "qwen-turbo"

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7
    ) -> str:
        """Generate response using Qwen."""
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
                return response.output.choices[0].message.content
            else:
                return f"Qwen API Error: {response.message}"

        except Exception as e:
            return f"Qwen API Error: {str(e)}"

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

    def __init__(self):
        """Initialize manager with available clients."""
        self.clients: Dict[str, BaseAIClient] = {}
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
        temperature: float = 0.7
    ) -> str:
        """
        Generate response using specified provider.

        Args:
            prompt: User prompt
            provider: AI provider name
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            Generated text
        """
        client = self.get_client(provider)

        if client is None:
            available = ", ".join(self.get_available_providers())
            return f"AI provider '{provider}' not available. Available: {available}"

        return client.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature
        )

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
