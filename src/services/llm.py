import json
import re
from typing import Any, Dict

import logging

import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    GenerationConfig,
    TextStreamer,
)

from src.config import HF_LLM_MODEL, HF_LLM_PARSING_MODEL, USE_4BIT_QUANTIZATION

_model_name: str = HF_LLM_MODEL
_model: AutoModelForCausalLM | None = None
_tokenizer: AutoTokenizer | None = None

def get_model(model_name: str = HF_LLM_MODEL) -> tuple[AutoModelForCausalLM, AutoTokenizer]:
    global _model, _tokenizer, _model_name

    if _model is not None and model_name == _model_name:
        return _model, _tokenizer

    _tokenizer = AutoTokenizer.from_pretrained(
        model_name,
        trust_remote_code=True,
    )

    if _tokenizer.pad_token is None:
        _tokenizer.pad_token = _tokenizer.eos_token

    if USE_4BIT_QUANTIZATION:
        quant_cfg = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=torch.bfloat16,
        )
    else:
        quant_cfg = None

    _model = AutoModelForCausalLM.from_pretrained(
        model_name,
        quantization_config=quant_cfg,
        device_map="auto",
        torch_dtype=torch.bfloat16,
        trust_remote_code=True,
        attn_implementation="sdpa",
    )
    _model.eval()
    _model = torch.compile(_model)

    return _model, _tokenizer

def init_llm():
    if HF_LLM_PARSING_MODEL == HF_LLM_MODEL:
        get_model(HF_LLM_MODEL)  # Single model for both generation and parsing
        logging.info("LLM model '%s' loaded successfully for both generation and parsing.\n", HF_LLM_MODEL)
    else: 
        logging.warning("Parsing model '%s' is different from generation model '%s'. Cannot preload models.", HF_LLM_PARSING_MODEL, HF_LLM_MODEL)
        logging.warning("Update config to use the same model for both to enable preloading and faster inference.")


def run_inference(
    messages: list[dict],
    *,
    max_new_tokens: int,
    temperature: float,
    top_p: float,
    repetition_penalty: float,
    do_sample: bool,
    stream: bool = False,
    model_name: str = HF_LLM_MODEL,
) -> str:
    model, tokenizer = get_model(model_name)

    # Apply Qwen chat template — produces the <|im_start|>…<|im_end|> wrapping
    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )
    inputs = tokenizer(text, return_tensors="pt").to(model.device)

    gen_cfg = GenerationConfig(
        max_new_tokens=max_new_tokens,
        do_sample=do_sample,
        temperature=temperature if do_sample else None,
        top_p=top_p if do_sample else None,
        repetition_penalty=repetition_penalty,
        pad_token_id=tokenizer.eos_token_id,
    )

    streamer = TextStreamer(tokenizer, skip_prompt=True) if stream else None

    with torch.inference_mode():
        output_ids = model.generate(
            **inputs,
            generation_config=gen_cfg,
            streamer=streamer,
        )

    new_tokens = output_ids[0][inputs["input_ids"].shape[-1]:]
    return tokenizer.decode(new_tokens, skip_special_tokens=True).strip()


def generate_response(
    prompt: str,
    system_prompt: str = "You are a helpful assistant.",
    *,
    max_new_tokens: int = 512,
    temperature: float = 0.7,
    top_p: float = 0.9,
    repetition_penalty: float = 1.1,
    stream: bool = False,
) -> str:
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": prompt},
    ]
    return run_inference(
        messages,
        max_new_tokens=max_new_tokens,
        temperature=temperature,
        top_p=top_p,
        repetition_penalty=repetition_penalty,
        do_sample=True,
        stream=stream,
    )


def generate_json(system_prompt: str, user_prompt: str, column_name: str) -> Dict[str, Any]:
    # Uses parsing model with deterministic decoding to extract structured info from user query.

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": user_prompt},
    ]

    raw = run_inference(
        messages,
        max_new_tokens=32,       # JSON result is always short
        temperature=0.0,         # near-deterministic — extraction is not creative
        top_p=1.0,
        repetition_penalty=1.15, # prevents null/null/null loops on hard cases
        do_sample=False,         # greedy decoding: fastest + most consistent
        model_name=HF_LLM_PARSING_MODEL,
    )

    return safe_json_parse(raw, column_name)

def safe_json_parse(raw: str, column_name: str) -> Dict[str, Any]:
    cleaned = re.sub(r"```(?:json)?|```", "", raw).strip()

    # Grab the first {...} block (model sometimes adds a trailing comment)
    match = re.search(r"\{.*?\}", cleaned, re.DOTALL)
    if not match:
        logging.warning("No JSON object found in model output: %r", raw)
        return {"name": column_name, "value": None, "constraint": None}

    try:
        data = json.loads(match.group())
    except json.JSONDecodeError as exc:
        logging.warning("JSON parse error (%s) for output: %r", exc, raw)
        return {"name": column_name, "value": None, "constraint": None}

    value = data.get("value")
    constraint = data.get("constraint")

    if value in (None, "None", "null", "NULL"):
        value = None
    if constraint in (None, "None", "null", "NULL"):
        constraint = None

    return {
        "name": data.get("name", column_name),
        "value": value,
        "constraint": constraint
    }