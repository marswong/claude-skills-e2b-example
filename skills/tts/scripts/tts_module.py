#!/usr/bin/env python3
"""
TTS (Text-to-Speech) Module for ChatGPT Skills
Convert text to speech using Microsoft Edge TTS (free, high quality)

Usage:
    from tts_module import TTSClient

    tts = TTSClient()

    # Generate speech and save to file
    tts.speak("Hello, world!", output="hello.mp3")

    # Generate with different voice
    tts.speak("你好，世界！", voice="zh-CN-XiaoxiaoNeural", output="hello_cn.mp3")

    # List available voices
    voices = tts.list_voices()
    voices = tts.list_voices(language="zh")

    # Play directly (requires mpv/ffplay)
    tts.speak_and_play("This will play immediately")

Command Line:
    python3 tts_module.py speak "Hello, world!"
    python3 tts_module.py speak "你好" --voice zh-CN-XiaoxiaoNeural
    python3 tts_module.py speak "Hello" --output hello.mp3
    python3 tts_module.py speak "Hello" --play
    python3 tts_module.py voices
    python3 tts_module.py voices --language zh
"""

import asyncio
import os
import sys
import subprocess
import tempfile
from typing import Optional, List, Dict
from datetime import datetime

try:
    import edge_tts
    HAS_EDGE_TTS = True
except ImportError:
    HAS_EDGE_TTS = False
    print("Warning: edge-tts not installed. Run: pip3 install edge-tts")


class TTSClient:
    """Text-to-Speech client using Microsoft Edge TTS"""

    # Popular voices
    POPULAR_VOICES = {
        # English
        "en-us-female": "en-US-JennyNeural",
        "en-us-male": "en-US-GuyNeural",
        "en-gb-female": "en-GB-SoniaNeural",
        "en-gb-male": "en-GB-RyanNeural",
        # Chinese
        "zh-cn-female": "zh-CN-XiaoxiaoNeural",
        "zh-cn-male": "zh-CN-YunxiNeural",
        "zh-cn-news": "zh-CN-XiaoyiNeural",
        "zh-tw-female": "zh-TW-HsiaoChenNeural",
        # Japanese
        "ja-female": "ja-JP-NanamiNeural",
        "ja-male": "ja-JP-KeitaNeural",
        # Korean
        "ko-female": "ko-KR-SunHiNeural",
        "ko-male": "ko-KR-InJoonNeural",
        # Others
        "fr-female": "fr-FR-DeniseNeural",
        "de-female": "de-DE-KatjaNeural",
        "es-female": "es-ES-ElviraNeural",
    }

    def __init__(self, voice: str = "en-US-JennyNeural", rate: str = "+0%", volume: str = "+0%"):
        """
        Initialize TTS client

        Args:
            voice: Default voice name or alias (e.g., "en-us-female", "zh-cn-female")
            rate: Speech rate (e.g., "+10%", "-20%")
            volume: Volume adjustment (e.g., "+50%", "-10%")
        """
        if not HAS_EDGE_TTS:
            raise ImportError("edge-tts not installed. Run: pip3 install edge-tts")

        self.voice = self._resolve_voice(voice)
        self.rate = rate
        self.volume = volume

    def _resolve_voice(self, voice: str) -> str:
        """Resolve voice alias to full voice name"""
        return self.POPULAR_VOICES.get(voice.lower(), voice)

    def _normalize_rate(self, rate: str) -> str:
        """
        Normalize rate to edge-tts format (+XX% or -XX%)

        Accepts:
            - "+10%", "-20%" (edge-tts format, returned as-is)
            - "1.5", "0.8" (multiplier format, converted to percentage)
        """
        if rate is None:
            return self.rate

        rate_str = str(rate).strip()

        # Already in correct format
        if rate_str.endswith('%'):
            return rate_str

        # Try to parse as float (multiplier format)
        try:
            multiplier = float(rate_str)
            # Convert multiplier to percentage change
            # 1.0 = +0%, 1.5 = +50%, 0.8 = -20%
            percent = int((multiplier - 1.0) * 100)
            if percent >= 0:
                return f"+{percent}%"
            else:
                return f"{percent}%"
        except ValueError:
            # Return as-is if can't parse
            return rate_str

    async def _speak_async(
        self,
        text: str,
        output: str,
        voice: Optional[str] = None,
        rate: Optional[str] = None,
        volume: Optional[str] = None
    ) -> str:
        """Async method to generate speech"""
        voice = self._resolve_voice(voice) if voice else self.voice
        rate = self._normalize_rate(rate)
        volume = volume or self.volume

        communicate = edge_tts.Communicate(text, voice, rate=rate, volume=volume)
        await communicate.save(output)
        return output

    def speak(
        self,
        text: str,
        output: Optional[str] = None,
        voice: Optional[str] = None,
        rate: Optional[str] = None,
        volume: Optional[str] = None
    ) -> str:
        """
        Generate speech from text

        Args:
            text: Text to convert to speech
            output: Output file path (default: auto-generated)
            voice: Voice name or alias
            rate: Speech rate (e.g., "+10%", "-20%")
            volume: Volume adjustment

        Returns:
            Path to the generated audio file
        """
        if not output:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output = os.path.join(tempfile.gettempdir(), f"tts_{timestamp}.mp3")

        # Ensure output directory exists
        os.makedirs(os.path.dirname(output) if os.path.dirname(output) else ".", exist_ok=True)

        # Run async function (handle nested event loop)
        try:
            # Check if we're in a running event loop
            try:
                loop = asyncio.get_running_loop()
                # We're in an async context, need special handling
                import nest_asyncio
                nest_asyncio.apply()
            except RuntimeError:
                # No running loop, this is fine
                pass

            # Now safe to run
            asyncio.run(self._speak_async(text, output, voice, rate, volume))
        except Exception as e:
            # Fallback: create new loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self._speak_async(text, output, voice, rate, volume))
            finally:
                loop.close()

        return output

    def speak_and_play(
        self,
        text: str,
        voice: Optional[str] = None,
        rate: Optional[str] = None,
        volume: Optional[str] = None,
        player: str = "auto"
    ) -> bool:
        """
        Generate speech and play it immediately

        Args:
            text: Text to speak
            voice: Voice name or alias
            rate: Speech rate
            volume: Volume adjustment
            player: Audio player ("auto", "mpv", "ffplay", "afplay")

        Returns:
            True if played successfully
        """
        # Generate to temp file
        output = self.speak(text, voice=voice, rate=rate, volume=volume)

        # Find player
        if player == "auto":
            if sys.platform == "darwin":
                player = "afplay"
            elif self._command_exists("mpv"):
                player = "mpv"
            elif self._command_exists("ffplay"):
                player = "ffplay"
            else:
                print(f"Audio saved to: {output}")
                print("No audio player found. Install mpv or ffplay to play directly.")
                return False

        try:
            if player == "afplay":
                subprocess.run(["afplay", output], check=True)
            elif player == "mpv":
                subprocess.run(["mpv", "--no-video", output], check=True,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            elif player == "ffplay":
                subprocess.run(["ffplay", "-nodisp", "-autoexit", output], check=True,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                subprocess.run([player, output], check=True)

            # Clean up temp file
            if output.startswith(tempfile.gettempdir()):
                os.remove(output)

            return True
        except Exception as e:
            print(f"Failed to play audio: {e}")
            print(f"Audio saved to: {output}")
            return False

    def _command_exists(self, cmd: str) -> bool:
        """Check if a command exists"""
        try:
            subprocess.run(["which", cmd], check=True, capture_output=True)
            return True
        except:
            return False

    async def _list_voices_async(self) -> List[Dict]:
        """Async method to list voices"""
        voices = await edge_tts.list_voices()
        return voices

    def list_voices(self, language: Optional[str] = None) -> List[Dict]:
        """
        List available voices

        Args:
            language: Filter by language code (e.g., "zh", "en", "ja")

        Returns:
            List of voice dictionaries
        """
        voices = asyncio.run(self._list_voices_async())

        if language:
            language = language.lower()
            voices = [v for v in voices if v.get("Locale", "").lower().startswith(language)]

        return voices

    def get_popular_voices(self) -> Dict[str, str]:
        """Get dictionary of popular voice aliases"""
        return self.POPULAR_VOICES.copy()


def main():
    """Command line interface"""
    import argparse

    parser = argparse.ArgumentParser(description="TTS Module - ChatGPT Skills")
    subparsers = parser.add_subparsers(dest="command", help="Command")

    # Speak command
    speak_parser = subparsers.add_parser("speak", help="Convert text to speech")
    speak_parser.add_argument("text", help="Text to convert")
    speak_parser.add_argument("--voice", "-v", default="en-US-JennyNeural",
                             help="Voice name or alias")
    speak_parser.add_argument("--output", "-o", help="Output file path")
    speak_parser.add_argument("--rate", "-r", default="+0%", help="Speech rate (e.g., +10%)")
    speak_parser.add_argument("--volume", default="+0%", help="Volume (e.g., +50%)")
    speak_parser.add_argument("--play", "-p", action="store_true", help="Play after generating")

    # Voices command
    voices_parser = subparsers.add_parser("voices", help="List available voices")
    voices_parser.add_argument("--language", "-l", help="Filter by language (e.g., zh, en)")
    voices_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # Popular command
    popular_parser = subparsers.add_parser("popular", help="Show popular voice aliases")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    try:
        tts = TTSClient()

        if args.command == "speak":
            print(f"Generating speech...")
            print(f"  Voice: {tts._resolve_voice(args.voice)}")
            print(f"  Rate: {args.rate}")

            if args.play:
                success = tts.speak_and_play(
                    args.text,
                    voice=args.voice,
                    rate=args.rate,
                    volume=args.volume
                )
                if success:
                    print("Playback complete.")
            else:
                output = tts.speak(
                    args.text,
                    output=args.output,
                    voice=args.voice,
                    rate=args.rate,
                    volume=args.volume
                )
                print(f"Audio saved to: {output}")

        elif args.command == "voices":
            voices = tts.list_voices(language=args.language)

            if args.json:
                import json
                print(json.dumps(voices, indent=2))
            else:
                print(f"\nAvailable voices" + (f" ({args.language})" if args.language else "") + ":")
                print("=" * 60)
                for v in voices[:30]:  # Limit output
                    locale = v.get("Locale", "")
                    name = v.get("ShortName", "")
                    gender = v.get("Gender", "")
                    print(f"  {name:<35} {gender:<8} {locale}")
                if len(voices) > 30:
                    print(f"  ... and {len(voices) - 30} more")
                print(f"\nTotal: {len(voices)} voices")

        elif args.command == "popular":
            print("\nPopular voice aliases:")
            print("=" * 50)
            for alias, name in tts.get_popular_voices().items():
                print(f"  {alias:<20} -> {name}")
            print("\nUsage: --voice zh-cn-female")

    except ImportError as e:
        print(f"Error: {e}")
        print("Install with: pip3 install edge-tts")


if __name__ == "__main__":
    main()
