import httpx

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen3:8b"
SYSTEM_PROMPT = "You are a friendly receptionist. Keep replies under 2 sentences."


def ask(messages: list[dict]) -> str:
    """Send the whole conversation to the LLM and return its reply."""
    response = httpx.post(
        OLLAMA_URL,
        json={"model": MODEL, "messages": messages, "stream": False, "think": False},
        timeout=60,
    )
    return response.json()["message"]["content"]


if __name__ == "__main__":
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    while True:
        user_text = input("You: ")
        if user_text.lower() in ("bye", "quit"):
            break
        messages.append({"role": "user", "content": user_text})
        reply = ask(messages)
        messages.append({"role": "assistant", "content": reply})
        print("Bot:", reply)