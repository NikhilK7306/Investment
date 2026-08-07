"""Use cases for memory management and reflection."""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from app.application.interfaces.repositories import (
    MemoryRepository,
    FailureMemoryRepository,
    SuccessMemoryRepository,
    KnowledgeMemoryRepository,
    BestPracticeRepository,
    ReflectionMemoryRepository,
    LessonRepository,
)
from app.domain.enums.enums import (
    MemoryType,
    AgentName,
    FailureCategory,
    Severity,
    LessonType,
    PredictionType,
)
from app.domain.entities.entities import (
    MemoryEntry,
    FailureMemory,
    SuccessMemory,
    KnowledgeMemory,
    BestPracticeMemory,
    ReflectionMemory,
    Lesson,
)


class StoreMemoryUseCase:
    """Use case for storing memory."""

    def __init__(self, memory_repo: MemoryRepository):
        self.memory_repo = memory_repo

    async def execute(
        self,
        memory_type: MemoryType,
        content: Dict[str, Any],
        embedding: Optional[List[float]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        ipo_symbol: Optional[str] = None,
        analysis_id: Optional[UUID] = None,
    ) -> UUID:
        """Store memory entry."""
        return await self.memory_repo.store(
            memory_type=memory_type,
            content=content,
            embedding=embedding,
            metadata=metadata,
            ipo_symbol=ipo_symbol,
            analysis_id=analysis_id,
        )


class SearchMemoryUseCase:
    """Use case for searching memory."""

    def __init__(self, memory_repo: MemoryRepository):
        self.memory_repo = memory_repo

    async def execute(
        self,
        memory_type: MemoryType,
        query_embedding: List[float],
        limit: int = 10,
        threshold: float = 0.75,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[MemoryEntry, float]]:
        """Search memory by semantic similarity."""
        return await self.memory_repo.search(
            memory_type=memory_type,
            query_embedding=query_embedding,
            limit=limit,
            threshold=threshold,
            filters=filters,
        )


class GetRecentMemoryUseCase:
    """Use case for getting recent memory entries."""

    def __init__(self, memory_repo: MemoryRepository):
        self.memory_repo = memory_repo

    async def execute(
        self,
        memory_type: MemoryType,
        limit: int = 100,
        ipo_symbol: Optional[str] = None,
    ) -> List[MemoryEntry]:
        """Get recent memory entries."""
        return await self.memory_repo.get_recent(memory_type, limit, ipo_symbol)


class CleanupMemoryUseCase:
    """Use case for cleaning up old memory entries."""

    def __init__(self, memory_repo: MemoryRepository):
        self.memory_repo = memory_repo

    async def execute(
        self,
        memory_type: MemoryType,
        older_than_days: int,
    ) -> int:
        """Delete old memory entries."""
        return await self.memory_repo.delete_old_entries(memory_type, older_than_days)


class RecordFailureUseCase:
    """Use case for recording a failure."""

    def __init__(self, failure_repo: FailureMemoryRepository):
        self.failure_repo = failure_repo

    async def execute(
        self,
        agent_name: AgentName,
        error_type: str,
        error_message: str,
        stack_trace: str = "",
        root_cause: str = "",
        attempted_fix: str = "",
        category: FailureCategory = FailureCategory.UNKNOWN,
        severity: Severity = Severity.MEDIUM,
        ipo_symbol: Optional[str] = None,
        analysis_id: Optional[UUID] = None,
    ) -> FailureMemory:
        """Record a failure."""
        import hashlib
        similarity_hash = hashlib.md5(
            f"{agent_name.value}:{error_message[:200]}".encode()
        ).hexdigest()[:16]

        # Check if similar failure exists
        existing = await self.failure_repo.find_similar(
            error_message=error_message,
            agent_name=agent_name,
            threshold=0.8,
            limit=1,
        )

        if existing:
            # Increment occurrences
            failure = existing[0][0]
            failure.occurrences += 1
            failure.last_occurrence = datetime.utcnow()
            failure.stack_trace = stack_trace or failure.stack_trace
            failure.root_cause = root_cause or failure.root_cause
            failure.attempted_fix = attempted_fix or failure.attempted_fix
            return failure

        # Create new failure
        failure = FailureMemory(
            failure_id=similarity_hash,
            agent_name=agent_name,
            error_type=error_type,
            error_message=error_message,
            stack_trace=stack_trace,
            root_cause=root_cause,
            attempted_fix=attempted_fix,
            resolved=False,
            confidence=0.0,
            category=category,
            severity=severity,
            similarity_hash=similarity_hash,
        )

        # Store in repository
        await self.failure_repo.store(
            memory_type=MemoryType.FAILURE,
            content={
                "failure_id": failure.failure_id,
                "agent_name": agent_name,
                "error_type": error_type,
                "error_message": error_message,
                "stack_trace": stack_trace,
                "root_cause": root_cause,
                "attempted_fix": attempted_fix,
                "resolved": False,
                "confidence": 0.0,
                "category": category.value,
                "severity": severity.value,
                "similarity_hash": similarity_hash,
            },
            metadata={"ipo_symbol": ipo_symbol, "analysis_id": str(analysis_id) if analysis_id else None},
            ipo_symbol=ipo_symbol,
            analysis_id=analysis_id,
        )

        return failure


class FindSimilarFailuresUseCase:
    """Use case for finding similar failures."""

    def __init__(self, failure_repo: FailureMemoryRepository):
        self.failure_repo = failure_repo

    async def execute(
        self,
        error_message: str,
        agent_name: AgentName,
        threshold: float = 0.8,
        limit: int = 5,
    ) -> List[Tuple[FailureMemory, float]]:
        """Find similar failures."""
        return await self.failure_repo.find_similar(
            error_message=error_message,
            agent_name=agent_name,
            threshold=threshold,
            limit=limit,
        )


class GetFailuresByCategoryUseCase:
    """Use case for getting failures by category."""

    def __init__(self, failure_repo: FailureMemoryRepository):
        self.failure_repo = failure_repo

    async def execute(
        self,
        category: str,
        limit: int = 50,
    ) -> List[FailureMemory]:
        """Get failures by category."""
        return await self.failure_repo.get_by_category(category, limit)


class MarkFailureResolvedUseCase:
    """Use case for marking a failure as resolved."""

    def __init__(self, failure_repo: FailureMemoryRepository):
        self.failure_repo = failure_repo

    async def execute(
        self,
        failure_id: UUID,
        resolution: str,
    ) -> bool:
        """Mark failure as resolved."""
        return await self.failure_repo.mark_resolved(failure_id, resolution)


class GetUnresolvedFailuresUseCase:
    """Use case for getting unresolved failures."""

    def __init__(self, failure_repo: FailureMemoryRepository):
        self.failure_repo = failure_repo

    async def execute(
        self,
        agent_name: Optional[AgentName] = None,
        limit: int = 100,
    ) -> List[FailureMemory]:
        """Get unresolved failures."""
        return await self.failure_repo.get_unresolved(agent_name, limit)


class RecordSuccessUseCase:
    """Use case for recording a success."""

    def __init__(self, success_repo: SuccessMemoryRepository):
        self.success_repo = success_repo

    async def execute(
        self,
        agent_name: AgentName,
        strategy_description: str,
        prompt_used: str = "",
        tool_sequence: List[str] = None,
        api_sequence: List[str] = None,
        confidence: float = 0.0,
        success_rate: float = 1.0,
        context: Dict[str, Any] = None,
        ipo_symbol: Optional[str] = None,
        analysis_id: Optional[UUID] = None,
    ) -> SuccessMemory:
        """Record a successful strategy."""
        import hashlib
        import json

        context_hash = hashlib.md5(
            json.dumps(context or {}, sort_keys=True).encode()
        ).hexdigest()[:16]

        success = SuccessMemory(
            success_id=f"{agent_name.value}_{context_hash}",
            agent_name=agent_name,
            strategy_description=strategy_description,
            prompt_used=prompt_used,
            tool_sequence=tool_sequence or [],
            api_sequence=api_sequence or [],
            confidence=confidence,
            success_rate=success_rate,
            context_hash=context_hash,
        )

        await self.success_repo.store(
            memory_type=MemoryType.SUCCESS,
            content={
                "success_id": success.success_id,
                "agent_name": agent_name,
                "strategy": strategy_description,
                "prompt_used": prompt_used,
                "tool_sequence": tool_sequence or [],
                "api_sequence": api_sequence or [],
                "confidence": confidence,
                "success_rate": success_rate,
                "context_hash": context_hash,
            },
            metadata={"ipo_symbol": ipo_symbol, "analysis_id": str(analysis_id) if analysis_id else None},
            ipo_symbol=ipo_symbol,
            analysis_id=analysis_id,
        )

        return success


class FindSuccessfulStrategiesUseCase:
    """Use case for finding successful strategies."""

    def __init__(self, success_repo: SuccessMemoryRepository):
        self.success_repo = success_repo

    async def execute(
        self,
        context: Dict[str, Any],
        agent_name: AgentName,
        threshold: float = 0.75,
        limit: int = 5,
    ) -> List[Tuple[SuccessMemory, float]]:
        """Find successful strategies for context."""
        return await self.success_repo.find_successful_strategies(
            context=context,
            agent_name=agent_name,
            threshold=threshold,
            limit=limit,
        )


class IncrementSuccessReuseUseCase:
    """Use case for incrementing success reuse count."""

    def __init__(self, success_repo: SuccessMemoryRepository):
        self.success_repo = success_repo

    async def execute(self, success_id: UUID) -> bool:
        """Increment reuse count."""
        return await self.success_repo.increment_reuse_count(success_id)


class StoreKnowledgeUseCase:
    """Use case for storing knowledge."""

    def __init__(self, knowledge_repo: KnowledgeMemoryRepository):
        self.knowledge_repo = knowledge_repo

    async def execute(
        self,
        concept: str,
        description: str,
        evidence: List[Dict[str, Any]] = None,
        confidence: float = 0.0,
        domain: str = "",
        tags: List[str] = None,
    ) -> KnowledgeMemory:
        """Store knowledge."""
        knowledge = KnowledgeMemory(
            concept=concept,
            description=description,
            evidence=evidence or [],
            confidence=confidence,
            domain=domain,
            tags=tags or [],
        )

        await self.knowledge_repo.store(
            memory_type=MemoryType.KNOWLEDGE,
            content={
                "concept": concept,
                "description": description,
                "evidence": evidence or [],
                "confidence": confidence,
                "domain": domain,
                "tags": tags or [],
            },
        )

        return knowledge


class SearchKnowledgeUseCase:
    """Use case for searching knowledge."""

    def __init__(self, knowledge_repo: KnowledgeMemoryRepository):
        self.knowledge_repo = knowledge_repo

    async def get_by_concept(
        self,
        concept: str,
        domain: Optional[str] = None,
    ) -> Optional[KnowledgeMemory]:
        """Get knowledge by concept."""
        return await self.knowledge_repo.get_by_concept(concept, domain)

    async def search_concepts(
        self,
        query_embedding: List[float],
        limit: int = 10,
        threshold: float = 0.7,
    ) -> List[Tuple[KnowledgeMemory, float]]:
        """Search knowledge concepts."""
        return await self.knowledge_repo.search_concepts(query_embedding, limit, threshold)

    async def get_by_domain(
        self,
        domain: str,
        limit: int = 50,
    ) -> List[KnowledgeMemory]:
        """Get knowledge by domain."""
        return await self.knowledge_repo.get_by_domain(domain, limit)


class StoreBestPracticeUseCase:
    """Use case for storing best practice."""

    def __init__(self, practice_repo: BestPracticeRepository):
        self.practice_repo = practice_repo

    async def execute(
        self,
        practice_name: str,
        description: str,
        applicable_context: Dict[str, Any] = None,
        success_rate: float = 0.0,
        tags: List[str] = None,
    ) -> BestPracticeMemory:
        """Store best practice."""
        practice = BestPracticeMemory(
            practice_name=practice_name,
            description=description,
            applicable_context=applicable_context or {},
            success_rate=success_rate,
            tags=tags or [],
        )

        await self.practice_repo.store(
            memory_type=MemoryType.BEST_PRACTICE,
            content={
                "practice_name": practice_name,
                "description": description,
                "applicable_context": applicable_context or {},
                "success_rate": success_rate,
                "tags": tags or [],
            },
        )

        return practice


class GetApplicablePracticesUseCase:
    """Use case for getting applicable best practices."""

    def __init__(self, practice_repo: BestPracticeRepository):
        self.practice_repo = practice_repo

    async def execute(
        self,
        context: Dict[str, Any],
        limit: int = 10,
    ) -> List[BestPracticeMemory]:
        """Get best practices applicable to context."""
        return await self.practice_repo.get_applicable_practices(context, limit)


class IncrementPracticeUsageUseCase:
    """Use case for incrementing best practice usage."""

    def __init__(self, practice_repo: BestPracticeRepository):
        self.practice_repo = practice_repo

    async def execute(self, practice_id: UUID) -> bool:
        """Increment usage count."""
        return await self.practice_repo.increment_usage(practice_id)


class RecordReflectionUseCase:
    """Use case for recording a reflection."""

    def __init__(self, reflection_repo: ReflectionMemoryRepository):
        self.reflection_repo = reflection_repo

    async def execute(
        self,
        prediction_id: UUID,
        ipo_symbol: str,
        prediction_type: PredictionType,
        predicted_value: float,
        actual_value: float,
        accuracy: float,
        mistakes_identified: List[str] = None,
        correct_assumptions: List[str] = None,
        missing_factors: List[str] = None,
        lessons_extracted: List[str] = None,
        prompt_improvements: List[str] = None,
        strategy_changes: List[str] = None,
        knowledge_updates: List[str] = None,
    ) -> ReflectionMemory:
        """Record reflection after outcome verification."""
        reflection = ReflectionMemory(
            prediction_id=prediction_id,
            ipo_symbol=ipo_symbol,
            prediction_type=prediction_type,
            predicted_value=predicted_value,
            actual_value=actual_value,
            accuracy=accuracy,
            error=abs(predicted_value - actual_value),
            mistakes_identified=mistakes_identified or [],
            correct_assumptions=correct_assumptions or [],
            missing_factors=missing_factors or [],
            lessons_extracted=lessons_extracted or [],
            prompt_improvements=prompt_improvements or [],
            strategy_changes=strategy_changes or [],
            knowledge_updates=knowledge_updates or [],
        )

        await self.reflection_repo.store(
            memory_type=MemoryType.REFLECTION,
            content={
                "prediction_id": str(prediction_id),
                "ipo_symbol": ipo_symbol,
                "prediction_type": prediction_type.value,
                "predicted_value": predicted_value,
                "actual_value": actual_value,
                "accuracy": accuracy,
                "error": abs(predicted_value - actual_value),
                "mistakes_identified": mistakes_identified or [],
                "correct_assumptions": correct_assumptions or [],
                "missing_factors": missing_factors or [],
                "lessons_extracted": lessons_extracted or [],
                "prompt_improvements": prompt_improvements or [],
                "strategy_changes": strategy_changes or [],
                "knowledge_updates": knowledge_updates or [],
            },
        )

        return reflection


class GetReflectionsUseCase:
    """Use case for getting reflections."""

    def __init__(self, reflection_repo: ReflectionMemoryRepository):
        self.reflection_repo = reflection_repo

    async def get_by_prediction(
        self,
        prediction_id: UUID,
    ) -> Optional[ReflectionMemory]:
        """Get reflection by prediction ID."""
        return await self.reflection_repo.get_by_prediction(prediction_id)

    async def get_by_ipo(
        self,
        ipo_symbol: str,
        limit: int = 20,
    ) -> List[ReflectionMemory]:
        """Get reflections for IPO."""
        return await self.reflection_repo.get_by_ipo(ipo_symbol, limit)

    async def get_unprocessed(self, limit: int = 50) -> List[ReflectionMemory]:
        """Get unprocessed reflections."""
        return await self.reflection_repo.get_unprocessed(limit)


class SaveLessonUseCase:
    """Use case for saving a lesson."""

    def __init__(self, lesson_repo: LessonRepository):
        self.lesson_repo = lesson_repo

    async def execute(
        self,
        lesson_type: LessonType,
        title: str,
        description: str,
        do: List[str] = None,
        dont: List[str] = None,
        best_practices: List[str] = None,
        anti_patterns: List[str] = None,
        known_bugs: List[str] = None,
        prompt_improvements: List[str] = None,
        confidence: float = 0.0,
        evidence: List[Dict[str, Any]] = None,
        applicable_agents: List[AgentName] = None,
        tags: List[str] = None,
    ) -> UUID:
        """Save lesson."""
        lesson = Lesson(
            lesson_type=lesson_type,
            title=title,
            description=description,
            do=do or [],
            dont=dont or [],
            best_practices=best_practices or [],
            anti_patterns=anti_patterns or [],
            known_bugs=known_bugs or [],
            prompt_improvements=prompt_improvements or [],
            confidence=confidence,
            evidence=evidence or [],
            applicable_agents=applicable_agents or [],
            tags=tags or [],
        )

        return await self.lesson_repo.save(lesson)


class GetLessonsUseCase:
    """Use case for getting lessons."""

    def __init__(self, lesson_repo: LessonRepository):
        self.lesson_repo = lesson_repo

    async def get_by_id(self, lesson_id: UUID) -> Optional[Lesson]:
        """Get lesson by ID."""
        return await self.lesson_repo.get_by_id(lesson_id)

    async def get_by_type(
        self,
        lesson_type: LessonType,
        limit: int = 50,
    ) -> List[Lesson]:
        """Get lessons by type."""
        return await self.lesson_repo.get_by_type(lesson_type, limit)

    async def get_applicable(
        self,
        agent_name: AgentName,
        context: Dict[str, Any],
        limit: int = 10,
    ) -> List[Lesson]:
        """Get applicable lessons for agent and context."""
        return await self.lesson_repo.get_applicable(agent_name, context, limit)

    async def search(self, query: str, limit: int = 20) -> List[Lesson]:
        """Search lessons by text."""
        return await self.lesson_repo.search(query, limit)