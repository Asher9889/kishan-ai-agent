# from typing import Any

# from app.ai.llm import llm_service
# from app.core.logger import logger


# class AnswerGenerator:
#     def generate(
#         self,
#         query: str,
#         results: list[dict[str, Any]],
#     ) -> dict[str, Any]:
#         """
#         Generate grounded answer
#         using multiple retrieved contexts.
#         """

#         contexts: list[str] = []

#         sources: list[
#             dict[str, Any]
#         ] = []

#         scores: list[float] = []

#         for item in results:
#             document = item.get(
#                 "document",
#                 "",
#             )

#             metadata = (
#                 item.get(
#                     "metadata",
#                     {},
#                 )
#                 or {}
#             )

#             ranking_score = float(
#                 item.get(
#                     "ranking_score",
#                     0.0,
#                 )
#             )

#             if document:
#                 contexts.append(
#                     document
#                 )

#             # Source-wise finding
#             finding = (
#                 metadata.get(
#                     "solution"
#                 )
#                 or metadata.get(
#                     "summary"
#                 )
#                 or document
#             )

#             sources.append(
#                 {
#                     "farmer_name": metadata.get(
#                         "farmer_name"
#                     ),
#                     "district": metadata.get(
#                         "district"
#                     ),
#                     "state": metadata.get(
#                         "state"
#                     ),
#                     "category": metadata.get(
#                         "category"
#                     ),
#                     "crop": metadata.get(
#                         "crop"
#                     ),
#                     "finding": finding,
#                 }
#             )

#             scores.append(
#                 ranking_score
#             )

#         combined_context = (
#             "\n\n".join(contexts)
#         )

#         prompt = f"""
# You are Krishi-Anubhav, an agricultural AI Assistant.

# Answer the farmer's question using ALL provided contexts.

# Rules:
# - Use ONLY the provided contexts.
# - Combine similar information intelligently.
# - If multiple valid solutions exist, include them.
# - Avoid repeating the same point.
# - Write in simple Hindi.
# - Keep the answer concise and practical.
# - If context is insufficient, say that sufficient information is not available.
# - Return ONLY the final Hindi answer.

# Farmer Question:
# {query}

# Contexts:
# {combined_context}
# """

#         answer = (
#             llm_service.generate(
#                 prompt=prompt,
#                 temperature=0.1,
#                 max_tokens=400,
#             )
#         )

#         # Average confidence
#         confidence = round(
#             (
#                 sum(scores)
#                 / len(scores)
#             )
#             if scores
#             else 0.0,
#             4,
#         )

#         logger.info(
#             (
#                 "Multi-context grounded "
#                 "answer generated"
#             ),
#             confidence=confidence,
#             contexts_used=len(
#                 contexts
#             ),
#         )

#         return {
#             "answer": answer.strip(),
#             "confidence": confidence,
#             "sources": (
#                 sources
#             ),
#             "contexts_used": len(
#                 contexts
#             ),
#         }


# answer_generator = (
#     AnswerGenerator()
# )

# from typing import Any

# from app.ai.llm import (
#     llm_service,
# )
# from app.core.logger import (
#     logger,
# )


# class AnswerGenerator:

#     def generate(
#         self,
#         *,
#         prompt: str,
#         results: list[
#             dict[str, Any]
#         ],
#     ) -> dict[str, Any]:
#         """
#         Generate conversational grounded answer
#         using:
#         - prompt builder
#         - memory
#         - RAG contexts
#         """

#         sources: list[
#             dict[str, Any]
#         ] = []

#         scores: list[float] = []

#         contexts_used = 0

#         for item in results:

#             document = item.get(
#                 "document",
#                 "",
#             )

#             metadata = (
#                 item.get(
#                     "metadata",
#                     {},
#                 )
#                 or {}
#             )

#             ranking_score = float(
#                 item.get(
#                     "ranking_score",
#                     0.0,
#                 )
#             )

#             if document:
#                 contexts_used += 1

#             # Source-wise findings
#             finding = (
#                 metadata.get(
#                     "solution"
#                 )
#                 or metadata.get(
#                     "summary"
#                 )
#                 or document
#             )

#             sources.append(
#                 {
#                     "farmer_name": metadata.get(
#                         "farmer_name"
#                     ),
#                     "district": metadata.get(
#                         "district"
#                     ),
#                     "state": metadata.get(
#                         "state"
#                     ),
#                     "category": metadata.get(
#                         "category"
#                     ),
#                     "crop": metadata.get(
#                         "crop"
#                     ),
#                     "finding": finding,
#                 }
#             )

#             scores.append(
#                 ranking_score
#             )

#         # =====================================
#         # Final Conversational RAG Generation
#         # =====================================

#         answer = (
#             llm_service.generate(
#                 prompt=prompt,
#                 temperature=0.1,
#                 max_tokens=400,
#             )
#         )

#         # =====================================
#         # Confidence Calculation
#         # =====================================

#         confidence = round(
#             (
#                 sum(scores)
#                 / len(scores)
#             )
#             if scores
#             else 0.0,
#             4,
#         )

#         logger.info(
#             (
#                 "Conversational grounded "
#                 "answer generated"
#             ),
#             confidence=confidence,
#             contexts_used=(
#                 contexts_used
#             ),
#             sources_count=len(
#                 sources
#             ),
#         )

#         return {
#             "answer": answer.strip(),
#             "confidence": confidence,
#             "sources": (
#                 sources
#             ),
#             "contexts_used": (
#                 contexts_used
#             ),
#         }


# answer_generator = (
#     AnswerGenerator()
# )

# ======================================

# from typing import Any

# from app.ai.llm import (
#     llm_service,
# )

# from app.core.logger import (
#     logger,
# )


# class AnswerGenerator:

#     def generate(
#         self,
#         *,
#         prompt: str,
#         results: list[
#             dict[str, Any]
#         ],
#     ) -> dict[str, Any]:
#         """
#         Generate grounded conversational
#         agricultural answer using:

#         - conversational memory
#         - metadata-aware RAG
#         - grounded agricultural knowledge
#         - expert-level explanation
#         """

#         sources: list[
#             dict[str, Any]
#         ] = []

#         scores: list[float] = []

#         contexts_used = 0

#         knowledge_points: list[
#             str
#         ] = []

#         # =====================================
#         # Process Retrieved Results
#         # =====================================

#         for item in results:

#             document = item.get(
#                 "document",
#                 "",
#             )

#             metadata = (
#                 item.get(
#                     "metadata",
#                     {},
#                 )
#                 or {}
#             )

#             ranking_score = float(
#                 item.get(
#                     "ranking_score",
#                     0.0,
#                 )
#             )

#             # =====================================
#             # Context tracking
#             # =====================================

#             if document:

#                 contexts_used += 1

#                 knowledge_points.append(
#                     document
#                 )

#             # =====================================
#             # Source-wise finding
#             # =====================================

#             finding = (
#                 metadata.get(
#                     "solution"
#                 )
#                 or metadata.get(
#                     "summary"
#                 )
#                 or document
#             )

#             sources.append(
#                 {
#                     "farmer_name": metadata.get(
#                         "farmer_name"
#                     ),
#                     "district": metadata.get(
#                         "district"
#                     ),
#                     "state": metadata.get(
#                         "state"
#                     ),
#                     "category": metadata.get(
#                         "category"
#                     ),
#                     "crop": metadata.get(
#                         "crop"
#                     ),
#                     "finding": finding,
#                 }
#             )

#             scores.append(
#                 ranking_score
#             )

#         # =====================================
#         # Enhanced Grounded Expert Prompt
#         # =====================================

#         grounded_knowledge = (
#             "\n\n".join(
#                 knowledge_points
#             )
#         )

#         enhanced_prompt = f"""
# You are Krishi-Anubhav,
# an expert agricultural AI assistant.

# Your role:
# - Help farmers using retrieved agricultural knowledge.
# - Use retrieved knowledge as FACTUAL grounding.
# - Explain answers naturally like an experienced agriculture expert.
# - Make answers practical and easy to understand.
# - Give reasoning and benefits wherever useful.
# - Do NOT sound robotic.
# - Do NOT simply repeat dataset lines.
# - Never invent facts outside the retrieved knowledge.
# - If multiple relevant solutions exist, combine them intelligently.
# - Write in clear, farmer-friendly Hindi.

# IMPORTANT:
# - Retrieved knowledge is the PRIMARY truth source.
# - Conversation memory is ONLY for continuity.
# - Keep answers grounded in retrieved agricultural contexts.

# Retrieved Agricultural Knowledge:
# {grounded_knowledge}

# {prompt}

# Provide:
# 1. Direct practical answer
# 2. Why this solution helps
# 3. Practical farming guidance if possible

# Return ONLY final Hindi answer.
# """

#         # =====================================
#         # Final LLM Generation
#         # =====================================

#         answer = (
#             llm_service.generate(
#                 prompt=enhanced_prompt,
#                 temperature=0.2,
#                 max_tokens=500,
#             )
#         )

#         # =====================================
#         # Confidence Calculation
#         # =====================================

#         confidence = round(
#             (
#                 sum(scores)
#                 / len(scores)
#             )
#             if scores
#             else 0.0,
#             4,
#         )

#         # =====================================
#         # Logging
#         # =====================================

#         logger.info(
#             (
#                 "Grounded expert "
#                 "agricultural answer generated"
#             ),
#             confidence=confidence,
#             contexts_used=(
#                 contexts_used
#             ),
#             sources_count=len(
#                 sources
#             ),
#         )

#         # =====================================
#         # Final Response
#         # =====================================

#         return {
#             "answer": answer.strip(),
#             "confidence": confidence,
#             "sources": (
#                 sources
#             ),
#             "contexts_used": (
#                 contexts_used
#             ),
#         }


# answer_generator = (
#     AnswerGenerator()
# )


# ====================================================================

from typing import Any
from typing import Generator

from app.ai.llm import (
    llm_service,
)

from app.core.logger import (
    logger,
)


class AnswerGenerator:

    # =====================================
    # NORMAL GENERATION
    # =====================================

    def generate(
        self,
        *,
        prompt: str,
        results: list[
            dict[str, Any]
        ],
    ) -> dict[str, Any]:

        sources: list[
            dict[str, Any]
        ] = []

        scores: list[float] = []

        contexts_used = 0

        knowledge_points: list[
            str
        ] = []

        # =====================================
        # Process Retrieved Results
        # =====================================

        for item in results:

            document = item.get(
                "document",
                "",
            )

            metadata = (
                item.get(
                    "metadata",
                    {},
                )
                or {}
            )

            ranking_score = float(
                item.get(
                    "ranking_score",
                    0.0,
                )
            )

            if document:

                contexts_used += 1

                knowledge_points.append(
                    document
                )

            finding = (
                metadata.get(
                    "solution"
                )
                or metadata.get(
                    "summary"
                )
                or document
            )

            sources.append(
                {
                    "farmer_name": metadata.get(
                        "farmer_name"
                    ),
                    "district": metadata.get(
                        "district"
                    ),
                    "state": metadata.get(
                        "state"
                    ),
                    "category": metadata.get(
                        "category"
                    ),
                    "crop": metadata.get(
                        "crop"
                    ),
                    "finding": finding,
                }
            )

            scores.append(
                ranking_score
            )

        # =====================================
        # Knowledge Availability
        # =====================================

        knowledge_found = (
            len(knowledge_points)
            > 0
        )

        # =====================================
        # Build Enhanced Prompt
        # =====================================

        enhanced_prompt = (
            self._build_prompt(
                prompt=prompt,
                knowledge_points=(
                    knowledge_points
                ),
                knowledge_found=(
                    knowledge_found
                ),
            )
        )

        # =====================================
        # Final Generation
        # =====================================

        answer = (
            llm_service.generate(
                prompt=enhanced_prompt,
                temperature=0.3,
                max_tokens=500,
            )
        )

        # =====================================
        # Confidence Score
        # =====================================

        confidence = round(
            (
                sum(scores)
                / len(scores)
            )
            if scores
            else 0.0,
            4,
        )

        # =====================================
        # Logging
        # =====================================

        logger.info(
            (
                "Grounded agricultural "
                "answer generated"
            ),
            confidence=confidence,
            contexts_used=(
                contexts_used
            ),
            sources_count=len(
                sources
            ),
            knowledge_found=(
                knowledge_found
            ),
        )

        # =====================================
        # Final Response
        # =====================================

        return {
            "answer": answer.strip(),
            "confidence": confidence,
            "sources": sources,
            "contexts_used": (
                contexts_used
            ),
            "knowledge_found": (
                knowledge_found
            ),
        }

    # =====================================
    # STREAMING GENERATION
    # =====================================

    def stream_generate(
        self,
        *,
        prompt: str,
        results: list[
            dict[str, Any]
        ],
    ) -> Generator[str, None, None]:

        knowledge_points: list[
            str
        ] = []

        for item in results:

            document = item.get(
                "document",
                "",
            )

            if document:

                knowledge_points.append(
                    document
                )

        knowledge_found = (
            len(knowledge_points)
            > 0
        )

        enhanced_prompt = (
            self._build_prompt(
                prompt=prompt,
                knowledge_points=(
                    knowledge_points
                ),
                knowledge_found=(
                    knowledge_found
                ),
            )
        )

        logger.info(
            (
                "Streaming answer "
                "generation started"
            ),
            knowledge_found=(
                knowledge_found
            ),
        )

        try:

            stream = (
                llm_service.stream_generate(
                    prompt=enhanced_prompt,
                    temperature=0.3,
                    max_tokens=500,
                )
            )

            for chunk in stream:

                if chunk:

                    yield chunk

        except Exception as exc:

            logger.exception(
                (
                    "Streaming generation failed"
                ),
                error=str(exc),
            )

            raise exc

    # =====================================
    # PROMPT BUILDER
    # =====================================

    def _build_prompt(
        self,
        *,
        prompt: str,
        knowledge_points: list[
            str
        ],
        knowledge_found: bool,
    ) -> str:

        grounded_knowledge = (
            "\n\n".join(
                knowledge_points
            )
        )

        return f"""
You are Krishi-Anubhav,
an expert agricultural AI assistant
specialized in Indian farming practices.

IMPORTANT SYSTEM RULES:

1. Retrieved agricultural knowledge
is the PRIMARY factual source.

2. If retrieved knowledge exists:
   - use it as factual truth
   - explain it naturally
   - make it conversational
   - sound like an experienced Krishi expert
   - NEVER invent unsupported facts

3. If retrieved knowledge is weak
or unavailable:
   - you MAY provide general
     agricultural guidance
   - but clearly mention:
     "यह सलाह AI कृषि विशेषज्ञ द्वारा दी गई है।
      यह वास्तविक संग्रहित कृषि ज्ञान पर आधारित नहीं है।"

4. Never hide whether answer came from:
   - factual retrieved knowledge
   OR
   - AI expert reasoning

5. Do NOT sound robotic.

6. Do NOT directly copy dataset text.

7. Use farmer-friendly Hindi.

8. Explain WHY the recommendation helps.

9. Mention quantity/dosage/timing
if available in knowledge.

10. Keep answers concise,
practical and conversational.

GOOD RESPONSE EXAMPLE:

Retrieved:
"जैविक खाद और गोबर की खाद उपयोगी है"

Good Answer:
"गन्ने की फसल में सड़ी हुई गोबर की खाद
और जैविक खाद का उपयोग लाभकारी होता है।
यह मिट्टी की उर्वरता बढ़ाने में मदद करता है
और फसल की बढ़वार बेहतर बनती है।"

BAD RESPONSE:
"डीएपी, यूरिया और पोटाश डालें"
(if not present in retrieved knowledge)

Knowledge Available:
{knowledge_found}

Retrieved Agricultural Knowledge:
{grounded_knowledge}

Conversation Context:
{prompt}

Now generate:
- grounded
- practical
- conversational
- expert-level
Hindi answer.

Return ONLY final Hindi answer.
"""

# =====================================
# Singleton Instance
# =====================================

answer_generator = (
    AnswerGenerator()
)
