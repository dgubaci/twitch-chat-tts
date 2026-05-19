"""Twitch Chat to Text-to-Speech Bot using Kokoro or gTTS."""

import asyncio
import os
import re
import time
import logging
from pathlib import Path
from typing import Optional, Set

import numpy as np
import pygame
from scipy.io.wavfile import write
from gtts import gTTS
import twitchio
from twitchio.ext import commands

import kokoro_onnx


# ============================================================================
# CONFIGURATION & CONSTANTS
# ============================================================================

BOT_TOKEN = "$ACCESS_TOKEN"  # Replace with your Twitch bot token
BOT_NICKNAME = "$BOT_NICKNAME"
CHANNELS = ["$CHANNEL_NAME"]  # Replace with the channel(s) to join

KOKORO_MODEL_PATH = r"modelvoice\kokoro-quant.onnx"
KOKORO_VOICES_PATH = r"modelvoice\voices-v1.0.bin"
KOKORO_DEFAULT_VOICE = "af_heart"

BAD_WORDS_FILE = "bad-words.txt"
BLACKLIST_FILE = "blacklist.txt"
IGNORE_WORDS_FILE = "ignore-words.txt"
TTS_TEMP_FILE = "tts_temp.wav"
NAME_REPEAT_COOLDOWN_SECONDS = 5 * 60


# ============================================================================
# FILE MANAGEMENT
# ============================================================================

def load_bad_words(filepath: str = BAD_WORDS_FILE) -> Set[str]:
    """
    Load profanity words from a file.

    Args:
        filepath: Path to the bad words file.

    Returns:
        A set of lowercase profanity words.
    """
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


def load_ignore_words(filepath: str = IGNORE_WORDS_FILE) -> Set[str]:
    """
    Load words to strip from TTS output (e.g. emotes, spam).

    Args:
        filepath: Path to the ignore words file.

    Returns:
        A set of lowercase words to omit from speech.
    """
    try:
        with open(filepath, encoding="utf-8") as f:
            return {
                line.strip().lower()
                for line in f
                if line.strip() and not line.strip().startswith("#")
            }
    except FileNotFoundError:
        print(f"[WARNING] Ignore words list not found at {filepath}. Ignore filter disabled.")
        return set()


def load_user_list(filepath: str = BLACKLIST_FILE) -> Set[str]:
    """
    Load blacklisted usernames from a file.

    Args:
        filepath: Path to the blacklist file.

    Returns:
        A set of lowercase usernames.
    """
    try:
        with open(filepath, encoding="utf-8") as f:
            return {
                line.strip().lower()
                for line in f
                if line.strip() and not line.strip().startswith("#")
            }
    except FileNotFoundError:
        return set()


def save_user_list(filepath: str, user_set: Set[str]) -> None:
    """
    Save blacklisted usernames to a file.

    Args:
        filepath: Path to the blacklist file.
        user_set: Set of usernames to save.
    """
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            for user in sorted(user_set):
                f.write(f"{user}\n")
    except Exception as e:
        print(f"[WARNING] Could not save blacklist to {filepath}: {e}")


# ============================================================================
# PROFANITY FILTERING
# ============================================================================

def filter_profanity(text: str, bad_words: Set[str]) -> str:
    """
    Replace profanity words with asterisks.

    Args:
        text: The text to filter.
        bad_words: Set of words to filter.

    Returns:
        The filtered text with profanity replaced by asterisks.
    """
    if not text or not bad_words:
        return text

    pattern = re.compile(
        r"(?<!\w)(" + "|".join(re.escape(word) for word in bad_words) + r")(?!\w)",
        flags=re.IGNORECASE,
    )
    return pattern.sub(lambda match: "*" * len(match.group(0)), text)


def contains_profanity(text: str, bad_words: Set[str]) -> bool:
    """
    Check if text contains profanity.

    Args:
        text: The text to check.
        bad_words: Set of words to check for.

    Returns:
        True if profanity is detected, False otherwise.
    """
    if not text or not bad_words:
        return False

    pattern = re.compile(
        r"(?<!\w)(" + "|".join(re.escape(word) for word in bad_words) + r")(?!\w)",
        flags=re.IGNORECASE,
    )
    return bool(pattern.search(text))


def strip_ignored_words(text: str, ignore_words: Set[str]) -> str:
    """
    Remove ignore-list words from text before TTS.

    Args:
        text: The text to filter.
        ignore_words: Set of words to strip.

    Returns:
        Text with ignored words removed and whitespace normalized.
    """
    if not text or not ignore_words:
        return text

    pattern = re.compile(
        r"(?<!\w)(" + "|".join(re.escape(word) for word in ignore_words) + r")(?!\w)",
        flags=re.IGNORECASE,
    )
    result = pattern.sub("", text)
    return re.sub(r"\s+", " ", result).strip()


# ============================================================================
# GLOBAL STATE
# ============================================================================

BLACKLISTED_USERS: Set[str] = load_user_list(BLACKLIST_FILE)
BAD_WORDS: Set[str] = load_bad_words()
IGNORE_WORDS: Set[str] = load_ignore_words()

TTS_ENGINE = None
CURRENT_VOICE = KOKORO_DEFAULT_VOICE
USE_KOKORO = False
USE_GTTS = True
AUDIO_AVAILABLE = False



# ============================================================================
# TTS INITIALIZATION
# ============================================================================

def initialize_tts_engine() -> None:
    """Initialize the Kokoro TTS engine on startup."""
    global TTS_ENGINE, USE_KOKORO

    try:
        print("[TTS] Initializing Kokoro TTS model...")
        TTS_ENGINE = kokoro_onnx.Kokoro(
            model_path=KOKORO_MODEL_PATH,
            voices_path=KOKORO_VOICES_PATH,
        )
        USE_KOKORO = True
        print("[TTS] Kokoro model loaded successfully.")

        try:
            if hasattr(TTS_ENGINE.voices, "keys"):
                voice_names = list(TTS_ENGINE.voices.keys())
            elif isinstance(TTS_ENGINE.voices, np.ndarray):
                voice_names = [str(v) for v in TTS_ENGINE.voices]
            else:
                voice_names = [str(TTS_ENGINE.voices)]

            print(f"[TTS] Available voices ({len(voice_names)}): {voice_names}")
        except Exception as e:
            print(f"[TTS] Warning: Could not enumerate voices: {e}")
    except Exception as e:
        print(f"[TTS] Error: Could not load Kokoro model. Audio features disabled: {e}")
        TTS_ENGINE = None
        USE_KOKORO = False


def initialize_audio() -> None:
    """Initialize pygame audio mixer."""
    global AUDIO_AVAILABLE

    try:
        pygame.mixer.init()
        AUDIO_AVAILABLE = True
        print("[AUDIO] Pygame mixer initialized successfully.")
    except Exception as e:
        print(f"[AUDIO] Warning: Could not initialize mixer: {e}")
        AUDIO_AVAILABLE = False


# ============================================================================
# TEXT-TO-SPEECH
# ============================================================================

def speak(text: str) -> None:
    """
    Synthesize and play audio from text.

    Args:
        text: The text to convert to speech.
    """
    text = text.replace("_", " ")
    print(f"[TTS] Speaking: {text}")

    if not AUDIO_AVAILABLE:
        print("[TTS] Audio device unavailable.")
        return

    try:
        if USE_KOKORO and TTS_ENGINE is not None:
            audio_samples, sample_rate = TTS_ENGINE.create(
                text,
                voice=CURRENT_VOICE,
                lang="en-us",
                speed=1.0,
                trim=True,
            )
            write(TTS_TEMP_FILE, sample_rate, audio_samples)
        elif USE_GTTS:
            tts = gTTS(text=text, lang="en", tld="com")
            tts.save(TTS_TEMP_FILE)
        else:
            print("[TTS] No TTS backend available.")
            return

        pygame.mixer.music.load(TTS_TEMP_FILE)
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

        pygame.mixer.music.unload()
        if os.path.exists(TTS_TEMP_FILE):
            os.remove(TTS_TEMP_FILE)

    except Exception as e:
        print(f"[TTS] Error during synthesis or playback: {e}")


async def async_speak(text: str) -> None:
    """
    Asynchronously synthesize and play audio from text.

    Args:
        text: The text to convert to speech.
    """
    await asyncio.to_thread(speak, text)



# ============================================================================
# TWITCH BOT
# ============================================================================

class TwitchBot(commands.Bot):
    """Twitch IRC bot with text-to-speech capabilities."""

    def __init__(self):
        """Initialize the bot with token and channels."""
        super().__init__(token=BOT_TOKEN, prefix="!", initial_channels=CHANNELS)
        self.last_announced_user: Optional[str] = None
        self.last_name_announced_at: Optional[float] = None

    def _should_announce_name(self, author_name: str) -> bool:
        if self.last_announced_user != author_name:
            return True
        if self.last_name_announced_at is None:
            return True
        return time.monotonic() - self.last_name_announced_at >= NAME_REPEAT_COOLDOWN_SECONDS

    def _mark_name_announced(self, author_name: str) -> None:
        self.last_announced_user = author_name
        self.last_name_announced_at = time.monotonic()

    async def event_ready(self) -> None:
        """Handle bot startup and connection."""
        initialize_tts_engine()
        initialize_audio()

        print(f"\n[BOT] Connected as: {self.nick}")
        print(f"[BOT] Joined channels: {self.connected_channels}")
        print(">>> CHAT IS NOW LIVE <<<\n")

        await async_speak("The text to speech bot is now online.")

    async def _handle_blacklist_command(self, message: twitchio.Message) -> bool:
        """
        Handle the !!blacklist command to manage user blacklist.

        Args:
            message: The chat message.

        Returns:
            True if command was processed, False otherwise.
        """
        if not message.content.lower().startswith("!!blacklist "):
            return False

        is_mod = getattr(message.author, "is_mod", False)
        is_broadcaster = message.author.name.lower() == CHANNELS[0].lower()

        if not (is_mod or is_broadcaster):
            await message.channel.send("Only moderators can manage the blacklist.")
            return True

        target_name = message.content.split(maxsplit=1)[1].strip().lstrip("@").lower()

        if not target_name:
            await message.channel.send("Usage: !!blacklist <username>")
            return True

        if target_name == message.author.name.lower():
            await message.channel.send("You cannot blacklist yourself.")
            return True

        BLACKLISTED_USERS.add(target_name)
        save_user_list(BLACKLIST_FILE, BLACKLISTED_USERS)
        await message.channel.send(f"{target_name} has been blacklisted.")
        print(f"[BLACKLIST] {target_name} added by {message.author.name}")

        return True

    async def _handle_voice_command(self, message: twitchio.Message) -> bool:
        """
        Handle voice change command for moderators.

        Args:
            message: The chat message.

        Returns:
            True if command was processed, False otherwise.
        """
        content_lower = message.content.lower()
        if not (content_lower.startswith("!voice ") or content_lower.startswith("!ttsvoice ")):
            return False

        is_mod = getattr(message.author, "is_mod", False)
        is_broadcaster = message.author.name.lower() == CHANNELS[0].lower()

        if not (is_mod or is_broadcaster):
            await message.channel.send("Only moderators can change the voice.")
            return True

        desired_voice = message.content.split(maxsplit=1)[1].strip()

        if not desired_voice:
            await message.channel.send("Usage: !voice <voice_name>")
            return True

        if USE_KOKORO and TTS_ENGINE is not None:
            try:
                available_voices = []
                if hasattr(TTS_ENGINE.voices, "files"):
                    available_voices = list(TTS_ENGINE.voices.files)
                else:
                    try:
                        available_voices = list(TTS_ENGINE.voices)
                    except Exception:
                        available_voices = []

                if desired_voice in available_voices:
                    globals()["CURRENT_VOICE"] = desired_voice
                    await message.channel.send(f"Voice changed to {desired_voice}.")
                    print(f"[VOICE] Voice changed to {desired_voice} by {message.author.name}")
                else:
                    await message.channel.send(f"Voice '{desired_voice}' not found.")
            except Exception as e:
                await message.channel.send(f"Error changing voice: {e}")
        else:
            await message.channel.send("Kokoro voices are not available.")

        return True

    async def event_message(self, message: twitchio.Message) -> None:
        """
        Handle incoming chat messages.

        Args:
            message: The chat message from Twitch.
        """
        # Ignore bot's own messages
        if message.echo:
            return

        author_name = message.author.name.lower()
        content = message.content.strip()

        # Check for mod/broadcaster commands
        if await self._handle_blacklist_command(message):
            return

        if await self._handle_voice_command(message):
            return

        # Ignore blacklisted users
        if author_name in BLACKLISTED_USERS:
            print(f"[FILTERED] Ignoring blacklisted user: {author_name}")
            return

        # Process message for TTS
        include_name = self._should_announce_name(author_name)

        if contains_profanity(content, BAD_WORDS):
            print(f"[CHAT] {message.author.name}: [profanity detected]")
            if include_name:
                announcement = f"Uh oh, {message.author.name} said a word they shouldn't have!"
            else:
                announcement = "Uh oh, they said a word they shouldn't have!"
        else:
            filtered_content = filter_profanity(content, BAD_WORDS)
            print(f"[CHAT] {message.author.name}: {filtered_content}")
            tts_content = strip_ignored_words(filtered_content, IGNORE_WORDS)
            if not tts_content:
                print(f"[FILTERED] Message contained only ignored words.")
                return
            if include_name:
                announcement = f"{message.author.name} said: {tts_content}"
            else:
                announcement = tts_content

        if include_name:
            self._mark_name_announced(author_name)

        await async_speak(announcement)
        await self.handle_commands(message)


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    bot = TwitchBot()
    print("[BOT] Starting Twitch bot...")
    try:
        bot.run()
    except KeyboardInterrupt:
        print("\n[BOT] Shutting down.")
