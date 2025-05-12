from src.utils import logger
from . import config
from .client import LLMClient
from .history_store import LLM_Message
from typing import Optional


class Summarizer:
    """
    Handles the generation of summaries for conversation history segments.
    """
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    def _format_messages_for_summary_prompt(self, messages_to_summarize: list[LLM_Message]) -> str:
        """
        Formats a list of Message objects into a single string for the summary prompt.
        Example:
        User: Hello
        Assistant: Hi there
        User: How are you?
        """
        formatted_text = []
        for msg in messages_to_summarize:
            # Use a simple role indicator. Avoid "summary_placeholder" here.
            role_display = "AI" if msg.role in ["assistant", "summary"] else msg.role.capitalize()
            formatted_text.append(f"{role_display}: {msg.content}")
        return "\n".join(formatted_text)

    async def summarize_messages(self,
                           messages_to_summarize: list[LLM_Message],
                           instruction: str = config.DEFAULT_SUMMARY_PROMPT,
                           summary_model: str = config.SUMMARY_MODEL,
                           max_tokens: int = config.MAX_RESPONSE_TOKEN
                          ) -> Optional[tuple[str, list[str]]]:
        """
        Generates a summary for a list of messages.

        Args:
            messages_to_summarize (List[Message]): The messages to be summarized.
            instruction (str): The specific instruction for the summarization LLM.
            summary_model (str): The model to use for summarization.
            max_tokens (int): Max tokens for the generated summary.

        Returns:
            Optional[Tuple[str, List[str]]]: A tuple containing the summary text
                                             and a list of original message IDs that were summarized.
                                             Returns None if summarization fails or no messages provided.
        """
        if not messages_to_summarize:
            logger.warning("待总结消息为空")
            return None

        text_block = self._format_messages_for_summary_prompt(messages_to_summarize)
        

        summary_text = await self.llm_client.get_summary(
            text_to_summarize=text_block,
            model=summary_model,
            max_tokens=max_tokens,
            instruction=instruction
        )

        if summary_text:
            original_ids = [msg.id for msg in messages_to_summarize]
            return summary_text, original_ids
        else:
            print("Failed to generate summary from LLM.")
            return None