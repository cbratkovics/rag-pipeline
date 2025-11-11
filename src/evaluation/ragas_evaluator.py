"""RAGAS evaluation framework for RAG pipeline assessment."""

import time

import numpy as np
from langchain_openai import ChatOpenAI

from src.core.config import get_settings
from src.core.models import EvaluationMetrics, QueryResult
from src.infrastructure.logging import LoggerMixin


class RAGASEvaluator(LoggerMixin):
    """RAGAS evaluation metrics calculator."""

    def __init__(self):
        """Initialize RAGAS evaluator."""
        self.settings = get_settings()
        self.llm = self._initialize_llm()

    def _initialize_llm(self):
        """Initialize OpenAI for evaluation."""
        llm_config = self.settings.get_llm_config()

        return ChatOpenAI(
            model=llm_config["model"],
            temperature=0.0,  # Deterministic for evaluation
            api_key=llm_config["api_key"],
        )

    async def evaluate(
        self,
        result: QueryResult,
        ground_truth: str | None = None,
    ) -> EvaluationMetrics:
        """Evaluate a query result using RAGAS metrics."""
        start_time = time.time()

        # Calculate individual metrics
        context_relevancy = await self._calculate_context_relevancy(
            query=result.query_text,
            contexts=[doc.document.content for doc in result.sources],
        )

        answer_faithfulness = await self._calculate_answer_faithfulness(
            answer=result.answer,
            contexts=[doc.document.content for doc in result.sources],
        )

        answer_relevancy = await self._calculate_answer_relevancy(
            query=result.query_text,
            answer=result.answer,
        )

        context_recall = await self._calculate_context_recall(
            query=result.query_text,
            contexts=[doc.document.content for doc in result.sources],
            ground_truth=ground_truth,
        )

        # Create evaluation metrics
        metrics = EvaluationMetrics(
            result_id=result.id,
            context_relevancy=context_relevancy,
            answer_faithfulness=answer_faithfulness,
            answer_relevancy=answer_relevancy,
            context_recall=context_recall,
            overall_score=0.0,  # Will be calculated
            evaluation_time_ms=(time.time() - start_time) * 1000,
        )

        # Calculate overall score
        metrics.overall_score = metrics.calculate_overall_score()

        self.logger.info(
            "RAGAS evaluation completed",
            result_id=str(result.id),
            overall_score=metrics.overall_score,
            evaluation_time_ms=metrics.evaluation_time_ms,
        )

        return metrics

    async def _calculate_context_relevancy(
        self,
        query: str,
        contexts: list[str],
    ) -> float:
        """Calculate context relevancy score."""
        if not contexts:
            return 0.0

        try:
            prompt = f"""Given the question and retrieved contexts, evaluate how relevant each context is to answering the question.
Rate each context as relevant (1) or not relevant (0).

Question: {query}

Contexts:
"""
            for i, context in enumerate(contexts, 1):
                prompt += f"\n{i}. {context[:500]}..."  # Truncate long contexts

            prompt += "\n\nProvide relevancy scores as a comma-separated list (e.g., 1,0,1,1,0):"

            response = await self.llm.ainvoke(prompt)
            scores_text = response.content.strip()

            # Parse scores
            scores = []
            for score in scores_text.split(","):
                try:
                    scores.append(float(score.strip()))
                except ValueError:
                    scores.append(0.5)  # Default to neutral if parsing fails

            # Calculate average relevancy
            relevancy = sum(scores) / len(scores) if scores else 0.5

            return min(max(relevancy, 0.0), 1.0)

        except Exception as e:
            self.logger.warning("Context relevancy calculation failed", error=str(e))
            return 0.5

    async def _calculate_answer_faithfulness(
        self,
        answer: str,
        contexts: list[str],
    ) -> float:
        """Calculate answer faithfulness score."""
        if not contexts or not answer:
            return 0.0

        try:
            combined_context = "\n".join(contexts[:3])  # Use top 3 contexts

            prompt = f"""Given the contexts and the answer, evaluate how faithful the answer is to the provided contexts.
An answer is faithful if all information in the answer can be traced back to the contexts.

Contexts:
{combined_context[:1500]}

Answer:
{answer}

Rate the faithfulness from 0 to 1 where:
- 1.0 = All information in the answer is directly supported by the contexts
- 0.5 = Some information is supported, some is not
- 0.0 = The answer contains information not found in the contexts

Faithfulness score (0-1):"""

            response = await self.llm.ainvoke(prompt)
            score_text = response.content.strip()

            try:
                score = float(score_text.split()[0])
            except (ValueError, IndexError):
                score = 0.5

            return min(max(score, 0.0), 1.0)

        except Exception as e:
            self.logger.warning("Answer faithfulness calculation failed", error=str(e))
            return 0.5

    async def _calculate_answer_relevancy(
        self,
        query: str,
        answer: str,
    ) -> float:
        """Calculate answer relevancy score."""
        if not answer:
            return 0.0

        try:
            prompt = f"""Given the question and answer, evaluate how relevant and complete the answer is.

Question: {query}

Answer: {answer}

Rate the relevancy from 0 to 1 where:
- 1.0 = The answer directly and completely addresses the question
- 0.5 = The answer partially addresses the question
- 0.0 = The answer is irrelevant to the question

Relevancy score (0-1):"""

            response = await self.llm.ainvoke(prompt)
            score_text = response.content.strip()

            try:
                score = float(score_text.split()[0])
            except (ValueError, IndexError):
                score = 0.5

            return min(max(score, 0.0), 1.0)

        except Exception as e:
            self.logger.warning("Answer relevancy calculation failed", error=str(e))
            return 0.5

    async def _calculate_context_recall(
        self,
        query: str,
        contexts: list[str],
        ground_truth: str | None = None,
    ) -> float:
        """Calculate context recall score."""
        if not contexts:
            return 0.0

        # If no ground truth provided, use a heuristic based on context coverage
        if not ground_truth:
            # Check if contexts cover different aspects of the query
            query_terms = set(query.lower().split())
            covered_terms = set()

            for context in contexts:
                context_terms = set(context.lower().split())
                covered_terms.update(query_terms.intersection(context_terms))

            recall = len(covered_terms) / len(query_terms) if query_terms else 0.5

            return min(max(recall, 0.0), 1.0)

        try:
            combined_context = "\n".join(contexts)

            prompt = f"""Given the ground truth answer and retrieved contexts, evaluate what percentage of information needed for the ground truth is present in the contexts.

Ground Truth: {ground_truth}

Contexts:
{combined_context[:1500]}

Rate the recall from 0 to 1 where:
- 1.0 = All information needed for the ground truth is in the contexts
- 0.5 = Some important information is present
- 0.0 = Critical information is missing from the contexts

Recall score (0-1):"""

            response = await self.llm.ainvoke(prompt)
            score_text = response.content.strip()

            try:
                score = float(score_text.split()[0])
            except (ValueError, IndexError):
                score = 0.5

            return min(max(score, 0.0), 1.0)

        except Exception as e:
            self.logger.warning("Context recall calculation failed", error=str(e))
            return 0.5

    async def batch_evaluate(
        self,
        results: list[QueryResult],
        ground_truths: list[str] | None = None,
    ) -> list[EvaluationMetrics]:
        """Evaluate multiple query results."""
        evaluations = []
        if ground_truths is None:
            ground_truths = [None] * len(results)  # type: ignore[list-item]

        for result, ground_truth in zip(results, ground_truths, strict=False):
            evaluation = await self.evaluate(result, ground_truth)
            evaluations.append(evaluation)

        return evaluations

    def check_thresholds(self, metrics: EvaluationMetrics) -> dict[str, bool]:
        """Check if metrics meet configured thresholds."""
        return {
            "context_relevancy": metrics.context_relevancy
            >= self.settings.ragas_threshold_context_relevancy,
            "answer_faithfulness": metrics.answer_faithfulness
            >= self.settings.ragas_threshold_answer_faithfulness,
            "answer_relevancy": metrics.answer_relevancy
            >= self.settings.ragas_threshold_answer_relevancy,
            "context_recall": metrics.context_recall
            >= self.settings.ragas_threshold_context_recall,
        }

    def aggregate_metrics(self, evaluations: list[EvaluationMetrics]) -> dict[str, float]:
        """Aggregate multiple evaluation metrics."""
        if not evaluations:
            return {}

        return {
            "mean_context_relevancy": float(np.mean([e.context_relevancy for e in evaluations])),
            "mean_answer_faithfulness": float(
                np.mean([e.answer_faithfulness for e in evaluations])
            ),
            "mean_answer_relevancy": float(np.mean([e.answer_relevancy for e in evaluations])),
            "mean_context_recall": float(np.mean([e.context_recall for e in evaluations])),
            "mean_overall_score": float(np.mean([e.overall_score for e in evaluations])),
            "std_overall_score": float(np.std([e.overall_score for e in evaluations])),
            "min_overall_score": min(e.overall_score for e in evaluations),
            "max_overall_score": max(e.overall_score for e in evaluations),
        }


# Global RAGAS evaluator instance
ragas_evaluator = RAGASEvaluator()
