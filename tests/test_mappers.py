"""
Tests for the mappers module.
"""

import pytest
from mappers import (
    generate_fake_id,
    identity,
    textReqOpenAItoTGI,
    textAnsTGItoOpenAI,
    chatReqOpenAItoTGI,
)


class TestGenerateFakeId:
    """Test ID generation function."""

    def test_id_length(self):
        """Test that generated ID has correct length."""
        id1 = generate_fake_id()
        assert len(id1) == 28

    def test_id_uniqueness(self):
        """Test that generated IDs are unique."""
        ids = [generate_fake_id() for _ in range(100)]
        assert len(set(ids)) == 100  # All unique

    def test_id_characters(self):
        """Test that ID contains only valid characters."""
        valid_chars = set("0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
        id1 = generate_fake_id()
        assert all(c in valid_chars for c in id1)


class TestIdentityMapper:
    """Test the identity pass-through mapper."""

    def test_returns_same_input(self):
        """Test that identity returns the same input."""
        input_data = {"test": "value", "number": 42}
        result = identity(input_data)
        assert result == input_data

    def test_works_with_empty_dict(self):
        """Test identity with empty dictionary."""
        result = identity({})
        assert result == {}


class TestTextReqOpenAItoTGI:
    """Test OpenAI to TGI text request mapper."""

    def test_basic_mapping(self):
        """Test basic parameter mapping."""
        input_payload = {
            "prompt": "Hello world",
            "max_tokens": 100,
            "temperature": 0.7
        }

        result = textReqOpenAItoTGI(input_payload, {})

        assert result["inputs"] == "Hello world"
        assert result["parameters"]["max_new_tokens"] == 100
        assert result["parameters"]["temperature"] == 0.7

    def test_temperature_zero_handled(self):
        """Test that temperature=0 is converted to 0.01."""
        input_payload = {
            "prompt": "Test",
            "temperature": 0
        }

        result = textReqOpenAItoTGI(input_payload, {})
        assert result["parameters"]["temperature"] == 0.01

    def test_negative_temperature_handled(self):
        """Test that negative temperature is converted to 0.01."""
        input_payload = {
            "prompt": "Test",
            "temperature": -0.5
        }

        result = textReqOpenAItoTGI(input_payload, {})
        assert result["parameters"]["temperature"] == 0.01

    def test_default_values(self):
        """Test that default values are set for missing parameters."""
        input_payload = {
            "prompt": "Test"
        }

        result = textReqOpenAItoTGI(input_payload, {})

        assert result["parameters"]["max_new_tokens"] == 20
        assert result["parameters"]["best_of"] == 1
        assert result["parameters"]["top_k"] == 10
        assert result["parameters"]["top_p"] == 0.95

    def test_stop_sequences(self):
        """Test that stop sequences are passed through."""
        input_payload = {
            "prompt": "Test",
            "stop": ["###", "END"]
        }

        result = textReqOpenAItoTGI(input_payload, {})
        assert result["parameters"]["stop"] == ["###", "END"]


class TestTextAnsTGItoOpenAI:
    """Test TGI to OpenAI text response mapper."""

    def test_basic_mapping(self):
        """Test basic response mapping."""
        tgi_response = {
            "generated_text": "Hello there!",
            "details": {
                "finish_reason": "stop_sequence",
                "generated_tokens": 3,
                "prefill": [1, 2, 3, 4, 5]
            }
        }

        result = textAnsTGItoOpenAI(tgi_response, {})

        assert result["object"] == "text_completion"
        assert result["choices"][0]["text"] == "Hello there!"
        assert result["choices"][0]["finish_reason"] == "stop"
        assert result["usage"]["prompt_tokens"] == 5
        assert result["usage"]["completion_tokens"] == 3
        assert result["usage"]["total_tokens"] == 8

    def test_finish_reason_mapping(self):
        """Test finish reason mapping."""
        test_cases = [
            ("stop_sequence", "stop"),
            ("length", "length"),
            ("eos_token", "stop"),
            ("none", "none"),
        ]

        for tgi_reason, expected_reason in test_cases:
            tgi_response = {
                "generated_text": "Test",
                "details": {
                    "finish_reason": tgi_reason,
                    "generated_tokens": 1,
                    "prefill": []
                }
            }

            result = textAnsTGItoOpenAI(tgi_response, {})
            assert result["choices"][0]["finish_reason"] == expected_reason

    def test_id_generation(self):
        """Test that an ID is generated."""
        tgi_response = {
            "generated_text": "Test",
            "details": {
                "finish_reason": "stop",
                "generated_tokens": 1,
                "prefill": []
            }
        }

        result = textAnsTGItoOpenAI(tgi_response, {})
        assert "id" in result
        assert result["id"].startswith("chatcmpl-")
        assert len(result["id"]) > 10


class TestChatReqOpenAItoTGI:
    """Test OpenAI to TGI chat request mapper."""

    def test_basic_mapping_with_prompter(self):
        """Test basic chat request mapping."""
        input_payload = {
            "messages": [
                {"role": "user", "content": "Hello"}
            ],
            "max_tokens": 100,
            "temperature": 0.7
        }

        config = {
            "prompter": "fromTemplate",
            "template": {
                "preprompt": "",
                "start": "",
                "user": "\nUser: ",
                "assistant": "\nBot: "
            }
        }

        result = chatReqOpenAItoTGI(input_payload, config)

        assert "inputs" in result
        assert "Hello" in result["inputs"]
        assert result["parameters"]["max_new_tokens"] == 100
        assert result["parameters"]["temperature"] == 0.7

    def test_temperature_zero_handled(self):
        """Test that temperature=0 is converted to 0.01."""
        input_payload = {
            "messages": [{"role": "user", "content": "Test"}],
            "temperature": 0
        }

        config = {
            "prompter": "fromTemplate",
            "template": {
                "preprompt": "",
                "start": "",
                "user": "\nUser: ",
                "assistant": "\nBot: "
            }
        }

        result = chatReqOpenAItoTGI(input_payload, config)
        assert result["parameters"]["temperature"] == 0.01
