# human_model.py
from transformers import AutoModelForCausalLM, AutoTokenizer, TextStreamer
import torch

# Human Model setup (Qwen Model)
human_model_name = "Qwen/Qwen2.5-1.5B-Instruct"

human_model = AutoModelForCausalLM.from_pretrained(
    human_model_name,
    torch_dtype="auto",
    device_map="cuda:0"
)
human_tokenizer = AutoTokenizer.from_pretrained(human_model_name)
human_streamer = TextStreamer(human_tokenizer)
