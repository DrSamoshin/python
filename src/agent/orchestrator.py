"""Agent Orchestrator - coordinates LLM, Tools, and RAG."""

import logging
from src.agent.llm.openai_client import OpenAIClient
from src.agent.dto import AgentMessage, AgentRequest, AgentResponse
from src.agent.exceptions import LLMError, LLMAuthenticationError, LLMRateLimitError

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """Main coordinator for Agent system with error handling."""

    def __init__(self):
        self.llm_client = OpenAIClient()
        # TODO: context_builder, tool_registry

    async def process(self, request: AgentRequest) -> AgentResponse:
        """
        Process user message through LLM with error handling.

        Args:
            request: AgentRequest with chat history and user message

        Returns:
            AgentResponse with generated content or error message
        """
        try:
            # Combine history + current message
            all_messages = request.chat_history + [request.user_message]

            # Call LLM
            response_content = await self.llm_client.chat_completion(
                messages=all_messages,
                system_message="You are a helpful assistant."
            )

            return AgentResponse(content=response_content)

        except LLMAuthenticationError as e:
            logger.error(f"LLM authentication error: {e}")
            return AgentResponse(
                content="Configuration error: Invalid OpenAI API key. Please contact support."
            )

        except LLMRateLimitError as e:
            logger.error(f"LLM rate limit error: {e}")
            return AgentResponse(
                content="Too many requests. Please wait a moment and try again."
            )

        except LLMError as e:
            logger.error(f"LLM error: {e}")
            return AgentResponse(
                content=f"Sorry, I encountered an error: {str(e)}"
            )

        except Exception as e:
            logger.error(f"Unexpected error in AgentOrchestrator: {e}", exc_info=True)
            return AgentResponse(
                content="An unexpected error occurred. Please try again."
            )


