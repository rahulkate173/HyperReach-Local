"""
LLM Handler for BitNet integration
Manages offline LLM inference for message generation
"""
import logging
from typing import Optional
from pathlib import Path
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

from backend.config import settings

logger = logging.getLogger(__name__)


class BitNetHandler:
    """Handler for BitNet LLM model operations"""

    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.device = settings.DEVICE
        self.model_name = settings.MODEL_NAME
        self._ensure_model_cached()

    def _ensure_model_cached(self):
        """Ensure model is cached locally"""
        cache_dir = str(settings.CACHE_DIR)
        logger.info(f"Cache directory: {cache_dir}")

    def load_model(self) -> bool:
        """Load BitNet model and tokenizer"""
        try:
            logger.info(f"Loading BitNet model: {self.model_name}")
            logger.info(f"Using device: {self.device}")

            # Download and load tokenizer
            logger.info("Loading tokenizer...")
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                cache_dir=str(settings.CACHE_DIR),
                trust_remote_code=True,
                device_map=self.device,
            )

            # Download and load model
            logger.info("Loading model...")
            if self.device == "cuda" and torch.cuda.is_available():
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    cache_dir=str(settings.CACHE_DIR),
                    trust_remote_code=True,
                    torch_dtype=torch.float16,
                    device_map="auto",
                )
                logger.info("✓ Model loaded on GPU")
            else:
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    cache_dir=str(settings.CACHE_DIR),
                    trust_remote_code=True,
                    device_map="cpu",
                )
                logger.info("✓ Model loaded on CPU")

            logger.info("✓ Model and tokenizer loaded successfully")
            return True

        except Exception as e:
            logger.error(f"Error loading model: {e}")
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
        """Generate text using BitNet model"""
        if not self.is_loaded():
            raise RuntimeError("Model not loaded. Call load_model() first.")

        try:
            max_tokens = max_tokens or settings.MAX_TOKENS

            # Tokenize input
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)

            # Generate with low memory options
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

            # Decode output
            generated_text = self.tokenizer.decode(
                outputs[0], skip_special_tokens=True
            )

            # Remove prompt from generated text
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


# Global LLM handler instance
_llm_handler: Optional[BitNetHandler] = None


def get_llm_handler() -> BitNetHandler:
    """Get or create LLM handler singleton"""
    global _llm_handler
    if _llm_handler is None:
        _llm_handler = BitNetHandler()
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
