from ai_calling_bot.brain import SYSTEM_PROMPT, ask
from ai_calling_bot.ears import record, transcribe

messages = [{"role": "system", "content": SYSTEM_PROMPT}]
print("Voice chat started. Say 'bye' to end.")

while True:
    user_text = transcribe(record())
    print("You:", user_text)
    if "bye" in user_text.lower():
        break

    messages.append({"role": "user", "content": user_text})
    reply = ask(messages)
    messages.append({"role": "assistant", "content": reply})
    print("Bot:", reply)