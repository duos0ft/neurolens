from enum import StrEnum


class AICapability(StrEnum):
    REQUEST_CLASSIFICATION = "request_classification"
    MESSAGE_EXPLANATION = "message_explanation"
    TASK_ASSISTANCE = "task_assistance"
    POLICY_GENERATION = "policy_generation"
    EMBEDDINGS = "embeddings"
    KNOWLEDGE_RETRIEVAL = "knowledge_retrieval"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    CONVERSATION_TITLE = "conversation_title"
    GENERAL_CONVERSATION = "general_conversation"
    POLICY_QUESTION = "policy_question"
