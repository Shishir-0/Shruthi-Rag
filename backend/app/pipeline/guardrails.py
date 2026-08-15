"""
SHRUTI Security Guardrails Engine
Handles off-topic filtering, unsafe input rejection, prompt injection defense, and context poisoning prevention.
"""
from backend.app.schemas import GuardrailCheck

class GuardrailEngine:
    OFF_TOPIC_REJECTION_MSG = "I am trained to answer questions grounded in the available knowledge base corpus."
    UNSAFE_REJECTION_MSG = "Request rejected due to safety or policy violation."

    def validate_input(self, query: str, query_type: str) -> GuardrailCheck:
        if query_type == "UNSAFE":
            return GuardrailCheck(
                is_safe=False,
                is_answerable=False,
                query_class="UNSAFE",
                rejection_reason=self.UNSAFE_REJECTION_MSG
            )

        if query_type == "OFF_TOPIC":
            return GuardrailCheck(
                is_safe=True,
                is_answerable=False,
                query_class="OFF_TOPIC",
                rejection_reason=self.OFF_TOPIC_REJECTION_MSG
            )

        return GuardrailCheck(is_safe=True, is_answerable=True, query_class=query_type)

    def sanitize_retrieved_context(self, context_text: str) -> str:
        # Prompt injection defense: strip dangerous instruction markers embedded in retrieved text
        forbidden_tokens = [
            "ignore previous instructions", "SYSTEM PROMPT:", "NEW INSTRUCTION:", "OVERRIDE SYSTEM"
        ]
        sanitized = context_text
        for tok in forbidden_tokens:
            sanitized = sanitized.replace(tok, "[STRIPPED_DATA]")
        return sanitized

guardrail_engine = GuardrailEngine()
