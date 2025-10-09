"""
Retry handler with exponential backoff and fallback strategies.
Improves reliability of AI Agent operations.
"""
import time
import functools
from typing import Callable, Optional, List, Any, Type
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RetryHandler:
    """Handles retries with exponential backoff and provider fallback."""

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0
    ):
        """
        Initialize retry handler.

        Args:
            max_retries: Maximum number of retry attempts
            base_delay: Initial delay in seconds
            max_delay: Maximum delay between retries
            exponential_base: Base for exponential backoff
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt using exponential backoff."""
        delay = self.base_delay * (self.exponential_base ** attempt)
        return min(delay, self.max_delay)

    def retry_with_backoff(
        self,
        func: Callable,
        *args,
        retry_exceptions: tuple = (Exception,),
        **kwargs
    ) -> Any:
        """
        Execute function with exponential backoff retry.

        Args:
            func: Function to execute
            *args: Function arguments
            retry_exceptions: Tuple of exceptions to retry on
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            Last exception if all retries fail
        """
        last_exception = None

        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)

            except retry_exceptions as e:
                last_exception = e

                if attempt < self.max_retries - 1:
                    delay = self._calculate_delay(attempt)
                    logger.warning(
                        f"Attempt {attempt + 1}/{self.max_retries} failed: {str(e)}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    time.sleep(delay)
                else:
                    logger.error(
                        f"All {self.max_retries} attempts failed. Last error: {str(e)}"
                    )

        raise last_exception


def retry_with_fallback(
    providers: List[str],
    max_retries_per_provider: int = 2
):
    """
    Decorator for retrying with provider fallback.

    Args:
        providers: List of provider names to try in order
        max_retries_per_provider: Retries per provider

    Example:
        @retry_with_fallback(["claude", "kimi", "qwen"])
        def analyze_with_ai(text, provider):
            # Your AI call here
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            handler = RetryHandler(max_retries=max_retries_per_provider)
            last_error = None

            # Try each provider in order
            for provider in providers:
                try:
                    # Update provider in kwargs
                    kwargs_with_provider = kwargs.copy()
                    kwargs_with_provider['provider'] = provider

                    logger.info(f"Attempting with provider: {provider}")

                    result = handler.retry_with_backoff(
                        func,
                        *args,
                        **kwargs_with_provider
                    )

                    logger.info(f"Success with provider: {provider}")
                    return result

                except Exception as e:
                    last_error = e
                    logger.warning(
                        f"Provider {provider} failed after retries: {str(e)}"
                    )
                    continue

            # All providers failed
            error_msg = f"All providers failed. Last error: {str(last_error)}"
            logger.error(error_msg)
            raise Exception(error_msg)

        return wrapper
    return decorator


def with_timeout(timeout_seconds: float):
    """
    Decorator to add timeout to function.

    Args:
        timeout_seconds: Maximum execution time

    Example:
        @with_timeout(30.0)
        def slow_operation():
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import signal

            def timeout_handler(signum, frame):
                raise TimeoutError(
                    f"Function {func.__name__} exceeded timeout of {timeout_seconds}s"
                )

            # Set timeout alarm (Unix only)
            try:
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(int(timeout_seconds))

                result = func(*args, **kwargs)

                signal.alarm(0)  # Cancel alarm
                return result

            except AttributeError:
                # Windows doesn't support SIGALRM, just run without timeout
                logger.warning("Timeout not supported on this platform")
                return func(*args, **kwargs)

        return wrapper
    return decorator


class CircuitBreaker:
    """
    Circuit breaker pattern to prevent cascading failures.

    States:
    - CLOSED: Normal operation
    - OPEN: Service is failing, reject requests
    - HALF_OPEN: Testing if service recovered
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: Type[Exception] = Exception
    ):
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery
            expected_exception: Exception type to track
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function through circuit breaker.

        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            Exception if circuit is open or function fails
        """
        if self.state == "OPEN":
            # Check if recovery timeout has passed
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                self.state = "HALF_OPEN"
                logger.info("Circuit breaker entering HALF_OPEN state")
            else:
                raise Exception(
                    f"Circuit breaker is OPEN. Service unavailable. "
                    f"Retry after {self.recovery_timeout}s"
                )

        try:
            result = func(*args, **kwargs)

            # Success - reset failure count
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                logger.info("Circuit breaker recovered to CLOSED state")

            self.failure_count = 0
            return result

        except self.expected_exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()

            logger.warning(
                f"Circuit breaker failure {self.failure_count}/{self.failure_threshold}"
            )

            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
                logger.error("Circuit breaker opened due to repeated failures")

            raise e


# Global circuit breakers for each provider
_circuit_breakers = {}


def get_circuit_breaker(provider: str) -> CircuitBreaker:
    """Get or create circuit breaker for provider."""
    if provider not in _circuit_breakers:
        _circuit_breakers[provider] = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60.0
        )

    return _circuit_breakers[provider]


# Example usage
if __name__ == "__main__":
    # Test retry handler
    handler = RetryHandler(max_retries=3)

    attempt_count = 0

    def flaky_function():
        nonlocal attempt_count
        attempt_count += 1

        if attempt_count < 3:
            raise Exception("Temporary failure")

        return "Success!"

    result = handler.retry_with_backoff(flaky_function)
    print(f"Result: {result}, Attempts: {attempt_count}")

    # Test fallback decorator
    @retry_with_fallback(["claude", "kimi", "qwen"], max_retries_per_provider=2)
    def analyze_text(text, provider=None):
        if provider == "claude":
            raise Exception("Claude unavailable")
        return f"Analysis by {provider}"

    try:
        result = analyze_text("Sample text")
        print(f"Fallback result: {result}")
    except Exception as e:
        print(f"All providers failed: {e}")
