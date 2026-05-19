# Twitch Chat TTS Bot

A Twitch IRC bot that reads chat messages aloud using text-to-speech — **completely free and runs 100% locally on your machine.** No subscriptions, no cloud fees. Just run it and go live.

Supports two TTS backends: **Kokoro** (local ONNX model, high-quality, zero cost) with automatic fallback to **gTTS** (Google Text-to-Speech, free, requires internet). Includes profanity filtering, user blacklisting, emote stripping, and moderator voice controls.

---

## Why This Bot?

- **Free for streamers** — no paid TTS service, no monthly fees, no per-character charges
- **Local processing** — Kokoro runs entirely on your PC; your chat data never leaves your machine
- **No API keys required** — connect to Twitch with a free bot account token and you're done
- **Instant setup** — one script, one config section, five minutes to go live

---

## Features

- **Dual TTS backends** — Kokoro ONNX runs locally for low-latency, high-quality speech; gTTS serves as an automatic fallback
- **Profanity filtering** — detects and censors bad words; announces violations without reading the offending content aloud
- **Ignore word stripping** — strips Twitch emotes or other noise words before speaking
- **User blacklisting** — mods/broadcasters can silence specific users with `!!blacklist <username>`
- **Voice switching** — mods/broadcasters can change the Kokoro voice mid-stream with `!voice <voice_name>`
- **Smart name announcements** — announces a chatter's name once, then suppresses it for 5 minutes to reduce repetition
- **Async playback** — audio synthesis runs off the main event loop so chat is never blocked

---

## Requirements

- Python 3.9+
- A Twitch bot account and OAuth token (both free)
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
| `BOT_TOKEN` | OAuth token for your bot account — get one free at [twitchapps.com/tmi](https://twitchapps.com/tmi/) |
| `BOT_NICKNAME` | Your bot account's Twitch username |
| `CHANNELS` | List of channel names to join |

### 3. Set up Kokoro (optional but recommended)

Kokoro is a free, open-source TTS model that runs entirely on your machine — no internet required during use.

Download the model and voices file and place them in a `modelvoice/` folder next to the script:

```
modelvoice/
  kokoro-quant.onnx
  voices-v1.0.bin
```

The default paths can be changed via `KOKORO_MODEL_PATH` and `KOKORO_VOICES_PATH`. If Kokoro fails to load, the bot falls back to gTTS automatically (requires internet but is still free).

### 4. Create filter files (optional)

These plain-text files go in the same directory as the script. One entry per line; lines starting with `#` are comments.

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

The bot connects to Twitch, loads the TTS engine, and announces itself in the channel. Stop it at any time with `Ctrl+C`.

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
  kokoro-quant.onnx  # Kokoro TTS model (free, runs locally)
  voices-v1.0.bin    # Kokoro voice pack
```

---

## Cost Breakdown

| Component | Cost |
|---|---|
| Bot script | Free (open source) |
| Twitch bot account | Free |
| Kokoro TTS (primary) | Free — runs locally, no internet needed |
| gTTS fallback | Free — uses Google's public TTS endpoint |
| **Total** | **$0** |

---

## Notes

- The bot token is currently hardcoded in the script. For security, move it to an environment variable and **do not commit your token to version control**. Example: `BOT_TOKEN = os.environ.get("TWITCH_BOT_TOKEN", "")`
- Kokoro ONNX requires compatible ONNX Runtime bindings — see the [kokoro-onnx](https://github.com/thewh1teagle/kokoro-onnx) project for details.
- Audio playback depends on `pygame`'s mixer, which requires a working audio device. On headless servers, you may need a virtual audio sink (e.g. PulseAudio with a null sink).
