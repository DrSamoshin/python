"""Custom exceptions for Agent system."""


class AgentError(Exception):
    """Base exception for Agent errors."""
    pass


class LLMError(AgentError):
    """Error from LLM provider (OpenAI, etc)."""
    pass


class LLMAuthenticationError(LLMError):
    """Authentication error (invalid API key)."""
    pass


class LLMRateLimitError(LLMError):
    """Rate limit exceeded."""
    pass


class LLMContextLengthError(LLMError):
    """Context length exceeded."""
    pass