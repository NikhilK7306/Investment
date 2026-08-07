"""Reflection Agent - Learns from past predictions vs actual outcomes."""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from app.agents.base import BaseAgent, AgentContext, AgentResult
from app.domain.enums.enums import (
    AgentName,
    AgentStatus,
    PredictionType,
    OutcomeStatus,
    LessonType,
)
from app.domain.entities.entities import (
    ReflectionMemory,
    Lesson,
    ExperienceMemory,
)
from app.domain.value_objects.value_objects import Prediction
from app.core.exceptions.base import AgentError


class ReflectionAgent(BaseAgent[Dict[str, Any], Dict[str, Any]]):
    """Agent that performs reflection on past predictions to improve future analysis."""

    def __init__(self):
        super().__init__(
            name=AgentName.REFLECTION,
            description="Analyzes past predictions vs outcomes to extract lessons and improve agents",
            version="1.0.0",
            max_retries=1,
            timeout_seconds=120,
        )
        # In-memory storage (in production, use persistent storage)
        self._predictions: Dict[str, Prediction] = {}
        self._reflections: Dict[str, ReflectionMemory] = {}
        self._lessons: Dict[str, Lesson] = {}
        self._outcome_data: Dict[str, Dict] = {}

    @property
    def system_prompt(self) -> str:
        return """You are the Reflection Agent for the IPO Intelligence System.

Your mission is to enable continuous learning by comparing predictions to reality:

REFLECTION PROCESS:
1. IDENTIFY PREDICTIONS DUE FOR VERIFICATION
   - Find predictions where enough time has passed
   - Minimum delay: 30 days for price predictions, 90 days for fundamentals

2. FETCH ACTUAL OUTCOMES
   - Stock price performance (1D, 1W, 1M, 3M, 6M, 12M)
   - Financial results vs predictions
   - Key events (earnings, guidance, M&A, regulatory)

3. CALCULATE ACCURACY
   - Directional accuracy (up/down)
   - Magnitude accuracy (percentage error)
   - Confidence calibration (predicted vs actual confidence)

4. ANALYZE ERRORS
   - What did we get wrong?
   - What assumptions failed?
   - What factors did we miss?
   - What data was misleading?

5. IDENTIFY CORRECT ASSESSMENTS
   - What did we get right?
   - Which reasoning patterns worked?
   - Which data sources were reliable?

6. EXTRACT LESSONS
   - Prompt improvements for each agent
   - Tool usage optimizations
   - Data source adjustments
   - Scoring weight changes
   - New risk factors to consider
   - Best practices to reinforce

7. UPDATE MEMORY SYSTEMS
   - Store reflections in reflection memory
   - Update failure memory for mistakes
   - Update success memory for correct predictions
   - Update knowledge memory with verified facts
   - Create lessons for applicable agents
   - Update best practices

8. CALIBRATE AGENTS
   - Adjust confidence thresholds
   - Modify scoring weights
   - Update prompts with lessons
   - Flag systemic biases

OUTPUT:
- Reflection reports per prediction
- Aggregated accuracy metrics
- Specific prompt/tool improvements per agent
- Knowledge base updates
- New lessons learned
- Calibration recommendations"""

    @property
    def available_tools(self) -> List[str]:
        return [
            "get_pending_predictions",
            "fetch_actual_outcomes",
            "calculate_accuracy",
            "analyze_prediction_errors",
            "extract_lessons",
            "update_agent_prompts",
            "update_scoring_weights",
            "update_knowledge_base",
            "calibrate_confidence",
            "generate_reflection_report",
        ]

    async def execute(
        self,
        context: AgentContext,
        input_data: Dict[str, Any],
    ) -> AgentResult[Dict[str, Any]]:
        """Execute reflection process."""
        start_time = datetime.utcnow()

        try:
            operation = input_data.get("operation", "run_reflection")

            if operation == "run_reflection":
                result = await self._run_reflection_cycle(context, input_data)
            elif operation == "verify_outcome":
                result = await self._verify_single_outcome(context, input_data)
            elif operation == "get_accuracy_stats":
                result = await self._get_accuracy_stats(context, input_data)
            elif operation == "calibrate_agents":
                result = await self._calibrate_agents(context, input_data)
            elif operation == "extract_lessons":
                result = await self._extract_lessons_batch(context, input_data)
            else:
                return AgentResult(
                    agent_name=self.name,
                    status=AgentStatus.FAILED,
                    error=f"Unknown operation: {operation}",
                    error_type="INVALID_OPERATION",
                )

            duration = (datetime.utcnow() - start_time).total_seconds() * 1000

            return AgentResult(
                agent_name=self.name,
                status=AgentStatus.COMPLETED,
                data=result,
                confidence=0.9,
                reasoning=f"Reflection {operation} completed",
                evidence=[f"Operation: {operation}"],
                duration_ms=duration,
            )

        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            return AgentResult(
                agent_name=self.name,
                status=AgentStatus.FAILED,
                error=str(e),
                error_type=type(e).__name__,
                duration_ms=duration,
            )

    async def _run_reflection_cycle(self, context: AgentContext, input_data: Dict) -> Dict:
        """Run a full reflection cycle."""
        min_delay_days = input_data.get("min_delay_days", 30)
        batch_size = input_data.get("batch_size", 50)

        # Get predictions pending verification
        pending = await self._get_pending_predictions(min_delay_days, batch_size)

        results = {
            "processed": 0,
            "verified": 0,
            "expired": 0,
            "inconclusive": 0,
            "reflections_created": 0,
            "lessons_extracted": 0,
            "prompt_improvements": 0,
            "knowledge_updates": 0,
            "accuracy_by_type": {},
            "accuracy_by_agent": {},
        }

        for prediction in pending:
            try:
                # Verify outcome
                outcome = await self._fetch_actual_outcome(prediction)
                if outcome is None:
                    results["inconclusive"] += 1
                    continue

                # Calculate accuracy
                accuracy = self._calculate_accuracy(prediction, outcome)

                # Create reflection
                reflection = await self._create_reflection(prediction, outcome, accuracy)
                results["reflections_created"] += 1

                # Extract lessons
                lessons = await self._extract_lessons_from_reflection(reflection)
                results["lessons_extracted"] += len(lessons)

                # Update statistics
                pred_type = prediction.prediction_type
                if pred_type not in results["accuracy_by_type"]:
                    results["accuracy_by_type"][pred_type] = []
                results["accuracy_by_type"][pred_type].append(accuracy)

                results["processed"] += 1
                results["verified"] += 1

            except Exception as e:
                # Log error but continue
                results["errors"] = results.get("errors", [])
                results["errors"].append(str(e))

        # Aggregate accuracy
        for pred_type, accuracies in results["accuracy_by_type"].items():
            results["accuracy_by_type"][pred_type] = {
                "mean": sum(accuracies) / len(accuracies),
                "count": len(accuracies),
                "median": sorted(accuracies)[len(accuracies) // 2],
            }

        return results

    async def _get_pending_predictions(
        self,
        min_delay_days: int,
        batch_size: int,
    ) -> List[Prediction]:
        """Get predictions pending verification."""
        cutoff = datetime.utcnow() - timedelta(days=min_delay_days)
        pending = []

        for pred in self._predictions.values():
            if pred.created_at <= cutoff and pred.metadata.get("status") == "pending":
                pending.append(pred)
                if len(pending) >= batch_size:
                    break

        return pending

    async def _fetch_actual_outcome(self, prediction: Prediction) -> Optional[Dict]:
        """Fetch actual outcome for a prediction."""
        # In production, this would query market data APIs
        # For now, return simulated outcome
        pred_type = prediction.prediction_type
        symbol = prediction.metadata.get("symbol", "")

        # Simulate fetching real data
        if pred_type.startswith("price_change"):
            # Would fetch actual price change from market data
            return {
                "actual_value": 0.05,  # 5% actual change
                "source": "market_data",
                "timestamp": datetime.utcnow().isoformat(),
            }
        elif pred_type == "outperform_market":
            return {
                "actual_value": 1.0,  # True
                "source": "market_data",
                "timestamp": datetime.utcnow().isoformat(),
            }
        elif pred_type == "bankruptcy_risk":
            return {
                "actual_value": 0.0,  # False
                "source": "financial_data",
                "timestamp": datetime.utcnow().isoformat(),
            }

        return None

    def _calculate_accuracy(self, prediction: Prediction, outcome: Dict) -> float:
        """Calculate prediction accuracy."""
        predicted = prediction.predicted_value
        actual = outcome.get("actual_value", 0)

        if prediction.prediction_type.startswith("price_change"):
            # For price changes, use directional + magnitude accuracy
            direction_correct = (predicted > 0) == (actual > 0)
            if abs(predicted) < 0.01 and abs(actual) < 0.01:
                magnitude_acc = 1.0
            else:
                magnitude_acc = max(0, 1 - abs(predicted - actual) / max(abs(predicted), abs(actual), 0.01))
            return (1.0 if direction_correct else 0.0) * 0.5 + magnitude_acc * 0.5

        elif prediction.prediction_type in ["outperform_market", "underperform_market", "bankruptcy_risk", "acquisition_target"]:
            # Binary predictions
            return 1.0 if (predicted > 0.5) == (actual > 0.5) else 0.0

        else:
            # Continuous predictions
            if abs(predicted) < 0.01:
                return 1.0 if abs(actual) < 0.01 else 0.0
            return max(0, 1 - abs(predicted - actual) / max(abs(predicted), 0.01))

    async def _create_reflection(
        self,
        prediction: Prediction,
        outcome: Dict,
        accuracy: float,
    ) -> ReflectionMemory:
        """Create reflection memory entry."""
        # Analyze what went wrong/right
        mistakes = []
        correct = []
        missing = []

        if accuracy < 0.5:
            mistakes.append(f"Prediction error: {abs(prediction.predicted_value - outcome.get('actual_value', 0)):.2%}")
            if prediction.predicted_value > outcome.get('actual_value', 0):
                mistakes.append("Overestimated positive outcome")
            else:
                mistakes.append("Underestimated negative outcome")
        else:
            correct.append("Direction and magnitude approximately correct")

        # Check assumptions
        for assumption in prediction.assumptions:
            if accuracy > 0.7:
                correct.append(f"Assumption validated: {assumption}")
            else:
                mistakes.append(f"Assumption failed: {assumption}")

        # Identify missing factors
        if accuracy < 0.6:
            missing.append("Market regime change not accounted for")
            missing.append("Company-specific catalyst not modeled")

        reflection = ReflectionMemory(
            prediction_id=prediction.id,
            ipo_symbol=prediction.metadata.get("symbol", ""),
            prediction_type=prediction.prediction_type,
            predicted_value=prediction.predicted_value,
            actual_value=outcome.get("actual_value", 0),
            accuracy=accuracy,
            error=abs(prediction.predicted_value - outcome.get("actual_value", 0)),
            mistakes_identified=mistakes,
            correct_assumptions=correct,
            missing_factors=missing,
            lessons_extracted=self._generate_lessons(mistakes, correct, missing),
            prompt_improvements=self._generate_prompt_improvements(mistakes, prediction),
            strategy_changes=self._generate_strategy_changes(mistakes),
            knowledge_updates=self._generate_knowledge_updates(correct, mistakes),
        )

        self._reflections[str(reflection.id)] = reflection
        return reflection

    def _generate_lessons(self, mistakes: List[str], correct: List[str], missing: List[str]) -> List[str]:
        """Generate lessons from reflection."""
        lessons = []
        for m in mistakes:
            lessons.append(f"LEARNED: {m}")
        for c in correct:
            lessons.append(f"VALIDATED: {c}")
        for m in missing:
            lessons.append(f"MISSING FACTOR: {m}")
        return lessons

    def _generate_prompt_improvements(self, mistakes: List[str], prediction: Prediction) -> List[str]:
        """Generate prompt improvements based on mistakes."""
        improvements = []
        for m in mistakes:
            if "overestimated" in m.lower():
                improvements.append("Add explicit caution against overconfidence in growth assumptions")
            elif "underestimated" in m.lower():
                improvements.append("Add explicit consideration of downside scenarios")
            elif "assumption failed" in m.lower():
                improvements.append("Require explicit validation of key assumptions before prediction")
        return improvements

    def _generate_strategy_changes(self, mistakes: List[str]) -> List[str]:
        """Generate strategy changes."""
        changes = []
        if any("market regime" in m.lower() for m in mistakes):
            changes.append("Add market regime detection to analysis pipeline")
        if any("catalyst" in m.lower() for m in mistakes):
            changes.append("Improve catalyst identification and timing models")
        return changes

    def _generate_knowledge_updates(self, correct: List[str], mistakes: List[str]) -> List[str]:
        """Generate knowledge base updates."""
        updates = []
        for c in correct:
            updates.append(f"CONFIRMED: {c}")
        for m in mistakes:
            if "assumption" in m.lower():
                updates.append(f"REVISE: {m}")
        return updates

    async def _extract_lessons_from_reflection(self, reflection: ReflectionMemory) -> List[Lesson]:
        """Extract structured lessons from reflection."""
        lessons = []

        for lesson_text in reflection.lessons_extracted:
            lesson = Lesson(
                lesson_type=LessonType.REASONING_PATTERN,
                title=lesson_text[:100],
                description=lesson_text,
                do=reflection.correct_assumptions,
                dont=reflection.mistakes_identified,
                best_practices=reflection.prompt_improvements,
                anti_patterns=reflection.missing_factors,
                confidence=reflection.accuracy,
                evidence=[{"reflection_id": str(reflection.id), "prediction_id": str(reflection.prediction_id)}],
                applicable_agents=[],  # Would be determined by prediction metadata
                tags=["reflection", reflection.prediction_type],
            )
            self._lessons[str(lesson.id)] = lesson
            lessons.append(lesson)

        return lessons

    async def _verify_single_outcome(self, context: AgentContext, input_data: Dict) -> Dict:
        """Verify a single prediction outcome."""
        prediction_id = input_data.get("prediction_id")
        actual_value = input_data.get("actual_value")

        prediction = self._predictions.get(prediction_id)
        if not prediction:
            return {"error": "Prediction not found"}

        accuracy = self._calculate_accuracy(prediction, {"actual_value": actual_value})

        reflection = await self._create_reflection(prediction, {"actual_value": actual_value}, accuracy)

        # Update prediction status
        prediction.metadata["status"] = "verified"
        prediction.metadata["actual_value"] = actual_value
        prediction.metadata["accuracy"] = accuracy
        prediction.metadata["verified_at"] = datetime.utcnow().isoformat()

        return {
            "prediction_id": prediction_id,
            "accuracy": accuracy,
            "reflection_id": str(reflection.id),
            "lessons": len(reflection.lessons_extracted),
        }

    async def _get_accuracy_stats(self, context: AgentContext, input_data: Dict) -> Dict:
        """Get accuracy statistics."""
        predictions = list(self._predictions.values())
        verified = [p for p in predictions if p.metadata.get("status") == "verified"]

        if not verified:
            return {"total_predictions": len(predictions), "verified": 0}

        stats = {
            "total_predictions": len(predictions),
            "verified": len(verified),
            "overall_accuracy": sum(p.metadata.get("accuracy", 0) for p in verified) / len(verified),
            "by_type": {},
            "by_agent": {},
            "by_confidence": {},
            "calibration": [],
        }

        # By type
        for p in verified:
            pred_type = p.prediction_type
            if pred_type not in stats["by_type"]:
                stats["by_type"][pred_type] = []
            stats["by_type"][pred_type].append(p.metadata.get("accuracy", 0))

        for pred_type, accs in stats["by_type"].items():
            stats["by_type"][pred_type] = {
                "mean": sum(accs) / len(accs),
                "count": len(accs),
            }

        # Calibration: predicted confidence vs actual accuracy
        confidence_buckets = [(0, 0.3), (0.3, 0.5), (0.5, 0.7), (0.7, 0.9), (0.9, 1.0)]
        for low, high in confidence_buckets:
            bucket = [p for p in verified if low <= p.confidence < high]
            if bucket:
                avg_accuracy = sum(p.metadata.get("accuracy", 0) for p in bucket) / len(bucket)
                avg_confidence = sum(p.confidence for p in bucket) / len(bucket)
                stats["calibration"].append({
                    "confidence_range": f"{low:.0%}-{high:.0%}",
                    "avg_confidence": avg_confidence,
                    "avg_accuracy": avg_accuracy,
                    "count": len(bucket),
                    "calibration_error": abs(avg_confidence - avg_accuracy),
                })

        return stats

    async def _calibrate_agents(self, context: AgentContext, input_data: Dict) -> Dict:
        """Calibrate agent confidence based on historical accuracy."""
        stats = await self._get_accuracy_stats(context, input_data)

        calibrations = {}
        for cal in stats.get("calibration", []):
            if cal["count"] >= 5:  # Minimum samples
                error = cal["calibration_error"]
                if error > 0.15:
                    calibrations[cal["confidence_range"]] = {
                        "adjustment": "reduce" if cal["avg_confidence"] > cal["avg_accuracy"] else "increase",
                        "magnitude": error,
                    }

        return {
            "calibrations_needed": calibrations,
            "overall_calibration_error": sum(c["calibration_error"] * c["count"] for c in stats["calibration"]) / max(sum(c["count"] for c in stats["calibration"]), 1),
        }

    async def _extract_lessons_batch(self, context: AgentContext, input_data: Dict) -> Dict:
        """Extract lessons from recent reflections."""
        limit = input_data.get("limit", 100)
        reflections = list(self._reflections.values())[-limit:]

        all_lessons = []
        for reflection in reflections:
            lessons = await self._extract_lessons_from_reflection(reflection)
            all_lessons.extend(lessons)

        # Aggregate by type
        by_type = {}
        for lesson in all_lessons:
            ltype = lesson.lesson_type.value
            if ltype not in by_type:
                by_type[ltype] = 0
            by_type[ltype] += 1

        return {
            "total_lessons": len(all_lessons),
            "by_type": by_type,
            "lesson_ids": [str(l.id) for l in all_lessons],
        }

    def register_prediction(self, prediction: Prediction) -> None:
        """Register a new prediction for future verification."""
        self._predictions[str(prediction.id)] = prediction

    def get_prediction(self, prediction_id: str) -> Optional[Prediction]:
        """Get prediction by ID."""
        return self._predictions.get(prediction_id)

    def get_reflection(self, reflection_id: str) -> Optional[ReflectionMemory]:
        """Get reflection by ID."""
        return self._reflections.get(reflection_id)

    def get_stats(self) -> Dict[str, int]:
        """Get reflection statistics."""
        return {
            "total_predictions": len(self._predictions),
            "pending_verification": sum(1 for p in self._predictions.values() if p.metadata.get("status") == "pending"),
            "verified": sum(1 for p in self._predictions.values() if p.metadata.get("status") == "verified"),
            "reflections": len(self._reflections),
            "lessons": len(self._lessons),
        }


def create_reflection_agent() -> ReflectionAgent:
    """Create reflection agent instance."""
    return ReflectionAgent()