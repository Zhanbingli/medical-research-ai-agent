"""Minimal AI client manager for Claude, Kimi, and Qwen."""
from typing import Optional, Dict, List
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
        """Generate text from the provider."""
        raise NotImplementedError

    @abstractmethod
    def get_model_info(self) -> Dict[str, str]:
        """Get model information."""
        raise NotImplementedError


class ClaudeClient(BaseAIClient):
    """Anthropic Claude client."""

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
    ) -> str:
        messages = [{"role": "user", "content": prompt}]

        kwargs = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages
        }

        if system_prompt:
            kwargs["system"] = system_prompt

        response = self.client.messages.create(**kwargs)
        return response.content[0].text

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
        self.provider = "kimi"

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7
    ) -> str:
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )

        return response.choices[0].message.content

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
        self.provider = "qwen"

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7
    ) -> str:
        from dashscope import Generation

        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        response = Generation.call(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            result_format="message"
        )

        if response.status_code != 200:
            raise RuntimeError(f"Qwen API Error: {response.message}")

        return response.output.choices[0].message.content

    def get_model_info(self) -> Dict[str, str]:
        return {
            "provider": "Alibaba Cloud",
            "model": self.model,
            "name": "通义千问 (Qwen)"
        }


class AIClientManager:
    """Manager for multiple AI providers with a minimal surface area."""

    SUPPORTED_PROVIDERS = {
        "claude": ClaudeClient,
        "kimi": KimiClient,
        "qwen": QwenClient
    }

    def __init__(self):
        self.clients: Dict[str, BaseAIClient] = {}
        self._initialize_clients()

    def _initialize_clients(self) -> None:
        """Initialize available AI clients based on environment variables."""
        if os.getenv("ANTHROPIC_API_KEY"):
            try:
                self.clients["claude"] = ClaudeClient(
                    api_key=os.getenv("ANTHROPIC_API_KEY")
                )
            except Exception as exc:  # pragma: no cover - initialization failures are surfaced to users
                print(f"Failed to initialize Claude: {exc}")

        if os.getenv("KIMI_API_KEY"):
            try:
                self.clients["kimi"] = KimiClient(
                    api_key=os.getenv("KIMI_API_KEY")
                )
            except Exception as exc:  # pragma: no cover
                print(f"Failed to initialize Kimi: {exc}")

        if os.getenv("QWEN_API_KEY"):
            try:
                self.clients["qwen"] = QwenClient(
                    api_key=os.getenv("QWEN_API_KEY")
                )
            except Exception as exc:  # pragma: no cover
                print(f"Failed to initialize Qwen: {exc}")

    def get_client(self, provider: Optional[str] = None) -> Optional[BaseAIClient]:
        """Get AI client for specified provider."""
        provider = provider or os.getenv("DEFAULT_AI_PROVIDER", "claude")
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
        """Generate a response with the given provider."""
        client = self.get_client(provider)

        if client is None:
            available = ", ".join(self.get_available_providers()) or "none"
            raise ValueError(f"AI provider '{provider}' not available. Available: {available}")

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


if __name__ == "__main__":  # pragma: no cover - manual quick check
    from dotenv import load_dotenv

    load_dotenv()
    manager = AIClientManager()
    print("Available providers:", manager.get_available_providers())
    for provider in manager.get_available_providers():
        print(provider, manager.get_provider_info(provider))
