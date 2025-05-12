from src.utils import logger
from . import config
from .tokenizer import Tokenizer
from .summarizer import Summarizer
from .history_store import History_Store, LLM_Message
from typing_extensions import Optional

class ContextBuilder:
    
    def __init__(
        self,
        history_store: History_Store,
        summarizer: Summarizer,
        tokenizer_model_name: str,
        max_input_tokens: int,
        summary_trigger_ratio: float,
        protected_length: int,
        default_system_prompt: str
    ) -> None:
        self.history_store = history_store
        self.summarizer = summarizer
        self.tokenizer = Tokenizer(model_name=tokenizer_model_name)
        self.protected_length = protected_length
        self.default_system_prompt = default_system_prompt
        self.current_token_nums = max_input_tokens * summary_trigger_ratio
    
    
    async def _is_trigger_summarize(self, current_token_nums: int):
        if current_token_nums > self.summary_trigger_tokens:
            logger.warning(f"Message token count {current_token_nums} exceed trigger threshold, attempting summarization...")
            messages_to_summarize = self.history_store.get_messages_for_summary(self.protected_length)
            if not messages_to_summarize:
                logger.warning("No suitable messages found for summarization at this time.")
                return False

            logger.info(f"Selected {len(messages_to_summarize)} messages for summarization.")
            
            # Generate summary
            summary_tuple = await self.summarizer.summarize_messages(messages_to_summarize)
            
            if summary_tuple:
                summary_text, original_message_ids = summary_tuple
                self.history_store.add_summary_message(summary_text, original_message_ids)
                logger.info("Summary added to history store, replacing original messages.")
                return True
            else:
                logger.error("Summarization failed or returned no text.")
                return False
        else:
            return False # No summarization triggere
        
        
    async def manage_context(self, plugin_prompt: Optional[str] = None) -> tuple[list[LLM_Message], int]:
        prompt = plugin_prompt if plugin_prompt else config.DEFUALT_SYSTEM_PROMPT
        
        # Do-While to summarize history
        while True:
            messages = [
                {"role": "system", "content": prompt}
            ]
            messages += [message.to_openai_message() for message in self.history_store.get_history()]
            current_token_nums = self.tokenizer.count_token_for_message_list(messages)
            if not self._is_trigger_summarize(current_token_nums):
                break
        
        return messages
            