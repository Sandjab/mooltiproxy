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
# * This is a minimal chatbot using MooltProxy.
# * Warning: this is a very simple implementation with no context cycling
# * for a more comprehensive implementation, use MooltiChat
# ! you need to install openai package to run this example
# ! pip install -U openai
# *

import openai
import os

# * set the the openai api key and the target to the proxy
openai.api_base = "http://127.0.0.1:8000"
openai.api_key = os.getenv("SANDJAB_PROXY_KEY")

# * Specify the proxy target
TARGET = "loic"

CONTEXT = """You are Bob, a very polite and helpfull assistant. Always answer as helpfully as possible, while being safe. Please ensure that your responses are socially unbiased and positive in nature. If a question does not make any sense, or is not factually coherent, explain why instead of answering something not correct. If you don't know the answer to a question, please don't share false information."""


# function for managing chat history


def generate_chat_response(prompt, chat_model="gpt-3.5-turbo", chat_history=[]):
    response = openai.ChatCompletion.create(
        model=chat_model,
        messages=chat_history + [{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=150,
        headers={"target": TARGET},  # * This is how you specify the target
    )

    chat_history.append({"role": "user", "content": prompt})
    chat_history.append(
        {"role": "assistant", "content": response["choices"][0]["message"]["content"]}
    )
    return response["choices"][0]["message"]["content"], chat_history


def main():
    print("Welcome to the chat! Type 'exit' to end the conversation.")

    # set a minimal preprompt
    chat_history = [{"role": "system", "content": CONTEXT}]

    user_input = ""
    while user_input.lower() != "exit":
        user_input = input("You: ")

        if user_input.lower() == "exit":
            break

        try:
            response, chat_history = generate_chat_response(
                user_input, chat_history=chat_history
            )
            print("ChatBot:", response)
        except Exception as e:
            print(e)


if __name__ == "__main__":
    main()
