import os
from typing import List

from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig, pipeline
import torch

from src.config import HF_LLM_MODEL, USE_8BIT_QUANTIZATION

_generator = None


def _get_generator():
    global _generator
    if _generator is not None:
        return _generator

    model_name = HF_LLM_MODEL
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    # Setup 8-bit quantization for Llama-2-7b on 4080
    quantization_config = None
    if USE_8BIT_QUANTIZATION and torch.cuda.is_available():
        quantization_config = BitsAndBytesConfig(
            load_in_8bit=True,
            bnb_8bit_quant_type="nf4",
            bnb_8bit_use_double_quant=True,
        )

    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        quantization_config=quantization_config,
        device_map="auto",
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
    )

    # For Llama-2-chat, set pad token
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    _generator = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        device_map="auto",
    )
    return _generator


def generate_response(prompt: str) -> str:
    gen = _get_generator()

    # Generate with lower max_new_tokens for Llama-2-7b to stay within VRAM
    output = gen(
        prompt,
        max_new_tokens=200,
        do_sample=True,
        top_p=0.9,
        temperature=0.7,
        pad_token_id=50256,
    )
    return output[0]["generated_text"]
