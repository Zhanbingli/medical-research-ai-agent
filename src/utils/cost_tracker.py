"""
Cost tracking and quota management for AI API usage.
Helps monitor spending and prevent overages.
"""
import json
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict
import threading


@dataclass
class UsageRecord:
    """Record of a single API usage."""
    timestamp: str
    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost: float
    operation: str  # summarize, synthesize, qa, etc.


class CostTracker:
    """Track API costs and enforce quotas."""

    # Pricing per 1M tokens (as of 2025)
    PRICING = {
        "claude": {
            "claude-3-5-sonnet-20241022": {
                "input": 3.00,    # $3 per 1M input tokens
                "output": 15.00   # $15 per 1M output tokens
            }
        },
        "kimi": {
            "moonshot-v1-8k": {
                "input": 0.20,    # ¥0.2 per 1K tokens (~$0.20 per 1M)
                "output": 0.20
            }
        },
        "qwen": {
            "qwen-turbo": {
                "input": 0.60,    # ¥0.6 per 1K tokens (~$0.60 per 1M)
                "output": 0.60
            }
        }
    }

    def __init__(self, storage_path: str = "./cache/usage_stats.json"):
        """
        Initialize cost tracker.

        Args:
            storage_path: Path to store usage statistics
        """
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        self.usage_records: List[UsageRecord] = []
        self.lock = threading.Lock()

        self._load_records()

    def _load_records(self):
        """Load usage records from disk."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    self.usage_records = [
                        UsageRecord(**record) for record in data
                    ]
            except Exception as e:
                print(f"Error loading usage records: {e}")

    def _save_records(self):
        """Save usage records to disk."""
        try:
            with open(self.storage_path, 'w') as f:
                data = [asdict(record) for record in self.usage_records]
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving usage records: {e}")

    def estimate_cost(
        self,
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int
    ) -> float:
        """
        Estimate cost for given usage.

        Args:
            provider: AI provider name
            model: Model name
            prompt_tokens: Number of input tokens
            completion_tokens: Number of output tokens

        Returns:
            Estimated cost in USD
        """
        if provider not in self.PRICING:
            return 0.0

        if model not in self.PRICING[provider]:
            # Use first available model pricing as fallback
            model = list(self.PRICING[provider].keys())[0]

        pricing = self.PRICING[provider][model]

        input_cost = (prompt_tokens / 1_000_000) * pricing["input"]
        output_cost = (completion_tokens / 1_000_000) * pricing["output"]

        return input_cost + output_cost

    def record_usage(
        self,
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        operation: str = "unknown"
    ) -> float:
        """
        Record API usage and return estimated cost.

        Args:
            provider: AI provider name
            model: Model name
            prompt_tokens: Number of input tokens
            completion_tokens: Number of output tokens
            operation: Type of operation performed

        Returns:
            Estimated cost in USD
        """
        cost = self.estimate_cost(
            provider, model, prompt_tokens, completion_tokens
        )

        record = UsageRecord(
            timestamp=datetime.now().isoformat(),
            provider=provider,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            estimated_cost=cost,
            operation=operation
        )

        with self.lock:
            self.usage_records.append(record)
            self._save_records()

        return cost

    def get_total_cost(
        self,
        provider: Optional[str] = None,
        since: Optional[datetime] = None
    ) -> float:
        """
        Get total cost for given filters.

        Args:
            provider: Filter by provider (None for all)
            since: Only include records since this datetime

        Returns:
            Total cost in USD
        """
        total = 0.0

        for record in self.usage_records:
            # Filter by provider
            if provider and record.provider != provider:
                continue

            # Filter by date
            if since:
                record_time = datetime.fromisoformat(record.timestamp)
                if record_time < since:
                    continue

            total += record.estimated_cost

        return total

    def get_usage_stats(
        self,
        since: Optional[datetime] = None
    ) -> Dict:
        """
        Get comprehensive usage statistics.

        Args:
            since: Only include records since this datetime

        Returns:
            Dictionary with usage statistics
        """
        stats = {
            "total_cost": 0.0,
            "total_tokens": 0,
            "total_requests": 0,
            "by_provider": {},
            "by_operation": {}
        }

        for record in self.usage_records:
            # Filter by date
            if since:
                record_time = datetime.fromisoformat(record.timestamp)
                if record_time < since:
                    continue

            # Update totals
            stats["total_cost"] += record.estimated_cost
            stats["total_tokens"] += record.total_tokens
            stats["total_requests"] += 1

            # By provider
            if record.provider not in stats["by_provider"]:
                stats["by_provider"][record.provider] = {
                    "cost": 0.0,
                    "tokens": 0,
                    "requests": 0
                }

            stats["by_provider"][record.provider]["cost"] += record.estimated_cost
            stats["by_provider"][record.provider]["tokens"] += record.total_tokens
            stats["by_provider"][record.provider]["requests"] += 1

            # By operation
            if record.operation not in stats["by_operation"]:
                stats["by_operation"][record.operation] = {
                    "cost": 0.0,
                    "tokens": 0,
                    "requests": 0
                }

            stats["by_operation"][record.operation]["cost"] += record.estimated_cost
            stats["by_operation"][record.operation]["tokens"] += record.total_tokens
            stats["by_operation"][record.operation]["requests"] += 1

        return stats

    def check_quota(
        self,
        daily_limit: float,
        monthly_limit: float
    ) -> Dict[str, bool]:
        """
        Check if usage is within quota limits.

        Args:
            daily_limit: Daily spending limit in USD
            monthly_limit: Monthly spending limit in USD

        Returns:
            Dictionary with quota status
        """
        now = datetime.now()

        daily_cost = self.get_total_cost(
            since=now - timedelta(days=1)
        )

        monthly_cost = self.get_total_cost(
            since=now - timedelta(days=30)
        )

        return {
            "daily_within_limit": daily_cost < daily_limit,
            "monthly_within_limit": monthly_cost < monthly_limit,
            "daily_used": daily_cost,
            "daily_limit": daily_limit,
            "daily_remaining": max(0, daily_limit - daily_cost),
            "monthly_used": monthly_cost,
            "monthly_limit": monthly_limit,
            "monthly_remaining": max(0, monthly_limit - monthly_cost)
        }

    def clear_old_records(self, days: int = 90):
        """
        Remove records older than specified days.

        Args:
            days: Keep records from last N days
        """
        cutoff = datetime.now() - timedelta(days=days)

        with self.lock:
            self.usage_records = [
                record for record in self.usage_records
                if datetime.fromisoformat(record.timestamp) >= cutoff
            ]
            self._save_records()


# Global cost tracker instance
_cost_tracker = None


def get_cost_tracker() -> CostTracker:
    """Get or create global cost tracker instance."""
    global _cost_tracker

    if _cost_tracker is None:
        _cost_tracker = CostTracker()

    return _cost_tracker


# Example usage
if __name__ == "__main__":
    tracker = CostTracker()

    # Record some usage
    cost1 = tracker.record_usage(
        provider="claude",
        model="claude-3-5-sonnet-20241022",
        prompt_tokens=1000,
        completion_tokens=500,
        operation="summarize"
    )
    print(f"Cost 1: ${cost1:.4f}")

    cost2 = tracker.record_usage(
        provider="kimi",
        model="moonshot-v1-8k",
        prompt_tokens=2000,
        completion_tokens=1000,
        operation="synthesize"
    )
    print(f"Cost 2: ${cost2:.4f}")

    # Get statistics
    stats = tracker.get_usage_stats()
    print(f"\nTotal cost: ${stats['total_cost']:.4f}")
    print(f"Total tokens: {stats['total_tokens']:,}")
    print(f"Total requests: {stats['total_requests']}")

    print("\nBy provider:")
    for provider, data in stats['by_provider'].items():
        print(f"  {provider}: ${data['cost']:.4f} ({data['requests']} requests)")

    # Check quota
    quota = tracker.check_quota(daily_limit=10.0, monthly_limit=100.0)
    print(f"\nQuota status:")
    print(f"  Daily: ${quota['daily_used']:.2f} / ${quota['daily_limit']:.2f}")
    print(f"  Monthly: ${quota['monthly_used']:.2f} / ${quota['monthly_limit']:.2f}")
