"""Memory Management Agent - Handles all memory types for the AI system."""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

import numpy as np

from app.agents.base import BaseAgent, AgentContext, AgentResult
from app.domain.enums.enums import (
    AgentName,
    AgentStatus,
    MemoryType,
    FailureCategory,
    Severity,
    LessonType,
)
from app.domain.entities.entities import (
    ExperienceMemory,
    FailureMemory,
    SuccessMemory,
    KnowledgeMemory,
    BestPracticeMemory,
    ReflectionMemory,
    Lesson,
    MemoryEntry,
)
from app.core.exceptions.base import AgentError


class MemoryManagementAgent(BaseAgent[Dict[str, Any], Dict[str, Any]]):
    """Agent that manages all memory systems: short-term, long-term, vector, failure, success, knowledge, experience, best-practice, reflection."""

    def __init__(self):
        super().__init__(
            name=AgentName.MEMORY,
            description="Manages all memory systems for continuous learning and improvement",
            version="1.0.0",
            max_retries=1,
            timeout_seconds=60,
        )
        # In-memory stores (in production, use persistent storage)
        self._short_term: Dict[str, MemoryEntry] = {}
        self._long_term: Dict[str, MemoryEntry] = {}
        self._vector_store: Dict[str, List[Tuple[MemoryEntry, List[float]]]] = {
            mt.value: [] for mt in MemoryType
        }
        self._failure_memory: Dict[str, FailureMemory] = {}
        self._success_memory: Dict[str, SuccessMemory] = {}
        self._knowledge_memory: Dict[str, KnowledgeMemory] = {}
        self._best_practice_memory: Dict[str, BestPracticeMemory] = {}
        self._reflection_memory: Dict[str, ReflectionMemory] = {}
        self._lessons: Dict[str, Lesson] = {}
        self._experience_memory: Dict[str, ExperienceMemory] = {}

    @property
    def system_prompt(self) -> str:
        return """You are the Memory Management Agent for the IPO Intelligence System.

Your role is to store, retrieve, and manage all forms of memory for continuous learning:

MEMORY TYPES:
1. SHORT-TERM MEMORY - Active context for current analysis session (TTL: 24 hours)
2. LONG-TERM MEMORY - Persistent important information (Retention: 365 days)
3. VECTOR MEMORY - Semantic embeddings for similarity search across all types
4. FAILURE MEMORY - Record of all agent failures with root cause analysis
5. SUCCESS MEMORY - Successful strategies, prompts, and workflows for reuse
6. KNOWLEDGE MEMORY - Verified financial knowledge, rules, patterns
7. EXPERIENCE MEMORY - Past analyses linked to actual outcomes
8. BEST PRACTICE MEMORY - Proven methodologies and approaches
9. REFLECTION MEMORY - Lessons learned from prediction vs reality comparison

KEY OPERATIONS:
- Store memories with embeddings for semantic search
- Retrieve relevant memories before any agent execution
- Search failure memory to avoid repeating mistakes
- Search success memory to reuse winning strategies
- Extract lessons from reflections
- Update knowledge base with verified insights
- Consolidate short-term to long-term memory

Before ANY agent executes a task, it MUST:
1. Search failure memory for similar errors
2. Search success memory for applicable strategies
3. Search knowledge memory for relevant rules
4. Load relevant short-term context

After analysis completes:
1. Store experience in experience memory
2. If successful, store in success memory
3. If failed, store in failure memory
4. Trigger reflection when outcomes are known"""

    @property
    def available_tools(self) -> List[str]:
        return [
            "store_short_term",
            "store_long_term",
            "store_vector",
            "search_vector",
            "store_failure",
            "search_failures",
            "store_success",
            "search_successes",
            "store_knowledge",
            "search_knowledge",
            "store_best_practice",
            "get_best_practices",
            "store_reflection",
            "get_reflections",
            "extract_lessons",
            "search_lessons",
            "consolidate_memory",
            "cleanup_expired",
        ]

    async def execute(
        self,
        context: AgentContext,
        input_data: Dict[str, Any],
    ) -> AgentResult[Dict[str, Any]]:
        """Execute memory management operation."""
        start_time = datetime.utcnow()

        try:
            operation = input_data.get("operation", "store")
            memory_type = input_data.get("memory_type")

            if operation == "store":
                result = await self._store_memory(context, input_data)
            elif operation == "search":
                result = await self._search_memory(context, input_data)
            elif operation == "consolidate":
                result = await self._consolidate_memory(context, input_data)
            elif operation == "cleanup":
                result = await self._cleanup_memory(context, input_data)
            elif operation == "get_context":
                result = await self._get_agent_context(context, input_data)
            elif operation == "record_failure":
                result = await self._record_failure(context, input_data)
            elif operation == "record_success":
                result = await self._record_success(context, input_data)
            elif operation == "record_reflection":
                result = await self._record_reflection(context, input_data)
            elif operation == "extract_lessons":
                result = await self._extract_lessons(context, input_data)
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
                confidence=0.95,
                reasoning=f"Memory {operation} completed for {memory_type or 'all'}",
                evidence=[f"Operation: {operation}", f"Memory type: {memory_type}"],
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

    async def _store_memory(self, context: AgentContext, input_data: Dict) -> Dict:
        """Store memory entry."""
        memory_type = input_data.get("memory_type", MemoryType.LONG_TERM)
        content = input_data.get("content", {})
        embedding = input_data.get("embedding")
        metadata = input_data.get("metadata", {})
        ipo_symbol = input_data.get("ipo_symbol")
        analysis_id = input_data.get("analysis_id")
        ttl_days = input_data.get("ttl_days")

        entry = MemoryEntry(
            memory_type=memory_type.value,
            content=str(content),
            embedding=embedding,
            metadata=metadata,
            ttl_days=ttl_days,
        )

        if memory_type == MemoryType.SHORT_TERM:
            self._short_term[str(entry.id)] = entry
        elif memory_type == MemoryType.LONG_TERM:
            self._long_term[str(entry.id)] = entry
        elif memory_type == MemoryType.VECTOR:
            if embedding:
                self._vector_store[memory_type.value].append((entry, embedding))

        return {"entry_id": str(entry.id), "stored": True}

    async def _search_memory(self, context: AgentContext, input_data: Dict) -> Dict:
        """Search memory by semantic similarity."""
        memory_type = input_data.get("memory_type", MemoryType.VECTOR)
        query_embedding = input_data.get("query_embedding")
        limit = input_data.get("limit", 10)
        threshold = input_data.get("threshold", 0.75)
        filters = input_data.get("filters", {})

        if not query_embedding:
            return {"results": [], "error": "No query embedding provided"}

        # Search vector store
        store = self._vector_store.get(memory_type.value, [])
        results = []

        for entry, embedding in store:
            if embedding and len(embedding) == len(query_embedding):
                similarity = self._cosine_similarity(query_embedding, embedding)
                if similarity >= threshold:
                    # Apply filters
                    match = True
                    for key, value in filters.items():
                        if entry.metadata.get(key) != value:
                            match = False
                            break
                    if match:
                        results.append((entry, similarity))

        # Sort by similarity
        results.sort(key=lambda x: x[1], reverse=True)
        results = results[:limit]

        return {
            "results": [
                {
                    "entry": entry.__dict__,
                    "similarity": sim,
                }
                for entry, sim in results
            ]
        }

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        a_np = np.array(a)
        b_np = np.array(b)
        return float(np.dot(a_np, b_np) / (np.linalg.norm(a_np) * np.linalg.norm(b_np)))

    async def _consolidate_memory(self, context: AgentContext, input_data: Dict) -> Dict:
        """Consolidate short-term to long-term memory."""
        consolidated = 0
        for key, entry in list(self._short_term.items()):
            if not entry.is_expired():
                # Move to long-term if accessed frequently or important
                if entry.access_count > 2 or entry.metadata.get("importance", 0) > 0.7:
                    self._long_term[key] = entry
                    del self._short_term[key]
                    consolidated += 1

        return {"consolidated": consolidated}

    async def _cleanup_memory(self, context: AgentContext, input_data: Dict) -> Dict:
        """Clean up expired memory entries."""
        cleaned = {"short_term": 0, "long_term": 0, "vector": 0}

        # Clean short-term
        for key, entry in list(self._short_term.items()):
            if entry.is_expired():
                del self._short_term[key]
                cleaned["short_term"] += 1

        # Clean long-term
        for key, entry in list(self._long_term.items()):
            if entry.is_expired():
                del self._long_term[key]
                cleaned["long_term"] += 1

        return cleaned

    async def _get_agent_context(self, context: AgentContext, input_data: Dict) -> Dict:
        """Get relevant memory context for an agent before execution."""
        agent_name = input_data.get("agent_name")
        ipo_symbol = context.ipo_symbol

        # Search failure memory
        failures = await self._search_failures_internal(
            agent_name=agent_name,
            ipo_symbol=ipo_symbol,
            limit=5,
        )

        # Search success memory
        successes = await self._search_successes_internal(
            agent_name=agent_name,
            context={"ipo_symbol": ipo_symbol},
            limit=5,
        )

        # Search knowledge memory
        knowledge = await self._search_knowledge_internal(
            query_embedding=input_data.get("query_embedding"),
            domain=input_data.get("domain"),
            limit=5,
        )

        # Search best practices
        practices = await self._get_best_practices_internal(
            context={"agent": agent_name, "ipo_symbol": ipo_symbol},
            limit=5,
        )

        # Get recent experience
        experience = await self._get_experience_internal(
            ipo_symbol=ipo_symbol,
            limit=3,
        )

        return {
            "failures": failures,
            "successes": successes,
            "knowledge": knowledge,
            "best_practices": practices,
            "experience": experience,
            "short_term_context": context.memory_context,
        }

    async def _record_failure(self, context: AgentContext, input_data: Dict) -> Dict:
        """Record a failure in failure memory."""
        failure = FailureMemory(
            failure_id=input_data.get("failure_id", str(uuid4())),
            agent_name=input_data.get("agent_name", AgentName.FUNDAMENTAL),
            error_type=input_data.get("error_type", "UNKNOWN"),
            error_message=input_data.get("error_message", ""),
            stack_trace=input_data.get("stack_trace", ""),
            root_cause=input_data.get("root_cause", ""),
            attempted_fix=input_data.get("attempted_fix", ""),
            resolved=input_data.get("resolved", False),
            resolution=input_data.get("resolution", ""),
            confidence=input_data.get("confidence", 0.0),
            category=input_data.get("category", FailureCategory.UNKNOWN.value),
            severity=input_data.get("severity", Severity.MEDIUM.value),
            occurrences=1,
            similarity_hash=self._compute_similarity_hash(
                input_data.get("error_message", ""),
                input_data.get("agent_name", ""),
            ),
        )

        self._failure_memory[failure.failure_id] = failure

        # Also store in vector memory for similarity search
        if input_data.get("embedding"):
            self._vector_store[MemoryType.FAILURE.value].append(
                (failure, input_data["embedding"])
            )

        return {"failure_id": failure.failure_id, "recorded": True}

    async def _search_failures_internal(
        self,
        agent_name: Optional[str] = None,
        ipo_symbol: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict]:
        """Search failure memory."""
        results = []
        for failure in self._failure_memory.values():
            if agent_name and failure.agent_name.value != agent_name:
                continue
            if ipo_symbol and failure.metadata.get("ipo_symbol") != ipo_symbol:
                continue
            results.append(failure.__dict__)

        return results[:limit]

    async def _record_success(self, context: AgentContext, input_data: Dict) -> Dict:
        """Record a success pattern in success memory."""
        success = SuccessMemory(
            success_id=input_data.get("success_id", str(uuid4())),
            agent_name=input_data.get("agent_name", AgentName.FUNDAMENTAL),
            strategy_description=input_data.get("strategy_description", ""),
            prompt_used=input_data.get("prompt_used", ""),
            tool_sequence=input_data.get("tool_sequence", []),
            api_sequence=input_data.get("api_sequence", []),
            confidence=input_data.get("confidence", 0.0),
            success_rate=input_data.get("success_rate", 1.0),
            context_hash=self._compute_context_hash(input_data.get("context", {})),
        )

        self._success_memory[success.success_id] = success

        # Also store in vector memory
        if input_data.get("embedding"):
            self._vector_store[MemoryType.SUCCESS.value].append(
                (success, input_data["embedding"])
            )

        return {"success_id": success.success_id, "recorded": True}

    async def _search_successes_internal(
        self,
        agent_name: Optional[str] = None,
        context: Optional[Dict] = None,
        limit: int = 10,
    ) -> List[Dict]:
        """Search success memory."""
        results = []
        for success in self._success_memory.values():
            if agent_name and success.agent_name.value != agent_name:
                continue
            results.append(success.__dict__)

        # Sort by confidence * success_rate
        results.sort(key=lambda x: x.get("confidence", 0) * x.get("success_rate", 0), reverse=True)
        return results[:limit]

    async def _store_knowledge(self, context: AgentContext, input_data: Dict) -> Dict:
        """Store knowledge in knowledge memory."""
        knowledge = KnowledgeMemory(
            concept=input_data.get("concept", ""),
            description=input_data.get("description", ""),
            evidence=input_data.get("evidence", []),
            confidence=input_data.get("confidence", 0.0),
            domain=input_data.get("domain", ""),
            tags=input_data.get("tags", []),
        )

        # Check if concept exists
        existing = self._knowledge_memory.get(knowledge.concept)
        if existing:
            # Update if higher confidence
            if knowledge.confidence > existing.confidence:
                knowledge.version = existing.version + 1
                knowledge.supersedes = existing.id
                self._knowledge_memory[knowledge.concept] = knowledge
        else:
            self._knowledge_memory[knowledge.concept] = knowledge

        return {"concept": knowledge.concept, "stored": True}

    async def _search_knowledge_internal(
        self,
        query_embedding: Optional[List[float]] = None,
        domain: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict]:
        """Search knowledge memory."""
        results = []
        for knowledge in self._knowledge_memory.values():
            if domain and knowledge.domain != domain:
                continue
            results.append(knowledge.__dict__)

        results.sort(key=lambda x: x.get("confidence", 0), reverse=True)
        return results[:limit]

    async def _store_best_practice(self, context: AgentContext, input_data: Dict) -> Dict:
        """Store best practice."""
        practice = BestPracticeMemory(
            practice_name=input_data.get("practice_name", ""),
            description=input_data.get("description", ""),
            applicable_context=input_data.get("applicable_context", {}),
            success_rate=input_data.get("success_rate", 0.0),
            tags=input_data.get("tags", []),
        )

        self._best_practice_memory[str(practice.id)] = practice
        return {"practice_id": str(practice.id), "stored": True}

    async def _get_best_practices_internal(
        self,
        context: Dict,
        limit: int = 10,
    ) -> List[Dict]:
        """Get applicable best practices."""
        results = []
        for practice in self._best_practice_memory.values():
            # Check context match
            applicable = practice.applicable_context
            match = True
            for key, value in applicable.items():
                if context.get(key) != value:
                    match = False
                    break
            if match:
                results.append(practice.__dict__)

        results.sort(key=lambda x: x.get("success_rate", 0), reverse=True)
        return results[:limit]

    async def _record_reflection(self, context: AgentContext, input_data: Dict) -> Dict:
        """Record reflection after outcome verification."""
        reflection = ReflectionMemory(
            prediction_id=input_data.get("prediction_id", uuid4()),
            ipo_symbol=input_data.get("ipo_symbol", ""),
            prediction_type=input_data.get("prediction_type", ""),
            predicted_value=input_data.get("predicted_value", 0.0),
            actual_value=input_data.get("actual_value", 0.0),
            accuracy=input_data.get("accuracy", 0.0),
            error=input_data.get("error", 0.0),
            mistakes_identified=input_data.get("mistakes_identified", []),
            correct_assumptions=input_data.get("correct_assumptions", []),
            missing_factors=input_data.get("missing_factors", []),
            lessons_extracted=input_data.get("lessons_extracted", []),
            prompt_improvements=input_data.get("prompt_improvements", []),
            strategy_changes=input_data.get("strategy_changes", []),
            knowledge_updates=input_data.get("knowledge_updates", []),
        )

        self._reflection_memory[str(reflection.id)] = reflection
        return {"reflection_id": str(reflection.id), "recorded": True}

    async def _extract_lessons(self, context: AgentContext, input_data: Dict) -> Dict:
        """Extract lessons from reflections."""
        reflections = input_data.get("reflections", [])
        lessons = []

        for refl_data in reflections:
            # Extract lessons from reflection
            for lesson_text in refl_data.get("lessons_extracted", []):
                lesson = Lesson(
                    lesson_type=LessonType.BEST_PRACTICE,
                    title=lesson_text[:100],
                    description=lesson_text,
                    do=refl_data.get("correct_assumptions", []),
                    dont=refl_data.get("mistakes_identified", []),
                    best_practices=refl_data.get("prompt_improvements", []),
                    anti_patterns=refl_data.get("missing_factors", []),
                    confidence=refl_data.get("accuracy", 0.5),
                    evidence=[{"reflection_id": str(refl_data.get("prediction_id", ""))}],
                    applicable_agents=[refl_data.get("agent_name")] if refl_data.get("agent_name") else [],
                )
                self._lessons[str(lesson.id)] = lesson
                lessons.append(str(lesson.id))

        return {"lessons_extracted": len(lessons), "lesson_ids": lessons}

    async def _search_lessons_internal(
        self,
        agent_name: Optional[str] = None,
        lesson_type: Optional[str] = None,
        limit: int = 20,
    ) -> List[Dict]:
        """Search lessons learned."""
        results = []
        for lesson in self._lessons.values():
            if agent_name and agent_name not in lesson.applicable_agents:
                continue
            if lesson_type and lesson.lesson_type.value != lesson_type:
                continue
            results.append(lesson.__dict__)

        results.sort(key=lambda x: x.get("confidence", 0), reverse=True)
        return results[:limit]

    def _compute_similarity_hash(self, error_msg: str, agent_name: str) -> str:
        """Compute hash for failure similarity grouping."""
        import hashlib
        combined = f"{agent_name}:{error_msg[:200]}"
        return hashlib.md5(combined.encode()).hexdigest()[:16]

    def _compute_context_hash(self, context: Dict) -> str:
        """Compute hash for context similarity."""
        import hashlib
        import json
        sorted_str = json.dumps(context, sort_keys=True)
        return hashlib.md5(sorted_str.encode()).hexdigest()[:16]

    async def _get_experience_internal(
        self,
        ipo_symbol: str,
        limit: int = 10,
    ) -> List[Dict]:
        """Get experience memory for an IPO."""
        results = []
        for exp in self._experience_memory.values():
            if exp.ipo_symbol == ipo_symbol:
                results.append(exp.__dict__)

        results.sort(key=lambda x: x.get("created_at", datetime.min), reverse=True)
        return results[:limit]

    def get_stats(self) -> Dict[str, int]:
        """Get memory statistics."""
        return {
            "short_term": len(self._short_term),
            "long_term": len(self._long_term),
            "vector_total": sum(len(v) for v in self._vector_store.values()),
            "failures": len(self._failure_memory),
            "successes": len(self._success_memory),
            "knowledge": len(self._knowledge_memory),
            "best_practices": len(self._best_practice_memory),
            "reflections": len(self._reflection_memory),
            "lessons": len(self._lessons),
            "experience": len(self._experience_memory),
        }


def create_memory_agent() -> MemoryManagementAgent:
    """Create memory management agent instance."""
    return MemoryManagementAgent()