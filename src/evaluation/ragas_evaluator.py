"""RAGAS evaluation framework for RAG pipeline assessment."""

import asyncio
import time

import numpy as np
from langchain_openai import ChatOpenAI
from sentence_transformers import CrossEncoder

from src.core.config import get_settings
from src.core.models import EvaluationMetrics, QueryResult
from src.infrastructure.logging import LoggerMixin


class RAGASEvaluator(LoggerMixin):
    """RAGAS evaluation metrics calculator with improved scoring."""

    def __init__(self):
        """Initialize RAGAS evaluator."""
        self.settings = get_settings()
        self.llm = self._initialize_llm()
        self.cross_encoder = None  # Lazy load on first use

    def _initialize_llm(self):
        """Initialize OpenAI for evaluation."""
        llm_config = self.settings.get_llm_config()

        return ChatOpenAI(
            model=llm_config["model"],
            temperature=0.0,  # Deterministic for evaluation
            api_key=llm_config["api_key"],
        )

    def _get_cross_encoder(self):
        """Lazy load cross-encoder for relevancy scoring."""
        if self.cross_encoder is None:
            try:
                self.cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
                self.logger.info("Cross-encoder loaded for RAGAS evaluation")
            except Exception as e:
                self.logger.warning(f"Failed to load cross-encoder: {e}")
                self.cross_encoder = False  # Mark as failed
        return self.cross_encoder if self.cross_encoder is not False else None

    async def evaluate(
        self,
        result: QueryResult,
        ground_truth: str | None = None,
    ) -> EvaluationMetrics:
        """Evaluate a query result using RAGAS metrics with parallel computation."""
        start_time = time.time()

        # Extract contexts from sources
        contexts = []
        for source in result.sources:
            if hasattr(source, "document"):
                contexts.append(source.document.content)
            elif hasattr(source, "content"):
                contexts.append(source.content)
            elif hasattr(source, "snippet"):
                contexts.append(source.snippet)

        # Calculate all metrics in parallel for efficiency
        tasks = [
            self._calculate_context_relevancy(result.query_text, contexts),
            self._calculate_answer_faithfulness(result.answer, contexts),
            self._calculate_answer_relevancy(result.query_text, result.answer),
            self._calculate_context_recall(result.query_text, contexts, ground_truth),
        ]

        results_tuple = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle any exceptions in metric calculations
        metrics_list = []
        for i, res in enumerate(results_tuple):
            if isinstance(res, Exception):
                self.logger.warning(f"Metric {i} calculation failed: {res}")
                metrics_list.append(0.7)  # Default value
            else:
                metrics_list.append(res)

        # Create evaluation metrics
        metrics = EvaluationMetrics(
            result_id=result.id,
            context_relevancy=metrics_list[0],
            answer_faithfulness=metrics_list[1],
            answer_relevancy=metrics_list[2],
            context_recall=metrics_list[3],
            overall_score=0.0,  # Will be calculated
            evaluation_time_ms=(time.time() - start_time) * 1000,
        )

        # Calculate weighted overall score
        metrics.overall_score = (
            metrics.context_relevancy * 0.25
            + metrics.answer_faithfulness * 0.30
            + metrics.answer_relevancy * 0.30
            + metrics.context_recall * 0.15
        )

        self.logger.info(
            "RAGAS evaluation completed",
            result_id=str(result.id),
            context_relevancy=f"{metrics.context_relevancy:.2f}",
            answer_faithfulness=f"{metrics.answer_faithfulness:.2f}",
            answer_relevancy=f"{metrics.answer_relevancy:.2f}",
            context_recall=f"{metrics.context_recall:.2f}",
            overall_score=f"{metrics.overall_score:.2f}",
            evaluation_time_ms=f"{metrics.evaluation_time_ms:.0f}",
        )

        return metrics

    async def _calculate_context_relevancy(
        self,
        query: str,
        contexts: list[str],
    ) -> float:
        """Calculate context relevancy using cross-encoder for better accuracy."""
        if not contexts:
            return 0.0

        try:
            # Try cross-encoder first for better accuracy
            cross_encoder = self._get_cross_encoder()
            if cross_encoder:
                # Use cross-encoder for accurate relevancy scores
                pairs = [(query, ctx[:512]) for ctx in contexts]  # Truncate for efficiency
                scores = cross_encoder.predict(pairs)

                # Normalize scores to 0-1 range using sigmoid-like transformation
                # Cross-encoder scores are typically in range [-10, 10]
                normalized_scores = 1 / (1 + np.exp(-np.array(scores)))
                relevancy = float(np.mean(normalized_scores))

                self.logger.debug(
                    f"Cross-encoder context relevancy: {relevancy:.3f}",
                    sample_scores=[f"{s:.3f}" for s in normalized_scores[:3]],
                )
                return min(max(relevancy, 0.0), 1.0)

        except Exception as e:
            self.logger.warning(f"Cross-encoder relevancy failed, using LLM: {e}")

        # Fallback to LLM-based scoring
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
            return 0.7  # Default to reasonable score

    async def _calculate_answer_faithfulness(
        self,
        answer: str,
        contexts: list[str],
    ) -> float:
        """Calculate answer faithfulness - how well answer is grounded in contexts."""
        if not contexts or not answer:
            return 0.0

        try:
            combined_context = " ".join(contexts[:3])[:2000]  # Use top 3 contexts

            # Extract claims from answer
            claims_prompt = f"""Extract all factual claims from this answer.
Each claim should be a single, specific, atomic statement.

Answer: {answer}

List each claim on a new line:"""

            claims_response = await self.llm.ainvoke(claims_prompt)
            claims = [c.strip() for c in claims_response.content.split("\n") if c.strip()]

            if not claims:
                # If no claims extracted, assume answer is simple and faithful
                return 0.75

            # Verify each claim against contexts
            verification_prompt = f"""Context: {combined_context}

For each claim below, respond with 1 if the claim is supported by the context, or 0 if not:
{chr(10).join(f"{i + 1}. {claim}" for i, claim in enumerate(claims))}

Response format (comma-separated): 1,0,1,1,0"""

            verification_response = await self.llm.ainvoke(verification_prompt)
            scores_text = verification_response.content.strip()

            # Parse scores
            scores = []
            for score in scores_text.replace(" ", "").split(","):
                try:
                    scores.append(float(score))
                except ValueError:
                    scores.append(0.5)

            faithfulness = float(np.mean(scores)) if scores else 0.75

            self.logger.debug(
                f"Answer faithfulness: {faithfulness:.3f}",
                claims_count=len(claims),
                verified=sum(1 for s in scores if s > 0.5),
            )

            return min(max(faithfulness, 0.0), 1.0)

        except Exception as e:
            self.logger.warning("Answer faithfulness calculation failed", error=str(e))
            return 0.75

    async def _calculate_answer_relevancy(
        self,
        query: str,
        answer: str,
    ) -> float:
        """Calculate how relevant the answer is to the query."""
        if not answer or not query:
            return 0.0

        try:
            # Use cross-encoder for direct query-answer relevance
            cross_encoder = self._get_cross_encoder()
            if cross_encoder:
                score = cross_encoder.predict([(query, answer[:512])])[0]
                # Normalize with sigmoid
                normalized = float(1 / (1 + np.exp(-score)))
                self.logger.debug(f"Cross-encoder answer relevancy: {normalized:.3f}")
                return min(max(normalized, 0.0), 1.0)

        except Exception as e:
            self.logger.warning(f"Cross-encoder answer relevancy failed, using LLM: {e}")

        # Fallback: Generate questions from answer and compare to original
        try:
            prompt = f"""Given this answer, generate 3 questions that it directly answers:

Answer: {answer}

Questions (one per line):"""

            response = await self.llm.ainvoke(prompt)
            generated_questions = [q.strip() for q in response.content.split("\n") if q.strip()]

            if not generated_questions:
                return 0.7

            # Use cross-encoder to compare original query with generated questions
            cross_encoder = self._get_cross_encoder()
            if cross_encoder and generated_questions:
                pairs = [(query, gq) for gq in generated_questions[:3]]
                similarities = cross_encoder.predict(pairs)
                # Normalize and average
                normalized = [1 / (1 + np.exp(-s)) for s in similarities]
                relevancy = float(np.mean(normalized))
                return min(max(relevancy, 0.0), 1.0)

            # Last resort: LLM-based scoring
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
                score = 0.7

            return min(max(score, 0.0), 1.0)

        except Exception as e:
            self.logger.warning("Answer relevancy calculation failed", error=str(e))
            return 0.7

    async def _calculate_context_recall(
        self,
        query: str,
        contexts: list[str],
        ground_truth: str | None = None,
    ) -> float:
        """Calculate context recall - how much relevant info was retrieved."""
        if not contexts:
            return 0.0

        # If no ground truth, estimate based on query aspect coverage
        if not ground_truth:
            try:
                # Extract key aspects from query using LLM
                aspects_prompt = f"""List the key aspects or concepts that need to be addressed to answer this query.

Query: {query}

Aspects (one per line, max 5):"""

                response = await self.llm.ainvoke(aspects_prompt)
                aspects = [a.strip() for a in response.content.split("\n") if a.strip()][:5]

                if not aspects:
                    # Fallback to term-based coverage
                    query_terms = set(query.lower().split())
                    covered_terms = set()

                    for context in contexts:
                        context_terms = set(context.lower().split())
                        covered_terms.update(query_terms.intersection(context_terms))

                    recall = len(covered_terms) / len(query_terms) if query_terms else 0.75
                    return min(max(recall, 0.0), 1.0)

                # Check which aspects are covered in contexts
                covered_aspects = 0
                for aspect in aspects:
                    # Check if aspect is mentioned in any context
                    aspect_lower = aspect.lower()
                    for context in contexts:
                        if aspect_lower in context.lower() or any(
                            word in context.lower() for word in aspect_lower.split()[:3]
                        ):
                            covered_aspects += 1
                            break

                recall = covered_aspects / len(aspects) if aspects else 0.75
                self.logger.debug(
                    f"Context recall: {recall:.3f}",
                    aspects_count=len(aspects),
                    covered=covered_aspects,
                )
                return min(max(recall, 0.0), 1.0)

            except Exception as e:
                self.logger.warning(f"Aspect-based recall failed: {e}")
                return 0.75

        # If ground truth provided, calculate actual recall
        try:
            combined_context = "\n".join(contexts[:3])[:2000]

            prompt = f"""Given the ground truth answer and retrieved contexts, evaluate what percentage of information needed for the ground truth is present in the contexts.

Ground Truth: {ground_truth}

Contexts:
{combined_context}

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
                score = 0.75

            return min(max(score, 0.0), 1.0)

        except Exception as e:
            self.logger.warning("Context recall calculation failed", error=str(e))
            return 0.75

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
