# sqlcoder_model.py
from transformers import AutoTokenizer, AutoModelForCausalLM, TextStreamer
import torch

# SQLCoder model setup
model_name = "defog/sqlcoder-7b-2"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    trust_remote_code=True,
    load_in_8bit=True,
    device_map="cuda:0",
    use_cache=True,
)

streamer = TextStreamer(tokenizer)
