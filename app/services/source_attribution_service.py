class SourceAttributionService:

    MIN_CONFIDENCE = 0.45

    def build(
        self,
        results: list,
    ) -> str | None:

        if not results:
            return None

        top = results[0]

        ranking_score = (
            top.get(
                "ranking_score",
                0.0,
            )
        )

        # =====================================
        # LOW CONFIDENCE
        # =====================================

        if (
            ranking_score
            < self.MIN_CONFIDENCE
        ):
            return None

        source_type = (
            top.get(
                "source_type",
                "",
            )
        )

        # =====================================
        # FARMER EXPERIENCE
        # =====================================

        if (
            source_type
            == "farmer_experience"
        ):

            farmer_name = (
                top.get(
                    "farmer_name"
                )
            )

            district = (
                top.get(
                    "district"
                )
            )

            state = (
                top.get(
                    "state"
                )
            )

            # exact farmer attribution
            if (
                farmer_name
                and district
            ):

                return (
                    f"यह सुझाव किसान "
                    f"{farmer_name} "
                    f"({district}) "
                    f"द्वारा साझा अनुभव "
                    f"पर आधारित है।"
                )

            # state attribution
            if state:

                return (
                    f"यह सुझाव "
                    f"{state} के किसानों "
                    f"के साझा अनुभवों "
                    f"पर आधारित है।"
                )

            # generic farmer attribution
            return (
                "यह सुझाव किसानों "
                "के साझा अनुभवों "
                "पर आधारित है।"
            )

        # =====================================
        # EXPERT KB
        # =====================================

        elif (
            source_type
            == "expert_kb"
        ):

            return (
                "यह जानकारी कृषि "
                "विशेषज्ञ सामग्री "
                "पर आधारित है।"
            )

        # =====================================
        # GOVERNMENT
        # =====================================

        elif (
            source_type
            == "government"
        ):

            return (
                "यह जानकारी सरकारी "
                "कृषि मार्गदर्शन "
                "से ली गई है।"
            )

        # =====================================
        # MIXED
        # =====================================

        elif (
            source_type
            == "mixed"
        ):

            return (
                "यह उत्तर कृषि विशेषज्ञ "
                "जानकारी और किसानों "
                "के साझा अनुभवों "
                "पर आधारित है।"
            )

        return None


source_attribution_service = (
    SourceAttributionService()
)