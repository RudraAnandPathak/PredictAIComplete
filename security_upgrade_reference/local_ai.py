import requests

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "qwen2.5:7b"


def chat_with_ollama(messages, temperature=0.2):
    """
    Send a conversation to the local Ollama model.

    Parameters:
        messages: A list of dictionaries containing
                  conversation roles and message content.
        temperature: Controls response variability.

    Returns:
        The assistant's response as a string.
    """

    if not messages:
        raise ValueError("At least one message is required.")

    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": 800,
        },
    }

    try:
        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=(10, 240),
        )

        response.raise_for_status()
        result = response.json()

        return result["message"]["content"]

    except requests.exceptions.ConnectionError as exc:
        raise RuntimeError(
            "Cannot connect to Ollama. "
            "Make sure Ollama is running."
        ) from exc

    except requests.exceptions.Timeout as exc:
        raise RuntimeError(
            "The AI model took too long to respond. "
            "Try again or use a shorter question."
        ) from exc

    except requests.exceptions.RequestException as exc:
        raise RuntimeError(
            f"Ollama request failed: {exc}"
        ) from exc

    except (KeyError, ValueError) as exc:
        raise RuntimeError(
            "Ollama returned an unexpected response."
        ) from exc


if __name__ == "__main__":
    test_messages = [
        {
            "role": "system",
            "content": (
                "You are PredictAI, an assistant that explains "
                "data analysis clearly. Be accurate, identify "
                "uncertainty, and never invent dataset statistics."
            ),
        },
        {
            "role": "user",
            "content": (
                "Explain the difference between correlation "
                "and causation in three sentences."
            ),
        },
    ]

    print("\nTesting PredictAI's local AI connection...\n")

    try:
        answer = chat_with_ollama(test_messages)
        print("Qwen's response:\n")
        print(answer)
        print("\nSUCCESS: PredictAI can communicate with Ollama.")

    except (RuntimeError, ValueError) as exc:
        print(f"\nTEST FAILED: {exc}")
