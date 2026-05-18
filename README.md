# 💬 Twitch Chat to TTS Bot

A Twitch chat bot that reads messages aloud using Text-to-Speech (TTS). Every message in chat is announced in real-time, creating an interactive and entertaining stream experience.

## ✨ Features
- **Real-time Chat Reading:** Connects to Twitch and announces every message using TTS
- **Dual TTS Engines:** Uses local Kokoro ONNX for high-quality synthesis, with Google TTS (gTTS) fallback
- **Profanity Filtering:** Automatically filters profanity with customizable bad words list (`bad-words.txt`)
- **User Blacklist:** Moderators can blacklist users from TTS announcements with `!!blacklist <username>`
- **Voice Selection:** Moderators can change TTS voice with `!voice <voice_name>` or `!ttsvoice <voice_name>`
- **Moderation Commands:** Built-in commands for channel moderators to control bot behavior

## 🛠️ Prerequisites
- Python 3.8+
- Twitch Bot OAuth Token (from Twitch Developer Console)
- Kokoro ONNX model files and voices (optional, falls back to gTTS)
- Audio drivers and pygame mixer support

## 📦 Installation

1. **Clone/Download the repository**
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Optional - Set up Kokoro ONNX TTS** (for local synthesis):
   - Download the Kokoro model and voices files
   - Update `KOKORO_MODEL_PATH` and `KOKORO_VOICES_PATH` in `app.py`
   - If not available, the bot will fall back to Google TTS

## ⚙️ Configuration

Edit the following settings in `app.py`:

```python
BOT_TOKEN = "your_twitch_bot_token_here"
NICKNAME = "your_bot_username"
CHANNELS = ["target_channel_1", "target_channel_2"]

# Kokoro ONNX paths (optional)
KOKORO_MODEL_PATH = r"path/to/kokoro-quant.onnx"
KOKORO_VOICES_PATH = r"path/to/voices-v1.0.bin"
KOKORO_DEFAULT_VOICE = "af_heart"  # Default voice name
```

## 🚀 Usage

```bash
python app.py
```

The bot will connect to the specified channels and begin announcing chat messages.

### Chat Commands

**For Moderators Only:**
- `!!blacklist <username>` - Blacklist a user from TTS announcements
- `!voice <voice_name>` or `!ttsvoice <voice_name>` - Change the TTS voice

## 📋 Configuration Files

- **`bad-words.txt`** - List of profanity words to filter (one per line, lines starting with # are ignored)
- **`blacklist.txt`** - Automatically generated list of blacklisted users

## ⚠️ Important Notes

- The bot requires moderator permissions or channel owner status to use moderation commands
- Audio playback requires working audio drivers and pygame mixer initialization
- Profanity filtering uses regex word boundaries for accurate detection
- If Kokoro ONNX fails to load, the bot automatically falls back to Google TTS
- Temporary WAV files are created during TTS synthesis and automatically cleaned up