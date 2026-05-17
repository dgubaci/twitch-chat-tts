# 💬 Twitch Chat TTS Bot

This bot connects to Twitch chat and announces messages using Text-to-Speech (TTS). It reads out every message received in the configured channels, providing a fun and functional real-time announcement system for your stream!

## ✨ Features
- **Real-time Chat Listening:** Connects to specified Twitch channels.
- **Text-to-Speech Announcements:** Uses Google TTS (`gTTS`) to speak out chat messages.
- **Twitch Integration:** Built using the `twitchio` library for seamless interaction with the Twitch IRC network.

## 🛠️ Prerequisites
Before running this bot, ensure you have the following installed:
- Python 3.x
- A Twitch Developer Account and OAuth Token.

### Installation
1. **Install Libraries:**
   The required libraries are listed in `requirements.txt`. Run the following command in your terminal:
   ```bash
   pip install -r requirements.txt
   ```
2. **Ensure Dependencies:**
   Make sure all necessary dependencies (`twitchio`, `gTTS`, `pygame`, etc.) are installed and available in your environment.

## ⚙️ Configuration
You must update the following placeholder values in `text-to-speech.py`:

1. **`BOT_TOKEN`**:
   Replace `"$ACCESS_TOKEN_HERE"` with your actual Twitch Bot OAuth Token.
2. **`NICKNAME`**:
   Replace `"USERNAME_HERE"` with the desired nickname for the bot.
3. **`CHANNELS`**:
   Update the list with the channels you want the bot to monitor (e.g., `["yourchannelname", "anotherchannel"]`).

## 🚀 Usage
Once the configuration is complete, run the script from your terminal:

```bash
python text-to-speech.py
```

The bot will connect to Twitch and begin listening for chat messages.

### ⚠️ Important Notes
- **Speech Output:** The bot uses `pygame` and temporary MP3 files. It requires the necessary audio drivers to function correctly.
- **Permissions:** Ensure the bot account has the necessary permissions to join and read messages in the target channels.