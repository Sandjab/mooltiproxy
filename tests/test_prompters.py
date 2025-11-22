"""
Tests for the prompters module.
"""

import pytest
from prompters import fromTemplate, llama2_chat, DEFAULT_SYSTEM_PROMPT


class TestFromTemplate:
    """Test the fromTemplate prompter."""

    def test_empty_messages_returns_empty_string(self):
        """Test that empty message list returns empty string."""
        result = fromTemplate([], {})
        assert result == ""

    def test_basic_user_message(self):
        """Test basic user message formatting."""
        messages = [
            {"role": "user", "content": "Hello"}
        ]
        config = {
            "template": {
                "preprompt": "",
                "start": "",
                "user": "User: ",
                "assistant": "Assistant: "
            }
        }

        prompt, stops = fromTemplate(messages, config)

        # Should include default system prompt
        assert DEFAULT_SYSTEM_PROMPT in prompt
        assert "User: Hello" in prompt
        assert "Assistant: " in prompt
        assert stops == ["User: "]

    def test_system_message_included(self):
        """Test that system message is properly included."""
        messages = [
            {"role": "system", "content": "You are Bob"},
            {"role": "user", "content": "Hi"}
        ]
        config = {
            "template": {
                "preprompt": ">>>",
                "start": "<<<",
                "system": "",
                "user": "\nUser: ",
                "assistant": "\nBot: "
            }
        }

        prompt, stops = fromTemplate(messages, config)

        assert prompt.startswith(">>>You are Bob<<<")
        assert "\nUser: Hi" in prompt
        assert "\nBot: " in prompt

    def test_multi_turn_conversation(self):
        """Test multi-turn conversation formatting."""
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "How are you?"}
        ]
        config = {
            "template": {
                "preprompt": "",
                "start": "",
                "user": "\n[USER]: ",
                "assistant": "\n[BOT]: "
            }
        }

        prompt, stops = fromTemplate(messages, config)

        assert "\n[USER]: Hello" in prompt
        assert "\n[BOT]: Hi there!" in prompt
        assert "\n[USER]: How are you?" in prompt
        assert prompt.endswith("\n[BOT]: ")


class TestLlama2Chat:
    """Test the llama2_chat prompter."""

    def test_empty_messages_returns_empty_string(self):
        """Test that empty message list returns empty string."""
        result = llama2_chat([])
        assert result == ""

    def test_single_user_message(self):
        """Test single user message with default system prompt."""
        messages = [
            {"role": "user", "content": "Hello"}
        ]

        prompt, stops = llama2_chat(messages)

        assert "<s>" in prompt
        assert "[INST]" in prompt
        assert "[/INST]" in prompt
        assert "<<SYS>>" in prompt
        assert DEFAULT_SYSTEM_PROMPT in prompt
        assert "Hello" in prompt
        assert stops == ["[INST]"]

    def test_system_message_included(self):
        """Test that custom system message is used."""
        messages = [
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": "Hi"}
        ]

        prompt, stops = llama2_chat(messages)

        assert "You are a helpful assistant" in prompt
        assert "<<SYS>>" in prompt
        assert "<</SYS>>" in prompt
        assert "Hi" in prompt

    def test_multi_turn_conversation(self):
        """Test multi-turn conversation formatting."""
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "How are you?"}
        ]

        prompt, stops = llama2_chat(messages)

        # Should have two complete turns plus one incomplete
        assert prompt.count("<s>") == 2  # Two complete turns
        assert prompt.count("</s>") == 1  # One closed turn
        assert "Hello" in prompt
        assert "Hi there!" in prompt
        assert "How are you?" in prompt
        assert prompt.count("[INST]") == 2
        assert prompt.count("[/INST]") == 2

    def test_proper_token_placement(self):
        """Test that special tokens are properly placed."""
        messages = [
            {"role": "user", "content": "Test"}
        ]

        prompt, stops = llama2_chat(messages)

        # Format should be: <s>[INST] <<SYS>>...​<</SYS>> Test [/INST]
        assert "[INST]" in prompt
        assert "[/INST]" in prompt
        assert prompt.index("[INST]") < prompt.index("<<SYS>>")
        assert prompt.index("<<SYS>>") < prompt.index("<</SYS>>")
        assert prompt.index("<</SYS>>") < prompt.index("Test")


class TestDefaultSystemPrompt:
    """Test the default system prompt."""

    def test_default_prompt_exists(self):
        """Test that default system prompt is defined."""
        assert DEFAULT_SYSTEM_PROMPT is not None
        assert len(DEFAULT_SYSTEM_PROMPT) > 0

    def test_default_prompt_content(self):
        """Test that default prompt has expected content."""
        assert "helpful" in DEFAULT_SYSTEM_PROMPT
        assert "assistant" in DEFAULT_SYSTEM_PROMPT
