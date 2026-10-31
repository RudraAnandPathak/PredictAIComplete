import pytest

from local_ai import chat_with_ollama


def test_empty_messages_are_rejected():
    with pytest.raises(ValueError, match="At least one chat message"):
        chat_with_ollama([])


def test_invalid_message_is_rejected_before_network_call():
    with pytest.raises(ValueError, match="Message 1"):
        chat_with_ollama([{"role": "user", "content": 123}])


def test_temperature_out_of_range_is_rejected():
    with pytest.raises(ValueError, match="temperature"):
        chat_with_ollama([{"role": "user", "content": "hello"}], temperature=3)
