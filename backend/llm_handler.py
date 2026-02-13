"""
LLM Handler for TinyLlama integration
Manages offline LLM inference for message generation
"""
import logging
from typing import Optional
from pathlib import Path
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import warnings

from backend.config import settings

logger = logging.getLogger(__name__)

# Suppress deprecation warnings
warnings.filterwarnings("ignore", category=FutureWarning)


class LLMHandler:
    """Handler for LLM model operations"""

    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.device = settings.DEVICE
        self.model_name = settings.MODEL_NAME
        self.fallback_model = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
        self._ensure_model_cached()

    def _ensure_model_cached(self):
        """Ensure model is cached locally"""
        cache_dir = str(settings.CACHE_DIR)
        logger.info(f"Cache directory: {cache_dir}")

    def load_model(self) -> bool:
        """Load LLM model and tokenizer"""
        try:
            logger.info(f"Loading model: {self.model_name}")
            logger.info(f"Using device: {self.device}")

            logger.info("Loading tokenizer...")
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                cache_dir=str(settings.CACHE_DIR),
                trust_remote_code=True,
            )

            logger.info("Loading model...")
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                cache_dir=str(settings.CACHE_DIR),
                trust_remote_code=True,
                low_cpu_mem_usage=True,
            )

            logger.info("✓ Model loaded successfully on CPU")
            logger.info("✓ Model and tokenizer loaded successfully")
            return True

        except Exception as e:
            logger.error(f"Error loading model {self.model_name}: {e}")
            logger.info(f"Attempting to load fallback model: {self.fallback_model}")
            
            try:
                self.model_name = self.fallback_model
                logger.info(f"Loading fallback model: {self.model_name}")
                
                self.tokenizer = AutoTokenizer.from_pretrained(
                    self.model_name,
                    cache_dir=str(settings.CACHE_DIR),
                    trust_remote_code=True,
                )

                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    cache_dir=str(settings.CACHE_DIR),
                    trust_remote_code=True,
                    low_cpu_mem_usage=True,
                )
                
                logger.info("✓ Fallback model loaded successfully")
                return True
                
            except Exception as fallback_error:
                logger.error(f"Failed to load fallback model: {fallback_error}")
                return False

    def is_loaded(self) -> bool:
        """Check if model is loaded"""
        return self.model is not None and self.tokenizer is not None

    def generate_text(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        top_p: float = 0.9,
    ) -> str:
        """Generate text using LLM model"""
        if not self.is_loaded():
            raise RuntimeError("Model not loaded. Call load_model() first.")

        try:
            max_tokens = max_tokens or settings.MAX_TOKENS

            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)

            with torch.no_grad():
                outputs = self.model.generate(
                    inputs["input_ids"],
                    max_length=min(max_tokens + len(inputs["input_ids"][0]), 2048),
                    temperature=temperature,
                    top_p=top_p,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id,
                    num_return_sequences=1,
                )

            generated_text = self.tokenizer.decode(
                outputs[0], skip_special_tokens=True
            )

            result = generated_text[len(prompt) :].strip()
            return result

        except Exception as e:
            logger.error(f"Error generating text: {e}")
            raise

    def generate_batch(
        self,
        prompts: list,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
    ) -> list:
        """Generate text for multiple prompts"""
        results = []
        for prompt in prompts:
            try:
                result = self.generate_text(
                    prompt, max_tokens=max_tokens, temperature=temperature
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Error generating for prompt: {e}")
                results.append("")
        return results

    def unload_model(self):
        """Unload model to free memory"""
        if self.model is not None:
            del self.model
            self.model = None
        if self.tokenizer is not None:
            del self.tokenizer
            self.tokenizer = None
        if self.device == "cuda":
            torch.cuda.empty_cache()
        logger.info("Model unloaded and memory cleared")


_llm_handler: Optional[LLMHandler] = None


def get_llm_handler() -> LLMHandler:
    """Get or create LLM handler singleton"""
    global _llm_handler
    if _llm_handler is None:
        _llm_handler = LLMHandler()
    return _llm_handler


async def initialize_llm() -> bool:
    """Initialize LLM on startup"""
    handler = get_llm_handler()
    return handler.load_model()


async def shutdown_llm():
    """Shutdown LLM on application shutdown"""
    global _llm_handler
    if _llm_handler is not None:
        _llm_handler.unload_model()
        _llm_handler = None
    logger.info("LLM shutdown complete")
