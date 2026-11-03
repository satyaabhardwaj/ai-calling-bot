import httpx

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen3:8b"
messages = [
    {"role": "system", "content": "You are a friendly receptionist. Keep replies under 2 sentences."}
]
while True:
    user_text = input("You: ")
    if user_text.lower() in ("bye", "quit"):
        break    
    messages.append({"role": "user", "content": user_text})

    response = httpx.post(
        OLLAMA_URL,
        json={"model": MODEL, "messages": messages, "stream": False, "think": False},
        timeout=60,
    )
    reply = response.json()["message"]["content"]

    messages.append({"role": "assistant", "content": reply})
    print("Bot:", reply) 