# File: app/services/diagnostic_service.py


class DiagnosticService:

    # =====================================
    # BUILD CONVERSATIONAL PLAN
    # =====================================

    def decide_response_mode(
        self,
        *,
        query: str,
        analysis: dict,
        memory: list | None = None,
    ) -> dict:

        crop = (
            analysis.get(
                "crop"
            )
            or ""
        )

        symptom = (
            analysis.get(
                "symptom"
            )
            or ""
        )

        category = (
            analysis.get(
                "category"
            )
            or ""
        )

        farmer_name = (
            analysis.get(
                "farmer_name"
            )
            or ""
        )

        intent = (
            analysis.get(
                "intent"
            )
            or ""
        )

        is_ambiguous = (
            analysis.get(
                "is_ambiguous",
                True,
            )
        )

        query_lower = (
            query.lower()
        )

        query_length = len(
            query.split()
        )

        # =================================
        # VERY SHORT QUERY
        # =================================

        if query_length <= 2:

            return {

                "mode": (
                    "clarification"
                ),

                "reason": (
                    "very_short_query"
                ),

                "priority": (
                    "high"
                ),
            }

        # =================================
        # FARMER INFORMATION QUERY
        # =================================

        farmer_keywords = [

            "बताओ",
            "बताया",
            "सलाह",
            "कौन",
            "कहाँ",
            "belong",
            "जानकारी",
            "खेती करते हैं",
            "क्या कहा",
            "क्या बताया",
        ]

        if (
            farmer_name
            and any(
                keyword in query_lower
                for keyword in farmer_keywords
            )
        ):

            return {

                "mode": (
                    "answer"
                ),

                "reason": (
                    "farmer_information_query"
                ),

                "priority": (
                    "high"
                ),
            }

        # =================================
        # INFORMATION QUERY
        # =================================

        info_keywords = [

            "कैसे करें",
            "जानकारी",
            "उपाय",
            "सलाह",
            "तकनीक",
            "फायदा",
            "महत्व",
        ]

        if any(
            keyword in query_lower
            for keyword in info_keywords
        ):

            return {

                "mode": (
                    "answer"
                ),

                "reason": (
                    "information_query"
                ),

                "priority": (
                    "normal"
                ),
            }

        # =================================
        # NO CROP
        # =================================

        if not crop:

            return {

                "mode": (
                    "clarification"
                ),

                "reason": (
                    "missing_crop"
                ),

                "priority": (
                    "high"
                ),
            }

        # =================================
        # SYMPTOM REQUIRED ONLY
        # FOR DISEASE/PROBLEM QUERIES
        # =================================

        problem_keywords = [

            "समस्या",
            "रोग",
            "कीड़ा",
            "कीट",
            "सूख",
            "पीला",
            "दाग",
            "इलाज",
            "control",
            "disease",
            "problem",
        ]

        is_problem_query = any(
            keyword in query_lower
            for keyword in problem_keywords
        )

        if (
            is_problem_query
            and not symptom
        ):

            return {

                "mode": (
                    "clarification"
                ),

                "reason": (
                    "missing_symptom"
                ),

                "priority": (
                    "medium"
                ),
            }

        # =================================
        # AMBIGUOUS QUERY
        # =================================

        if is_ambiguous:

            return {

                "mode": (
                    "explore"
                ),

                "reason": (
                    "ambiguous_problem"
                ),

                "priority": (
                    "medium"
                ),
            }

        # =================================
        # CATEGORY-BASED ADAPTATION
        # =================================

        if category in [

            "कीट",
            "रोग",
            "कीट नियंत्रण",
            "रोग नियंत्रण",
        ]:

            return {

                "mode": (
                    "diagnostic"
                ),

                "reason": (
                    "crop_issue"
                ),

                "priority": (
                    "high"
                ),
            }

        # =================================
        # DEFAULT ANSWER
        # =================================

        return {

            "mode": (
                "answer"
            ),

            "reason": (
                "sufficient_context"
            ),

            "priority": (
                "normal"
            ),
        }


diagnostic_service = (
    DiagnosticService()
)