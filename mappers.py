"""
MIT License

Copyright (c) 2023 Jean-Paul Gavini

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

# *
# * This file contains the functions that map the source api to the target one, and back
# * To add a new target or source api, add the corresponding functions here
# * Though not mandatory, it is recommended to adopt the following naming convention and signature:
# * - <prefix>Req<Source>to<Target>(ip:Any, cfg:dict) for the request mapper
#     where prefix indicates the type of endpoint used (e.g. text completion, chat completion, etc.)
#     ip is the input payload, and cfg is the endpoint configuration dictionary
# * - <prefix>Ans<Target>to<Source> for the answer mapper
#     where prefix indicates the type of endpoint used (e.g. text completion, chat completion, etc.),
#     ip is the input payload, and cfg is the endpoint configuration dictionary

from typing import Any
import prompters
import time
import random


# Help function to generate an OpenAI-like id
def generate_fake_id() -> str:
    # generate a 28 chars long id, with the current timestamp encoded as prefix
    # ! this is a fake id whose uniqueness is not guaranteed
    PUSH_CHARS = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    L = len(PUSH_CHARS)
    id = ""
    ts = int("".join(str(time.time()).split(".")))

    while True:
        id += PUSH_CHARS[ts % L]
        ts = ts // L
        if ts < 1:
            break
    for i in range(28 - len(id)):
        id += random.choice(PUSH_CHARS)

    return id


# Pure paththrough function, to test prompter code branch
def identity(ip: Any, cfg: dict = {}) -> Any:
    """Identity function"""
    return ip


# * Input Conversion from an OpenAI text completion request to a TGI text completion request
def textReqOpenAItoTGI(ip: Any, cfg: dict = {}) -> Any:
    """Converts a payload to TGI format"""
    # TODO Mapping of typical_p

    # * Sanity Checks
    # temperature can be O for OpenAI, but must be strictly positive for TGI
    temperature = ip.get("temperature", 0.5)
    if temperature <= 0:
        temperature = 0.01

    op = {
        "inputs": ip.get("prompt", ""),
        "parameters": {
            "best_of": ip.get("best_of", 1),
            "decoder_input_details": True,
            "details": False,
            "do_sample": False,
            "max_new_tokens": ip.get("max_tokens", 20),
            "repetition_penalty": ip.get("frequency_penalty", 1.03),
            "return_full_text": False,
            "seed": 0,
            "stop": ip.get("stop", []),
            "temperature": ip.get("temperature", 0.5),
            "top_k": ip.get("top_k", 10),
            "top_p": ip.get("top_p", 0.95),
            "truncate": None,
            "typical_p": 0.95,
            "watermark": False,
        },
    }

    return op


# * Output conversion from a TGI text completion answer to an OpenAI text completion answer
def textAnsTGItoOpenAI(ip: Any, cfg: dict = {}) -> Any:
    """Converts a payload from TGI format"""
    # TODO compute tokens, check finish reasons values

    reasons_dict = {
        "stop_sequence": "stop",
        "length": "length",
        "eos_token": "stop",
        "none": "none",
    }

    # Map finish reason
    fr = ip["details"].get("finish_reason", "none")
    finish_reason = reasons_dict.get(fr, fr)

    # Retrieve token counts
    in_tokens = len(ip["details"].get("prefill", ""))
    out_tokens = ip["details"].get("generated_tokens", 0)

    op = {
        "id": f"chatcmpl-{generate_fake_id()}",
        "object": "text_completion",
        "created": int(time.time()),
        "model": "Unknown",
        "choices": [
            {
                "text": ip.get("generated_text", ""),
                "index": 0,
                "logprobs": None,
                "finish_reason": finish_reason,
            }
        ],
        "usage": {
            "prompt_tokens": in_tokens,
            "completion_tokens": out_tokens,
            "total_tokens": in_tokens + out_tokens,
        },
    }
    return op


# * Input Conversion from an OpenAI chat completion request to a TGI chat completion request
def chatReqOpenAItoTGI(ip: Any, cfg: dict = {}) -> Any:
    """Converts a payload to TGI format"""
    # TODO Mapping of presence_penalty and frequency_penalty to repetition_penalty
    # TODO Mapping of typical_p

    # * Sanity Checks
    # temperature can be O for OpenAI, but must be strictly positive for TGI
    temperature = ip.get("temperature", 0.5)
    if temperature <= 0:
        temperature = 0.01

    prompter = cfg.get("prompter", "fromTemplate")
    prompt, stops = getattr(prompters, prompter)(ip.get("messages", []), cfg)

    op = {
        "inputs": prompt,
        "parameters": {
            "best_of": ip.get("best_of", 1),
            "decoder_input_details": True,
            "details": False,
            "do_sample": False,
            "max_new_tokens": ip.get("max_tokens", 512),
            "repetition_penalty": ip.get("frequency_penalty", 1.03),
            "return_full_text": False,
            "seed": 0,
            "stop": ip.get("stop", stops),
            "temperature": temperature,
            "top_k": ip.get("top_k", 10),
            "top_p": ip.get("top_p", 0.95),
            "truncate": None,
            "typical_p": 0.95,
            "watermark": False,
        },
    }

    return op


# * Output conversion from a TGI chat completion answer to an OpenAI chat completion answer
def chatAnsTGItoOpenAI(ip: Any, cfg: dict = {}) -> Any:
    """Converts a payload from TGI format"""

    reasons_dict = {
        "stop_sequence": "stop",
        "length": "length",
        "eos_token": "stop",
        "none": "none",
    }

    # Map finish reason
    fr = ip["details"].get("finish_reason", "none")
    finish_reason = reasons_dict.get(fr, fr)

    # Check if the answers contains a stop token, and remove it
    answer = ip.get("generated_text", "")
    if fr == "stop_sequence":
        stop = cfg["template"].get("user", None)
        if stop and answer.endswith(stop):
            answer = answer[: -len(stop)]

    # Compute id
    id = ip.get("id", f"chatcmpl-{generate_fake_id()}")

    # Retrieve token counts
    in_tokens = len(ip["details"].get("prefill", ""))
    out_tokens = ip["details"].get("generated_tokens", 0)

    op = {
        "id": id,
        "object": "chat.completion",
        "created": int(time.time()),
        "model": "Unknown",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": answer,
                },
                "finish_reason": finish_reason,
            }
        ],
        "usage": {
            "prompt_tokens": in_tokens,
            "completion_tokens": out_tokens,
            "total_tokens": in_tokens + out_tokens,
        },
    }

    return op
