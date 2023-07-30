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

# if not preprompt is provided, this default prompt will be used
DEFAULT_SYSTEM_PROMPT = """You are a helpful, respectful and honest assistant. Always answer as helpfully as possible, while being safe. Please ensure that your responses are socially unbiased and positive in nature. If a question does not make any sense, or is not factually coherent, explain why instead of answering something not correct. If you don't know the answer to a question, please don't share false information."""


# Build a prompt from a prompt template and a list of messages
def fromTemplate(messages: list[dict], cfg: dict) -> (str, str):
    if not messages:
        return ""
    i = 0

    template = cfg["template"]

    if messages[0]["role"] == "system":
        prompt = template["preprompt"] + messages[0]["content"] + template["start"]
        i = 1
    else:
        prompt = template["preprompt"] + DEFAULT_SYSTEM_PROMPT + template["start"]

    if messages[i:]:
        for message in messages[i:]:
            role = message["role"]
            content = message["content"]
            prompt += template[role] + content

    prompt += template["assistant"]

    return prompt, [template["user"]]


# Specific prompter for Llama-2
# Official Llama-2 chat has a very specific prompt format
def llama2_chat(messages: list[dict], cfg: dict = {}) -> (str, str):
    if not messages:
        return ""

    B_INST, E_INST = "[INST]", "[/INST]"
    B_SYS, E_SYS = "<<SYS>>\n", "\n<</SYS>>\n\n"
    BOS, EOS = "<s>", "</s>"

    if messages[0]["role"] != "system":
        messages = [
            {
                "role": "system",
                "content": DEFAULT_SYSTEM_PROMPT,
            }
        ] + messages
    messages = [
        {
            "role": messages[1]["role"],
            "content": B_SYS + messages[0]["content"] + E_SYS + messages[1]["content"],
        }
    ] + messages[2:]

    messages_list = [
        f"{BOS}{B_INST} {(prompt['content']).strip()} {E_INST} {(answer['content']).strip()} {EOS}"
        for prompt, answer in zip(messages[::2], messages[1::2])
    ]
    messages_list.append(f"{BOS}{B_INST} {(messages[-1]['content']).strip()} {E_INST}")

    return "".join(messages_list), [B_INST]


if __name__ == "__main__":
    messages = [
        {"role": "system", "content": "You are an helpful assistant named Bob."},
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hello! How can I assist you today?"},
        {"role": "user", "content": "tell me a joke"},
    ]
    print("-------------------------------")
    print(llama2_chat(messages))
    print("-------------------------------")
