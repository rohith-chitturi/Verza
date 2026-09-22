import re
import shutil
import subprocess
from typing import Any

from contracts.schemas.world import AudioClip, AudioContext, AudioSegment, AudioTrack
from core.telemetry.logging import get_logger

logger = get_logger("providers.ffmpeg.audio")


class AudioSegmentationProvider:
    """
    Real Provider implementation for Audio Segmentation using FFmpeg's silencedetect filter.
    """

    __version__: str = "1.0"

    def __init__(self):
        # Enforce fail-fast dependency check per M2 Real Media Understanding architecture
        if not shutil.which("ffmpeg"):
            raise RuntimeError(
                "ENVIRONMENT DEPENDENCY FAILURE: ffmpeg is not installed or not in PATH."
            )

    def segment_audio(self, media_path: str) -> AudioContext:
        logger.info("audio_segmentation_started", provider="ffmpeg", media_path=media_path)

        cmd = [
            "ffmpeg",
            "-i", media_path,
            "-af", "silencedetect=noise=-30dB:d=0.5",
            "-f", "null",
            "-"
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError as e:
            # Differentiate between a missing file/bad format and a crash
            if "No such file or directory" in e.stderr or "Invalid data found" in e.stderr:
                raise RuntimeError(
                    f"ENVIRONMENT / MEDIA INPUT FAILURE: Failed to open or decode media at {media_path}. "
                    f"Details: {e.stderr}"
                )
            raise RuntimeError(
                f"MEDIA PROCESSING FAILURE: FFmpeg segmentation crashed. "
                f"Details: {e.stderr}"
            )

        # Parse FFmpeg stderr for silence boundaries
        # Example FFmpeg stderr lines:
        # [silencedetect @ 0x...] silence_start: 1
        # [silencedetect @ 0x...] silence_end: 2 | silence_duration: 1
        stderr = result.stderr
        
        # We need the media duration to bound the final active segment
        duration = self._get_duration(media_path)

        silence_starts = []
        silence_ends = []

        for line in stderr.splitlines():
            if "silence_start:" in line:
                match = re.search(r"silence_start:\s+([\d\.]+)", line)
                if match:
                    silence_starts.append(float(match.group(1)))
            elif "silence_end:" in line:
                match = re.search(r"silence_end:\s+([\d\.]+)", line)
                if match:
                    silence_ends.append(float(match.group(1)))

        silences = []
        active_segments = []
        
        # Ensure parity between starts and ends
        for s_start, s_end in zip(silence_starts, silence_ends):
            silences.append((s_start, s_end))

        # Derive active audio regions by inversing the silence gaps
        current_time = 0.0
        for s_start, s_end in silences:
            if s_start > current_time:
                active_segments.append((current_time, s_start))
            current_time = s_end

        # Capture the final active segment if the audio doesn't end on silence
        if current_time < duration:
            active_segments.append((current_time, duration))

        # Map to AudioContext schema
        speech_clips = [
            AudioClip(start_s=start, end_s=end, content="ACTIVE_AUDIO") 
            for start, end in active_segments
        ]
        
        silence_clips = [
            AudioClip(start_s=start, end_s=end, content="SILENCE") 
            for start, end in silences
        ]

        # The AudioContext contract places ACTIVE_AUDIO into `speech_tracks` (representing non-silence)
        # Semantic mapping to actual language/speech happens in later cognitive M3 phases.
        speech_track = AudioTrack(segments=[AudioSegment(clips=speech_clips)]) if speech_clips else AudioTrack(segments=[])
        silence_track = AudioTrack(segments=[AudioSegment(clips=silence_clips)]) if silence_clips else AudioTrack(segments=[])

        return AudioContext(
            speech_tracks=[speech_track] if speech_track.segments else [],
            music_tracks=[],
            effects=[],
            ambience=[],
            silence=[silence_track] if silence_track.segments else [],
        )

    def _get_duration(self, media_path: str) -> float:
        """Helper to get exact duration in seconds using ffprobe."""
        cmd = [
            "ffprobe", 
            "-v", "error", 
            "-show_entries", "format=duration", 
            "-of", "default=noprint_wrappers=1:nokey=1", 
            media_path
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return float(result.stdout.strip())
        except (subprocess.CalledProcessError, ValueError):
            return 0.0

    def health(self) -> bool:
        return shutil.which("ffmpeg") is not None

    def capabilities(self) -> dict[str, Any]:
        return {"tracks": ["speech", "silence"], "real_execution": True}
