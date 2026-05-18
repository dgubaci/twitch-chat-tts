import asyncio
import twitchio
from twitchio.ext import commands
from gtts import gTTS
# Core libraries for ONNX audio synthesis
import numpy as np
from scipy.io.wavfile import write 
import pygame
import os
import re # Added for regex support
# Assuming the primary entry point for the library is this import
import kokoro_onnx


# --- Profanity filter setup ---

def load_bad_words(filepath="bad-words.txt"):
    try:
        with open(filepath, encoding="utf-8") as f:
            return {
                line.strip().lower()
                for line in f
                if line.strip() and not line.strip().startswith("#")
            }
    except FileNotFoundError:
        print(f"[WARNING] Bad words list not found at {filepath}. Profanity filter disabled.")
        return set()


def load_user_list(filepath="blacklist.txt"):
    try:
        with open(filepath, encoding="utf-8") as f:
            return {
                line.strip().lower()
                for line in f
                if line.strip() and not line.strip().startswith("#")
            }
    except FileNotFoundError:
        return set()


def save_user_list(filepath, user_set):
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            for user in sorted(user_set):
                f.write(f"{user}\n")
    except Exception as e:
        print(f"[WARNING] Could not save blacklist to {filepath}: {e}")


def filter_profanity(text, bad_words):
    if not text or not bad_words:
        return text

    pattern = re.compile(
        r"(?<!\w)(" + "|".join(re.escape(word) for word in bad_words) + r")(?!\w)",
        flags=re.IGNORECASE,
    )

    return pattern.sub(lambda match: "*" * len(match.group(0)), text)


def contains_profanity(text, bad_words):
    if not text or not bad_words:
        return False

    pattern = re.compile(
        r"(?<!\w)(" + "|".join(re.escape(word) for word in bad_words) + r")(?!\w)",
        flags=re.IGNORECASE,
    )

    return bool(pattern.search(text))


BLACKLIST_FILE = "blacklist.txt"
BLACKLISTED_USERS = load_user_list(BLACKLIST_FILE)
BAD_WORDS = load_bad_words()

# --- Configuration ---
BOT_TOKEN = "$ACCESS_TOKEN"
NICKNAME = "$BOT_USERNAME"
CHANNELS = ["$CHANNEL_NAME"]

KOKORO_MODEL_PATH = r"$DIRECTORY_TO_MODEL\kokoro-quant.onnx"
KOKORO_VOICES_PATH = r"$DIRECTORY_TO_VOICES\voices-v1.0.bin"
KOKORO_DEFAULT_VOICE = "af_heart"
CURRENT_VOICE = KOKORO_DEFAULT_VOICE

# --- TTS Model Initialization ---
# Global variable to hold the loaded model object
TTS_ENGINE = None
USE_KOKORO = False
USE_GTTS = True
AUDIO_AVAILABLE = False

def initialize_tts_engine():
    """Initializes the kokoro-onnx model globally on startup."""
    global TTS_ENGINE, USE_KOKORO
    try:
        print("[TTS SETUP] Initializing local Kokoro TTS model...")
        TTS_ENGINE = kokoro_onnx.Kokoro(
            model_path=KOKORO_MODEL_PATH,
            voices_path=KOKORO_VOICES_PATH,
        )
        USE_KOKORO = True
        print("[TTS SETUP] Kokoro TTS Model Loaded successfully.")

        try:
            if hasattr(TTS_ENGINE.voices, 'keys'):
                voice_names = list(TTS_ENGINE.voices.keys())
            elif isinstance(TTS_ENGINE.voices, np.ndarray):
                voice_names = [str(v) for v in TTS_ENGINE.voices]
            else:
                voice_names = [str(TTS_ENGINE.voices)]
            print(f"[TTS SETUP] Loaded voices ({len(voice_names)}): {voice_names}")
        except Exception as e:
            print(f"[TTS SETUP WARNING] Could not enumerate loaded voices: {e}")
    except Exception as e:
        print(f"[TTS SETUP ERROR] Could not load Kokoro TTS model. Audio features will be disabled. Error: {e}")
        TTS_ENGINE = None
        USE_KOKORO = False

try:
    pygame.mixer.init()
    AUDIO_AVAILABLE = True
except Exception as e:
    print(f"[AUDIO SETUP WARNING] Could not initialize pygame audio: {e}")
    AUDIO_AVAILABLE = False


def speak(text):
    """Saves TTS to a WAV file and plays it using pygame safely."""
    text = text.replace("_", " ")
    print(f"[TTS] Speaking: {text}")

    if not AUDIO_AVAILABLE:
        print("[TTS] Audio device is unavailable. Cannot speak.")
        return

    try:
        filename = "tts_temp.wav"

        if USE_KOKORO and TTS_ENGINE is not None:
            # Use the globally selected voice name (string) when available.
            voice_to_use = globals().get('CURRENT_VOICE', KOKORO_DEFAULT_VOICE)
            audio_samples, sample_rate = TTS_ENGINE.create(
                text,
                voice=voice_to_use,
                lang='en-us',
                speed=1.0,
                trim=True,
            )
            write(filename, sample_rate, audio_samples)
        elif USE_GTTS:
            tts = gTTS(text=text, lang='en', tld='com')
            tts.save(filename)
        else:
            print("[TTS] No TTS backend available.")
            return

        pygame.mixer.music.load(filename)
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

        pygame.mixer.music.unload()
        if os.path.exists(filename):
            os.remove(filename)

    except Exception as e:
        print(f"[TTS ERROR] Failed during synthesis or playback: {e}")

async def async_speak(text):
    await asyncio.to_thread(speak, text)

# --- Class Definition (TwitchIO v2 standard) ---
class TwitchBot(commands.Bot):
    def __init__(self):
        super().__init__(
            token=BOT_TOKEN,
            prefix="!",
            initial_channels=CHANNELS
        )

    async def event_ready(self):
        # Call the initializer when the bot is about to run
        initialize_tts_engine() 
        
        # self.nick is fully valid here in v2
        print(f'\n[BOT] Connection established! Logged in as: {self.nick}')
        print(f"[BOT] Joined channels: {self.connected_channels}")
        print(">>> CHAT LINE IS OPEN. TYPE IN TWITCH CHAT NOW! <<<\n")
        await async_speak("The text to speech bot is now online.")

    async def event_message(self, message):
        # ... (Rest of the event_message function remains identical) ...
        # Prevent the bot from reading its own messages
        if message.echo:
            return

        content = message.content.strip()
        lower_content = content.lower()
        author_name = message.author.name.lower()

        if lower_content.startswith("!!blacklist "):
            if not getattr(message.author, "is_mod", False) and author_name != CHANNELS[0].lower():
                await message.channel.send("Only moderators can add users to the blacklist.")
                return

            target_name = content.split(maxsplit=1)[1].strip().lstrip("@")
            if not target_name:
                await message.channel.send("Usage: !!blacklist <username>")
                return

            target_name = target_name.lower()
            if target_name == author_name:
                await message.channel.send("You cannot blacklist yourself.")
                return

            BLACKLISTED_USERS.add(target_name)
            save_user_list(BLACKLIST_FILE, BLACKLISTED_USERS)
            await message.channel.send(f"{target_name} has been blacklisted from TTS.")
            print(f"[BLACKLIST] {target_name} added by {message.author.name}")
            return

        # Moderators can change the TTS voice with !voice <voice_name>
        if lower_content.startswith("!voice ") or lower_content.startswith("!ttsvoice "):
            if not getattr(message.author, "is_mod", False) and author_name != CHANNELS[0].lower():
                await message.channel.send("Only moderators can change the TTS voice.")
                return

            desired = content.split(maxsplit=1)[1].strip()
            if not desired:
                await message.channel.send("Usage: !voice <voice_name>")
                return

            if USE_KOKORO and TTS_ENGINE is not None:
                try:
                    # Kokoro stores voices in a numpy archive; check available keys
                    available = []
                    if hasattr(TTS_ENGINE.voices, 'files'):
                        available = list(TTS_ENGINE.voices.files)
                    else:
                        try:
                            available = list(TTS_ENGINE.voices)
                        except Exception:
                            available = []
                    if desired in available:
                        globals()['CURRENT_VOICE'] = desired
                        await message.channel.send(f"TTS voice set to {desired}.")
                        print(f"[VOICE] Voice changed to {desired} by {message.author.name}")
                    else:
                        await message.channel.send(f"Voice '{desired}' not found. Use the registered voice name from the voices file.")
                except Exception as e:
                    await message.channel.send(f"Error checking voices: {e}")
            else:
                await message.channel.send("Kokoro voices are not available; cannot change voice.")

            return

        if author_name in BLACKLISTED_USERS:
            print(f"[BLACKLISTED] Ignoring message from {message.author.name}.")
            return
            
        if contains_profanity(message.content, BAD_WORDS):
            print(f"[CHAT CAUGHT] {message.author.name} used profanity.")
            announcement = f"Uh oh, {message.author.name} said a no-no word!"
        else:
            filtered_content = filter_profanity(message.content, BAD_WORDS)
            print(f"[CHAT CAUGHT] {message.author.name}: {filtered_content}")
            announcement = f"{message.author.name} said {filtered_content}"

        await async_speak(announcement)

        # Allow commands down the line to continue processing
        await self.handle_commands(message)

if __name__ == '__main__':
    bot = TwitchBot()
    print("Opening classic Twitch IRC network socket...")
    try:
        bot.run()
    except KeyboardInterrupt:
        print("\nShutting down.")
