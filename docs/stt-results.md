# Speech-to-text results

Testing how well Whisper understands English, Hindi and Hinglish (mixed Hindi + English),
to decide whether it's good enough for Indian callers and to compare with Sarvam later.

## Setup

| Item | Value |
|---|---|
| Model | `mlx-community/whisper-large-v3-turbo` (1.61 GB) |
| Library | `mlx-whisper` (runs on the Apple GPU) |
| Machine | MacBook Air M2, 16 GB RAM, built-in microphone |
| Audio | 5-second recordings, 16,000 Hz, mono, float32 |
| Language setting | Auto-detect (Whisper guesses the language) unless noted |
| Date | 2026-11-04 |

## Results: auto-detect

| # | Test | What I said (approx.) | Detected | Whisper output | Loudest sample | Verdict |
|---|---|---|---|---|---|---|
| 1 | English | "Hi, my name is Satyabharadwaj. Who are you? What is your name?" | `en` | Hi my name is Satyabharadwaj. Who are you? What is your name? | 1.23 (clipped) | ✅ Perfect, including name and punctuation |
| 2 | Hindi | "Hello, mera naam Satya hai, mere ko ek naya kitchen chahiye" | `hi` | हेलो मेरा नाम सत्या है मेरे को एक नया कीचन चाहिए | — | ✅ Correct, in Devanagari |
| 3 | Hinglish | "Hi hi, mera budget 2 lakh rupay, can you call me tomorrow" | `hi` | हाई हाई मेरा बजट दो लाख रुपे क्यान यू काल मी टुमोरो | 0.88 | ⚠️ English part written phonetically in Devanagari |
| 4 | Hinglish | "Mera budget 2 lakh hai, can you call me tomorrow?" | `hi` | मेरा बजट दो लाख है, can you call me tomorrow? | 1.20 (clipped) | ✅ Mixed script: Hindi in Devanagari, English in Latin |

## Results: forced language

| # | Test | Setting | What I said | Whisper output | Verdict |
|---|---|---|---|---|---|
| 5 | Hinglish | `language="en"` | "Hi, mera budget 2 lakh hai, can you call me tomorrow?" | Hi, my budget 2,000,000,000, can you call me tomorrow? | ❌ **Translated** to English, and "2 lakh" (200,000) became **2,000,000,000** (2 billion) |
| 6 | Hindi | `language="en"` | "Hello, mera naam Satya hai, aapka naam kya hai?" | Hello, my name is Satya. What's your name? | ⚠️ **Translated** to English. Meaning is correct, but it's no longer what the caller actually said |
| 7 | Hinglish | `language="hi"` | "Mera naam Satya hai, can you call me tomorrow?" | मेरा नाम सत्या है Can you call me tomorrow? | ✅ Best Hinglish result: Hindi in Devanagari, English kept in English, nothing translated |

## Observations

1. **English and pure Hindi work well.** Whisper detected the language correctly and the text was accurate.
2. **Hinglish is inconsistent.** Two similar Hinglish sentences (tests 3 and 4) came out in different
   formats: one fully in Devanagari (English words spelled by sound), one in mixed script.
3. **Numbers come out as words.** "2 lakh" became "दो लाख". Field extraction (Lesson 7) must
   convert spoken/Hindi numbers like "दो लाख" or "2 lakh" into `200000`.
4. **Clipping.** Two recordings peaked above 1.0 (too loud / too close to the mic). Accuracy was
   still fine, but phone audio will clip more often.
5. **Forcing `language="en"` translates instead of transcribing.** Whisper doesn't write Hindi in
   English letters; it translates it into English. That changes the caller's words, and in test 5 it
   turned "2 lakh" into "2,000,000,000", a 10,000× wrong budget. **Never force English for Hindi or
   Hinglish callers.**
6. **Forcing `language="hi"` gave the cleanest Hinglish** (test 7): mixed script, no translation.
   In this small test it beat auto-detect, which was inconsistent (tests 3 and 4). One sample isn't
   proof, so it needs more tests before deciding.
7. **First run downloads the model** (1.61 GB, one time). The first download froze and had to be
   restarted; the model then loaded from the local cache with 0 bytes downloaded.

## Impact on the bot

| Stage | Impact |
|---|---|
| Brain (LLM) | Low: the LLM can read Devanagari, mixed script and phonetic English |
| Field extraction | Medium: must normalise numbers and mixed scripts |
| Dashboard / transcripts | Medium: switching scripts makes transcripts harder to read and search |

## Next

- [x] Run forced-language tests (5–7)
- [ ] More Hinglish samples: auto-detect vs `language="hi"`, to confirm which is more reliable
- [ ] Measure transcription time per recording
- [ ] Repeat tests 1–4 with Sarvam (Saarika) in the later API lesson and compare accuracy and speed
