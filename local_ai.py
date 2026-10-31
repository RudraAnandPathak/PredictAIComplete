"""Configurable Ollama client for PredictAI's local development version."""
from __future__ import annotations

import os
from typing import Any

import requests

DEFAULT_OLLAMA_URL = "http://localhost:11434/api/chat"
DEFAULT_MODEL_NAME = "qwen2.5:7b"


def _ollama_url() -> str:
    """Read the endpoint at call time so environment changes are respected."""
    return os.getenv("PREDICTAI_OLLAMA_URL", DEFAULT_OLLAMA_URL).rstrip("/")


def _model_name() -> str:
    return os.getenv("PREDICTAI_OLLAMA_MODEL", DEFAULT_MODEL_NAME).strip() or DEFAULT_MODEL_NAME


def chat_with_ollama(
    messages: list[dict[str, str]],
    temperature: float = 0.2,
    *,
    timeout_connect: float = 10,
    timeout_read: float = 240,
    num_predict: int = 800,
) -> str:
    """Send chat messages to Ollama and return the assistant text.

    Configuration environment variables:
      PREDICTAI_OLLAMA_URL   Full chat endpoint (default localhost:11434/api/chat)
      PREDICTAI_OLLAMA_MODEL Model name (default qwen2.5:7b)

    This adapter is for local development. It does not make Ollama available
    to a public website when the user's computer is switched off.
    """
    if not isinstance(messages, list) or not messages:
        raise ValueError("At least one chat message is required.")
    if not 0 <= float(temperature) <= 2:
        raise ValueError("temperature must be between 0 and 2.")
    if int(num_predict) < 1:
        raise ValueError("num_predict must be a positive integer.")

    for index, message in enumerate(messages):
        if not isinstance(message, dict) or not isinstance(message.get("role"), str) or not isinstance(message.get("content"), str):
            raise ValueError(f"Message {index + 1} must contain string 'role' and 'content' fields.")

    payload: dict[str, Any] = {
        "model": _model_name(),
        "messages": messages,
        "stream": False,
        "options": {"temperature": float(temperature), "num_predict": int(num_predict)},
    }

    try:
        response = requests.post(
            _ollama_url(),
            json=payload,
            timeout=(float(timeout_connect), float(timeout_read)),
        )
        response.raise_for_status()
        result = response.json()
    except requests.exceptions.ConnectionError as exc:
        raise RuntimeError("Cannot connect to Ollama. Make sure Ollama is installed and running.") from exc
    except requests.exceptions.Timeout as exc:
        raise RuntimeError("The AI model took too long to respond. Try again or use a shorter question.") from exc
    except requests.exceptions.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else "unknown"
        if status == 404:
            raise RuntimeError(
                f"Ollama returned HTTP 404. Check that model '{_model_name()}' is installed and the endpoint is correct."
            ) from exc
        raise RuntimeError(f"Ollama returned an HTTP error (status {status}).") from exc
    except requests.exceptions.RequestException as exc:
        raise RuntimeError("The request to Ollama failed. Check your local connection and configuration.") from exc
    except ValueError as exc:
        # requests raises ValueError for invalid JSON. This is handled below
        # separately from a structurally valid JSON response.
        raise RuntimeError("Ollama returned invalid JSON.") from exc

    try:
        content = result["message"]["content"]
    except (KeyError, TypeError) as exc:
        raise RuntimeError("Ollama returned an unexpected response structure.") from exc

    if not isinstance(content, str) or not content.strip():
        raise RuntimeError("Ollama returned an empty response.")
    return content


if __name__ == "__main__":
    test_messages = [
        {"role": "system", "content": "You are PredictAI. Be accurate and never invent dataset statistics."},
        {"role": "user", "content": "Explain the difference between correlation and causation in three sentences."},
    ]
    print("Testing PredictAI's local AI connection...\n")
    try:
        print(chat_with_ollama(test_messages))
        print("\nSUCCESS: PredictAI received a response from Ollama.")
    except (RuntimeError, ValueError) as exc:
        print(f"\nTEST FAILED: {exc}")
