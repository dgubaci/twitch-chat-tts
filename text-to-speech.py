import asyncio
import twitchio
from twitchio.ext import commands
from gtts import gTTS
import pygame
import os

# --- Configuration ---
BOT_TOKEN = "$ACCESS_TOKEN_HERE"
NICKNAME = "USERNAME_HERE"
CHANNELS = ["CHANNEL_NAME_HERE"]

pygame.mixer.init()

def speak(text):
    """Saves TTS to an MP3 and plays it using pygame safely."""
    print(f"[TTS] Speaking: {text}")
    try:
        filename = "tts_temp.mp3"
        tts = gTTS(text=text, lang='en', tld='com')
        tts.save(filename)
        
        pygame.mixer.music.load(filename)
        pygame.mixer.music.play()
        
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
            
        pygame.mixer.music.unload()
        if os.path.exists(filename):
            os.remove(filename)
            
    except Exception as e:
        print(f"[TTS ERROR] {e}")

async def async_speak(text):
    await asyncio.to_thread(speak, text)

# --- Class Definition (TwitchIO v2 standard) ---
class TwitchBot(commands.Bot):
    def __init__(self):
        # Clean, classic v2 constructor parameters
        super().__init__(
            token=BOT_TOKEN,
            prefix="!",
            initial_channels=CHANNELS
        )

    async def event_ready(self):
        # self.nick is fully valid here in v2
        print(f'\n[BOT] Connection established! Logged in as: {self.nick}')
        print(f"[BOT] Joined channels: {self.connected_channels}")
        print(">>> CHAT LINE IS OPEN. TYPE IN TWITCH CHAT NOW! <<<\n")
        await async_speak("The text to speech bot is now online.")

    async def event_message(self, message):
        # Prevent the bot from reading its own messages
        if message.echo:
            return
            
        print(f"[CHAT CAUGHT] {message.author.name}: {message.content}")
        
        announcement = f"{message.author.name} said {message.content}"
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