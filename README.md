# Twitch Chat TTS Bot

A Twitch IRC bot that reads chat messages aloud using text-to-speech. Supports two TTS backends — **Kokoro** (local, high-quality ONNX model) with automatic fallback to **gTTS** (Google Text-to-Speech via the internet). Includes profanity filtering, user blacklisting, emote stripping, and moderator voice controls.

---

## Features

- **Dual TTS backends** — Kokoro ONNX runs locally for low-latency, high-quality speech; gTTS serves as an automatic fallback
- **Profanity filtering** — Detects and censors bad words; announces violations without reading the offending content aloud
- **Ignore word stripping** — Strips Twitch emotes or other noise words before speaking
- **User blacklisting** — Mods/broadcasters can silence specific users with `!!blacklist <username>`
- **Voice switching** — Mods/broadcasters can change the Kokoro voice mid-stream with `!voice <voice_name>`
- **Smart name announcements** — Announces a chatter's name once, then suppresses it for 5 minutes to reduce repetition
- **Async playback** — Audio synthesis runs off the main event loop so chat is never blocked

---

## Requirements

- Python 3.9+
- A Twitch bot account and OAuth token
- Kokoro ONNX model files (optional but recommended — see [Setup](#setup))

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure the bot

Open `twitch-chat-tts.py` and update the constants near the top of the file:

| Constant | Description |
|---|---|
| `BOT_TOKEN` | OAuth token for your bot account (get one at [twitchapps.com/tmi](https://twitchapps.com/tmi/)) |
| `BOT_NICKNAME` | Your bot account's username |
| `CHANNELS` | List of channel names to join |

### 3. Set up Kokoro (optional)

Download the Kokoro ONNX model and voices file and place them in a `modelvoice/` folder next to the script:

```
modelvoice/
  kokoro-quant.onnx
  voices-v1.0.bin
```

The default paths can be changed via `KOKORO_MODEL_PATH` and `KOKORO_VOICES_PATH`. If Kokoro fails to load, the bot falls back to gTTS automatically.

### 4. Create filter files (optional)

These plain-text files go in the same directory as the script. Each entry is one word or phrase per line. Lines starting with `#` are treated as comments.

| File | Purpose |
|---|---|
| `bad-words.txt` | Words to detect and censor |
| `ignore-words.txt` | Words to strip silently before TTS (e.g. emotes) |
| `blacklist.txt` | Usernames to ignore entirely (auto-managed by the bot) |

---

## Running the Bot

```bash
python twitch-chat-tts.py
```

The bot will connect to Twitch, load the TTS engine, and announce itself in the channel. Stop it at any time with `Ctrl+C`.

---

## Chat Commands

These commands are only available to **moderators** and the **broadcaster**.

| Command | Description |
|---|---|
| `!!blacklist <username>` | Prevents a user's messages from being read aloud |
| `!voice <voice_name>` | Changes the active Kokoro TTS voice |
| `!ttsvoice <voice_name>` | Alias for `!voice` |

---

## Project Structure

```
twitch-chat-tts.py   # Main bot script
bad-words.txt        # Profanity filter list
ignore-words.txt     # Words to strip from TTS (emotes, etc.)
blacklist.txt        # Auto-managed list of silenced users
modelvoice/
  kokoro-quant.onnx  # Kokoro TTS model
  voices-v1.0.bin    # Kokoro voice pack
```

---

## Notes

- The bot token is currently hardcoded in the script. For production use, move it to an environment variable or a config file and **do not commit tokens to version control**.
- Kokoro ONNX requires compatible ONNX Runtime bindings — see the [kokoro-onnx](https://github.com/thewh1teagle/kokoro-onnx) project for details.
- Audio playback depends on `pygame`'s mixer, which requires a working audio device. On headless servers, you may need a virtual audio sink (e.g. PulseAudio with a null sink).
