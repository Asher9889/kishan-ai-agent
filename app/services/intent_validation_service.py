class IntentValidationService:

    """
    Soft intent-awareness service.

    This service DOES NOT block retrieval.
    It only provides intent signals
    to help the LLM understand whether
    retrieved knowledge matches the
    probable user intent.
    """

    def __init__(self):

        self.intent_keywords = {

            # =================================
            # CULTIVATION
            # =================================

            "cultivation": [

                "खेती",
                "खेती कैसे करें",
                "खेती करना",
                "फसल उगाना",
                "बुवाई",
                "रोपाई",
                "उत्पादन",
                "खेती की विधि",
                "खेती का तरीका",
                "कैसे उगाएं",
            ],

            # =================================
            # DISEASE
            # =================================

            "disease": [

                "रोग",
                "बीमारी",
                "धब्बा",
                "फफूंद",
                "कीट",
                "इलाज",
                "संक्रमण",
                "पत्ती पीली",
                "सड़न",
                "दवा",
            ],

            # =================================
            # FERTILIZER
            # =================================

            "fertilizer": [

                "खाद",
                "उर्वरक",
                "डीएपी",
                "यूरिया",
                "पोटाश",
                "गोबर",
                "जैविक खाद",
                "एनपीके",
            ],

            # =================================
            # IRRIGATION
            # =================================

            "irrigation": [

                "सिंचाई",
                "पानी",
                "ड्रिप",
                "स्प्रिंकलर",
                "पानी की कमी",
                "जल प्रबंधन",
            ],

            # =================================
            # PEST
            # =================================

            "pest": [

                "कीड़ा",
                "कीट",
                "मक्खी",
                "इल्ली",
                "पेस्ट",
            ],

            # =================================
            # STORAGE
            # =================================

            "storage": [

                "भंडारण",
                "स्टोरेज",
                "सड़न",
                "सुरक्षित रखना",
            ],
        }

    # =====================================
    # DETECT INTENT
    # =====================================

    def detect_intent(
        self,
        text: str,
    ) -> str:

        """
        Detect probable user intent.
        """

        if not text:

            return "general"

        text = text.lower()

        detected_intents = []

        # =================================
        # FIND MATCHES
        # =================================

        for (
            intent,
            keywords,
        ) in self.intent_keywords.items():

            for keyword in keywords:

                if keyword in text:

                    detected_intents.append(
                        intent
                    )

                    break

        # =================================
        # NO MATCH
        # =================================

        if not detected_intents:

            return "general"

        # =================================
        # PRIORITY ORDER
        # =================================

        priority_order = [

            "disease",
            "pest",
            "fertilizer",
            "irrigation",
            "cultivation",
            "storage",
        ]

        for priority in priority_order:

            if priority in detected_intents:

                return priority

        return detected_intents[0]

    # =====================================
    # VALIDATE
    # =====================================

    def validate(
        self,
        query: str,
        retrieved_text: str,
    ) -> dict:

        """
        Soft intent validation.

        Returns intent signals only.
        DOES NOT reject retrieval.
        """

        query_intent = (
            self.detect_intent(
                query
            )
        )

        retrieved_intent = (
            self.detect_intent(
                retrieved_text
            )
        )

        intent_match = (
            query_intent
            == retrieved_intent
        )

        # =================================
        # CONFIDENCE
        # =================================

        confidence = 1.0

        if not intent_match:

            confidence = 0.55

        if (
            query_intent == "general"
            or retrieved_intent == "general"
        ):

            confidence = 0.70

        result = {

            "query_intent":
                query_intent,

            "retrieved_intent":
                retrieved_intent,

            "intent_match":
                intent_match,

            "intent_confidence":
                confidence,
        }

        print(
            "INTENT VALIDATION:",
            result,
        )

        return result


# =====================================
# SINGLETON
# =====================================

intent_validation_service = (
    IntentValidationService()
)
