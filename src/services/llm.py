import warnings
warnings.filterwarnings("ignore")

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

    # Use 4-bit quantization on GPU to keep Qwen on VRAM instead of offloading to CPU.
    quantization_config = None
    if USE_8BIT_QUANTIZATION and torch.cuda.is_available():
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=torch.float16,
        )

    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        quantization_config=quantization_config,
        device_map="auto",
        #dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
    )

    # Qwen tokenizers often do not define a pad token; reuse EOS for generation.
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    _generator = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
    )
    return _generator


def init_llm():
    _get_generator()
    print(f"LLM model '{HF_LLM_MODEL}' loaded successfully.\n")


def generate_response(prompt: str) -> str:
    gen = _get_generator()

    # Keep generation short enough for 7B-class models on a single consumer GPU.
    output = gen(
        prompt,
        max_new_tokens=200,
        do_sample=True,
        top_p=0.9,
        temperature=0.7,
        return_full_text=False,
        pad_token_id=gen.tokenizer.eos_token_id,
    )
    return output[0]["generated_text"]
