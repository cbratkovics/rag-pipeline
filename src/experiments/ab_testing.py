"""A/B testing framework for experiment management."""

import hashlib
import random
from datetime import datetime, timedelta

import numpy as np
from scipy import stats

from src.core.config import get_settings
from src.core.models import ExperimentResult, ExperimentVariant, QueryResult
from src.infrastructure.cache import cache_manager
from src.infrastructure.logging import LoggerMixin


class ABTestManager(LoggerMixin):
    """Manages A/B testing experiments."""

    def __init__(self):
        """Initialize A/B test manager."""
        self.settings = get_settings()
        self.active_experiments: dict[str, ExperimentConfig] = {}

    async def initialize(self) -> None:
        """Initialize A/B test manager."""
        # Load active experiments from cache or database
        cached_experiments = await cache_manager.get_pattern("experiments:*")
        for key, config in cached_experiments.items():
            exp_id = key.split(":")[-1]
            self.active_experiments[exp_id] = ExperimentConfig(**config)

        self.logger.info(
            "A/B test manager initialized",
            active_experiments=len(self.active_experiments),
        )

    def assign_variant(
        self,
        user_id: str | None = None,
        session_id: str | None = None,
        experiment_id: str = "default",
    ) -> ExperimentVariant:
        """Assign user to experiment variant using hash-based assignment."""
        if not self.settings.ab_test_enabled:
            return ExperimentVariant.BASELINE

        # Get or create experiment config
        if experiment_id not in self.active_experiments:
            self.active_experiments[experiment_id] = ExperimentConfig(
                experiment_id=experiment_id,
                variants=self.settings.ab_test_variants,
                traffic_split=self.settings.ab_test_traffic_split,
            )

        config = self.active_experiments[experiment_id]

        # Use user_id or session_id for consistent assignment
        identifier = user_id or session_id or str(random.random())

        # Hash-based assignment for consistency
        hash_value = int(hashlib.md5(f"{experiment_id}:{identifier}".encode()).hexdigest(), 16)
        assignment_value = (hash_value % 100) / 100.0

        # Determine variant based on traffic split
        cumulative_split = 0.0
        for variant_name, split in zip(config.variants, config.traffic_split, strict=False):
            cumulative_split += split
            if assignment_value < cumulative_split:
                variant = ExperimentVariant(variant_name)
                self.logger.debug(
                    "Variant assigned",
                    experiment_id=experiment_id,
                    user_id=user_id,
                    variant=variant.value,
                )
                return variant

        # Fallback to baseline
        return ExperimentVariant.BASELINE

    async def record_result(
        self,
        experiment_id: str,
        variant: ExperimentVariant,
        result: QueryResult,
        metrics: dict[str, float] | None = None,
    ) -> None:
        """Record experiment result."""
        # Create result key
        result_key = cache_manager.make_key(
            "experiment_results",
            experiment_id,
            variant.value,
            str(result.id),
        )

        # Prepare result data
        result_data = {
            "variant": variant.value,
            "success": result.status.value == "completed",
            "latency_ms": result.processing_time_ms,
            "cost_usd": result.cost_usd,
            "confidence_score": result.confidence_score,
            "timestamp": datetime.utcnow().isoformat(),
        }

        if metrics:
            result_data["ragas_score"] = metrics.get("overall_score", 0.0)

        # Store result
        await cache_manager.set(result_key, result_data, ttl=86400 * 7)  # Keep for 7 days

        self.logger.debug(
            "Experiment result recorded",
            experiment_id=experiment_id,
            variant=variant.value,
            result_id=str(result.id),
        )

    async def calculate_statistics(
        self,
        experiment_id: str,
        min_samples: int | None = None,
    ) -> list[ExperimentResult]:
        """Calculate experiment statistics."""
        min_samples = min_samples or self.settings.ab_test_min_samples

        # Get all results for experiment
        pattern = cache_manager.make_key("experiment_results", experiment_id, "*")
        all_results = await cache_manager.get_pattern(pattern)

        # Group by variant
        variant_data: dict[str, list[dict]] = {}
        for _key, data in all_results.items():
            variant = data["variant"]
            if variant not in variant_data:
                variant_data[variant] = []
            variant_data[variant].append(data)

        # Calculate statistics for each variant
        experiment_results = []
        for variant_name, results in variant_data.items():
            if len(results) < min_samples:
                self.logger.warning(
                    "Insufficient samples for variant",
                    experiment_id=experiment_id,
                    variant=variant_name,
                    samples=len(results),
                    min_samples=min_samples,
                )
                continue

            # Calculate metrics
            success_count = sum(1 for r in results if r["success"])
            success_rate = success_count / len(results)
            avg_latency = np.mean([r["latency_ms"] for r in results])
            avg_cost = np.mean([r["cost_usd"] for r in results])
            ragas_scores = [r.get("ragas_score", 0.0) for r in results if "ragas_score" in r]
            avg_ragas = np.mean(ragas_scores) if ragas_scores else 0.0

            # Calculate confidence interval for success rate
            ci_lower, ci_upper = self._calculate_confidence_interval(
                success_count,
                len(results),
                self.settings.ab_test_confidence_level,
            )

            experiment_results.append(
                ExperimentResult(
                    experiment_id=experiment_id,
                    variant=ExperimentVariant(variant_name),
                    sample_size=len(results),
                    success_count=success_count,
                    success_rate=success_rate,
                    avg_latency_ms=avg_latency,
                    avg_cost_usd=avg_cost,
                    avg_ragas_score=avg_ragas,
                    confidence_interval_lower=ci_lower,
                    confidence_interval_upper=ci_upper,
                    is_significant=False,  # Will be calculated
                    p_value=1.0,  # Will be calculated
                )
            )

        # Perform statistical significance testing
        if len(experiment_results) >= 2:
            self._perform_significance_testing(experiment_results)

        return experiment_results

    def _calculate_confidence_interval(
        self,
        successes: int,
        trials: int,
        confidence_level: float,
    ) -> tuple[float, float]:
        """Calculate Wilson score confidence interval."""
        if trials == 0:
            return 0.0, 0.0

        p_hat = successes / trials
        z = stats.norm.ppf((1 + confidence_level) / 2)

        denominator = 1 + z**2 / trials
        center = (p_hat + z**2 / (2 * trials)) / denominator
        margin = z * np.sqrt((p_hat * (1 - p_hat) + z**2 / (4 * trials)) / trials) / denominator

        return max(0.0, center - margin), min(1.0, center + margin)

    def _perform_significance_testing(
        self,
        results: list[ExperimentResult],
    ) -> None:
        """Perform statistical significance testing between variants."""
        # Find baseline
        baseline = next((r for r in results if r.variant == ExperimentVariant.BASELINE), None)
        if not baseline:
            return

        for result in results:
            if result.variant == baseline.variant:
                continue

            # Perform chi-square test
            observed = [
                [result.success_count, result.sample_size - result.success_count],
                [baseline.success_count, baseline.sample_size - baseline.success_count],
            ]

            try:
                chi2, p_value, _, _ = stats.chi2_contingency(observed)
                result.p_value = p_value
                result.is_significant = p_value < (1 - self.settings.ab_test_confidence_level)
            except Exception as e:
                self.logger.warning(
                    "Significance testing failed",
                    error=str(e),
                    variant=result.variant.value,
                )

    async def get_winning_variant(
        self,
        experiment_id: str,
    ) -> ExperimentVariant | None:
        """Determine winning variant based on success rate."""
        results = await self.calculate_statistics(experiment_id)
        if not results:
            return None

        # Find variant with highest success rate that is statistically significant
        best_result = None
        for result in results:
            if result.is_significant and (
                best_result is None or result.success_rate > best_result.success_rate
            ):
                best_result = result

        if best_result:
            return best_result.variant

        # If no significant winner, return variant with highest success rate
        best_result = max(results, key=lambda r: r.success_rate)
        return best_result.variant


class MultiArmedBandit(LoggerMixin):
    """Multi-armed bandit for dynamic traffic allocation."""

    def __init__(
        self,
        variants: list[str],
        exploration_rate: float = 0.1,
    ):
        """Initialize multi-armed bandit."""
        self.settings = get_settings()
        self.variants = variants
        self.exploration_rate = exploration_rate
        self.arm_counts = dict.fromkeys(variants, 0)
        self.arm_rewards = dict.fromkeys(variants, 0.0)

    def select_arm(self) -> str:
        """Select variant using epsilon-greedy strategy."""
        if random.random() < self.exploration_rate:
            # Exploration: random selection
            return random.choice(self.variants)
        else:
            # Exploitation: select best performing
            avg_rewards = {
                v: self.arm_rewards[v] / max(self.arm_counts[v], 1) for v in self.variants
            }
            return max(avg_rewards, key=lambda k: avg_rewards[k])

    def update_arm(self, variant: str, reward: float) -> None:
        """Update arm statistics."""
        if variant in self.variants:
            self.arm_counts[variant] += 1
            self.arm_rewards[variant] += reward

    async def adapt_traffic_split(
        self,
        experiment_id: str,
        manager: ABTestManager,
    ) -> list[float]:
        """Adapt traffic split based on performance."""
        results = await manager.calculate_statistics(experiment_id)
        if not results:
            return self.settings.ab_test_traffic_split

        # Calculate rewards (success rate * (1 - cost))
        rewards = {}
        for result in results:
            reward = result.success_rate * (1 - min(result.avg_cost_usd, 1.0))
            rewards[result.variant.value] = reward
            self.update_arm(result.variant.value, reward)

        # Calculate new traffic split based on performance
        total_reward = sum(rewards.values())
        if total_reward > 0:
            new_split = [rewards.get(v, 0.0) / total_reward for v in self.variants]
        else:
            new_split = [1.0 / len(self.variants)] * len(self.variants)

        # Apply smoothing to prevent drastic changes
        current_split = manager.active_experiments[experiment_id].traffic_split
        smoothing_factor = 0.7
        smoothed_split = [
            smoothing_factor * current + (1 - smoothing_factor) * new
            for current, new in zip(current_split, new_split, strict=False)
        ]

        # Normalize
        total = sum(smoothed_split)
        normalized_split = [s / total for s in smoothed_split]

        return normalized_split


class ExperimentConfig:
    """Configuration for an A/B test experiment."""

    def __init__(
        self,
        experiment_id: str,
        variants: list[str],
        traffic_split: list[float],
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ):
        """Initialize experiment configuration."""
        self.experiment_id = experiment_id
        self.variants = variants
        self.traffic_split = traffic_split
        self.start_date = start_date or datetime.utcnow()
        self.end_date = end_date or (datetime.utcnow() + timedelta(days=30))

    def is_active(self) -> bool:
        """Check if experiment is active."""
        now = datetime.utcnow()
        return self.start_date <= now <= self.end_date


# Global A/B test manager instance
ab_test_manager = ABTestManager()
