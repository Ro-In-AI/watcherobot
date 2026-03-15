#!/usr/bin/env python3
"""
MVP-W Test Server
Simple WebSocket server with GUI for testing audio streaming

Usage:
    python main.py [--host HOST] [--port PORT]

Requirements:
    pip install websockets PyQt6 pyaudio
    Optional: pip install opuslib (需要 opus.dll)
"""

import sys
import asyncio
import json
import base64
import argparse
import logging
import struct
import wave
import os
import tempfile
import subprocess
import shutil
import zlib
import random
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from collections import deque
from pathlib import Path

# Qt imports
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QTextEdit, QPushButton, QLabel,
                             QSlider, QGroupBox, QComboBox, QSpinBox,
                             QCheckBox)
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QTimer
from PyQt6.QtGui import QFont, QColor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Audio constants
SAMPLE_RATE = 16000
CHANNELS = 1
FRAME_DURATION_MS = 20  # Opus frame duration
FRAME_SIZE = SAMPLE_RATE * FRAME_DURATION_MS // 1000  # 320 samples per frame

# Get script directory for relative paths
SCRIPT_DIR = Path(__file__).parent.absolute()

# Try to import pyaudio
try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False
    logger.warning("pyaudio not available, audio playback disabled")

# Try to import opuslib for Opus decoding
try:
    from opuslib import Decoder as OpusDecoder
    OPUSLIB_AVAILABLE = True
except (ImportError, Exception) as e:
    OPUSLIB_AVAILABLE = False
    OpusDecoder = None
    logger.warning(f"opuslib not available: {e}")

# Check for opusdec.exe tool
OPUSDEC_PATH = SCRIPT_DIR / "opus-tools" / "opusdec.exe"
OPUSDEC_AVAILABLE = OPUSDEC_PATH.exists()
if OPUSDEC_AVAILABLE:
    logger.info(f"Found opusdec.exe at {OPUSDEC_PATH}")

# Overall Opus support
OPUS_AVAILABLE = OPUSLIB_AVAILABLE or OPUSDEC_AVAILABLE


class OggOpusWrapper:
    """Wrap raw Opus frames in Ogg container for opusdec.exe compatibility.

    Ogg Opus format: https://wiki.xiph.org/OggOpus
    """

    def __init__(self, sample_rate: int = SAMPLE_RATE, channels: int = CHANNELS):
        self.sample_rate = sample_rate
        self.channels = channels
        self.serial_number = 0x12345678  # Arbitrary serial number
        self.page_sequence = 0
        self.granule_position = 0
        self.preskip = 312  # Opus default preskip for 48kHz, scaled for 16kHz
        self.output_gain = 0
        self.channel_mapping_family = 0  # Mono/stereo only

    def _crc32_ogg(self, data: bytes) -> int:
        """Calculate Ogg CRC32 (polynomial 0x04C11DB7)"""
        # Ogg uses a specific CRC32 polynomial
        crc_table = []
        for i in range(256):
            crc = i << 24
            for _ in range(8):
                if crc & 0x80000000:
                    crc = (crc << 1) ^ 0x04C11DB7
                else:
                    crc <<= 1
                crc &= 0xFFFFFFFF
            crc_table.append(crc)

        crc = 0
        for byte in data:
            crc = ((crc << 8) ^ crc_table[((crc >> 24) ^ byte) & 0xFF]) & 0xFFFFFFFF
        return crc

    def _create_ogg_page(self, data: bytes, granule: int, bos: bool = False,
                         eos: bool = False) -> bytes:
        """Create an Ogg page with the given data."""
        # Ogg page header
        header = bytearray()

        # Capture pattern "OggS"
        header.extend(b'OggS')

        # Version (0)
        header.append(0)

        # Header type: bos=0x02, eos=0x04
        flags = 0
        if bos:
            flags |= 0x02
        if eos:
            flags |= 0x04
        header.append(flags)

        # Granule position (64-bit little-endian)
        header.extend(struct.pack('<Q', granule))

        # Serial number (32-bit)
        header.extend(struct.pack('<I', self.serial_number))

        # Page sequence number (32-bit)
        header.extend(struct.pack('<I', self.page_sequence))
        self.page_sequence += 1

        # CRC placeholder (will be filled later)
        crc_offset = len(header)
        header.extend(struct.pack('<I', 0))

        # Number of segments
        # Each segment is max 255 bytes, so we need to calculate segments
        remaining = len(data)
        segments = []
        while remaining > 0:
            seg_size = min(255, remaining)
            segments.append(seg_size)
            remaining -= seg_size

        header.append(len(segments))

        # Segment table
        for seg in segments:
            header.append(seg)

        # Combine header and data for CRC calculation
        page = bytes(header) + data

        # Calculate and insert CRC
        crc = self._crc32_ogg(page)
        page = page[:crc_offset] + struct.pack('<I', crc) + page[crc_offset + 4:]

        return page

    def _create_opus_header(self) -> bytes:
        """Create OpusHead packet."""
        header = bytearray()

        # "OpusHead"
        header.extend(b'OpusHead')

        # Version (1)
        header.append(1)

        # Channel count
        header.append(self.channels)

        # Pre-skip (16-bit little-endian)
        header.extend(struct.pack('<H', self.preskip))

        # Sample rate (32-bit little-endian)
        header.extend(struct.pack('<I', self.sample_rate))

        # Output gain (16-bit little-endian)
        header.extend(struct.pack('<H', self.output_gain))

        # Channel mapping family
        header.append(self.channel_mapping_family)

        return bytes(header)

    def _create_opus_tags(self) -> bytes:
        """Create OpusTags packet."""
        tags = bytearray()

        # "OpusTags"
        tags.extend(b'OpusTags')

        # Vendor string length and string
        vendor = b'MVP-W Test Server'
        tags.extend(struct.pack('<I', len(vendor)))
        tags.extend(vendor)

        # User comment list length (0 comments)
        tags.extend(struct.pack('<I', 0))

        return bytes(tags)

    def wrap_frames(self, opus_frames: List[bytes]) -> bytes:
        """Wrap multiple Opus frames into an Ogg Opus stream."""
        ogg_data = bytearray()

        # First page: OpusHead
        opus_header = self._create_opus_header()
        ogg_data.extend(self._create_ogg_page(opus_header, granule=0, bos=True))

        # Second page: OpusTags
        opus_tags = self._create_opus_tags()
        ogg_data.extend(self._create_ogg_page(opus_tags, granule=0))

        # Data pages: each Opus frame
        frame_samples = FRAME_SIZE  # 320 samples per 20ms frame at 16kHz
        for i, frame in enumerate(opus_frames):
            granule = self.granule_position + frame_samples
            is_last = (i == len(opus_frames) - 1)
            ogg_data.extend(self._create_ogg_page(frame, granule=granule, eos=is_last))
            self.granule_position = granule

        return bytes(ogg_data)

    def reset(self) -> None:
        """Reset wrapper state for new stream."""
        self.page_sequence = 0
        self.granule_position = 0


# Try to import websockets
try:
    import websockets
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    logger.error("websockets not available. Install with: pip install websockets")


class AudioPlayer:
    """Audio player with file-based Opus processing.

    For MVP, we save Opus frames to files and decode offline.
    This is simpler and doesn't require opus.dll for real-time decoding.
    """

    def __init__(self, sample_rate: int = SAMPLE_RATE, channels: int = CHANNELS) -> None:
        self.sample_rate = sample_rate
        self.channels = channels
        self.audio: Optional[pyaudio.PyAudio] = None
        self.stream: Optional[pyaudio.Stream] = None
        self.decode_mode = "save"  # "opuslib", "save"
        self.ogg_wrapper: Optional[OggOpusWrapper] = None
        self.frame_buffer: List[bytes] = []  # Buffer for file saving

        if PYAUDIO_AVAILABLE:
            self.audio = pyaudio.PyAudio()

        # Try opuslib for real-time decoding (optional)
        if OPUSLIB_AVAILABLE:
            try:
                self.opus_decoder = OpusDecoder(sample_rate, channels, 'int16')
                self.decode_mode = "opuslib"
                logger.info("Using opuslib for real-time Opus decoding")
            except Exception as e:
                logger.warning(f"opuslib init failed: {e}")
                self.opus_decoder = None

        # Setup Ogg wrapper for file saving
        if OPUSDEC_AVAILABLE:
            self.ogg_wrapper = OggOpusWrapper(sample_rate, channels)
            logger.info("Will save Opus to Ogg files for offline decoding")

        if self.decode_mode != "opuslib":
            logger.info("Opus frames will be saved to files for offline processing")

    def __enter__(self) -> 'AudioPlayer':
        """Enter context manager"""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        """Exit context manager - cleanup resources"""
        self.close()
        return False

    def play_wav(self, wav_file: str) -> bool:
        """Play a WAV file through PyAudio."""
        if not self.audio:
            logger.warning("PyAudio not available")
            return False

        try:
            with wave.open(wav_file, 'rb') as wf:
                stream = self.audio.open(
                    format=pyaudio.paInt16,
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True
                )
                data = wf.readframes(4096)
                while data:
                    stream.write(data)
                    data = wf.readframes(4096)
                stream.stop_stream()
                stream.close()
            return True
        except Exception as e:
            logger.error(f"Audio playback error: {e}")
            return False

    def close(self) -> None:
        """Close audio stream and release resources"""
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except Exception:
                pass
            self.stream = None
        if self.audio:
            try:
                self.audio.terminate()
            except Exception:
                pass
            self.audio = None


class AudioBuffer:
    """Buffer for collecting and processing audio frames"""

    def __init__(self, max_frames: int = 1000):
        self.frames: deque = deque(maxlen=max_frames)
        self.total_bytes = 0
        self.frame_count = 0

    def add_frame(self, data: bytes, is_opus: bool = True) -> None:
        """Add an audio frame to the buffer"""
        self.frames.append((data, is_opus))
        self.total_bytes += len(data)
        self.frame_count += 1

    def clear(self) -> None:
        """Clear the buffer"""
        self.frames.clear()
        self.total_bytes = 0
        self.frame_count = 0

    def get_stats(self) -> Dict[str, int]:
        """Get buffer statistics"""
        return {
            'frames': self.frame_count,
            'bytes': self.total_bytes
        }


class WebSocketThread(QThread):
    """WebSocket server running in background thread"""

    # Signals
    client_connected = pyqtSignal(str)
    client_disconnected = pyqtSignal(str)
    message_received = pyqtSignal(str, str)  # client_id, message
    audio_received = pyqtSignal(str, int, int)  # client_id, opus_bytes, pcm_bytes
    log_signal = pyqtSignal(str)
    server_started = pyqtSignal(int)
    server_stopped = pyqtSignal()

    def __init__(self, host: str = '0.0.0.0', port: int = 8766, save_audio: bool = False) -> None:
        super().__init__()
        self.host = host
        self.port = port
        self.running = False
        self.clients: Dict[Any, str] = {}
        self.audio_player = AudioPlayer()
        self.audio_buffer = AudioBuffer()
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.save_audio_files = save_audio  # Option to save audio to files

    async def handle_client(self, websocket: Any) -> None:
        """Handle a WebSocket client"""
        client_addr = websocket.remote_address
        client_id = f"{client_addr[0]}:{client_addr[1]}"
        self.clients[websocket] = client_id

        self.client_connected.emit(client_id)
        self.log_signal.emit(f"Client connected: {client_id}")

        try:
            async for message in websocket:
                await self.process_message(websocket, client_id, message)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            if websocket in self.clients:
                del self.clients[websocket]
            self.client_disconnected.emit(client_id)
            self.log_signal.emit(f"Client disconnected: {client_id}")

    async def process_message(self, websocket: Any, client_id: str, message: Any) -> None:
        """Process incoming message - handles both JSON strings and binary audio data"""
        # Handle binary data (AUD1 protocol or raw audio)
        if isinstance(message, bytes):
            await self._handle_binary_audio(client_id, message)
            return

        # Handle empty messages
        if not message:
            self.log_signal.emit(f"[{client_id}] Received empty message")
            return

        # Handle string messages (JSON)
        try:
            data = json.loads(message)
            msg_type = data.get('type', 'unknown')

            if msg_type == 'audio':
                # Handle audio data (base64 encoded in JSON)
                audio_b64 = data.get('data', '')
                if audio_b64:
                    try:
                        opus_data = base64.b64decode(audio_b64)
                        # Decode and play Opus
                        pcm_size = self._play_opus_frame(client_id, opus_data)
                        self.audio_received.emit(client_id, len(opus_data), pcm_size)
                    except Exception as e:
                        self.log_signal.emit(f"Audio decode error: {e}")

            elif msg_type == 'audio_end':
                self.log_signal.emit(f"[{client_id}] Audio stream ended")
                stats = self.audio_buffer.get_stats()
                self.log_signal.emit(f"[{client_id}] Total: {stats['frames']} frames, {stats['bytes']} bytes")

                # Echo back all buffered audio to ESP32 as TTS
                if self.audio_player.frame_buffer:
                    self._echo_audio_to_esp32(client_id, self.audio_player.frame_buffer, websocket)

                    # Optionally save to file for debugging
                    if self.save_audio_files:
                        output_file = self._save_opus_to_file(client_id, self.audio_player.frame_buffer)
                        if output_file:
                            self.log_signal.emit(f"[{client_id}] Saved: {output_file}")

                    self.audio_player.frame_buffer.clear()

            else:
                # Other message types
                self.message_received.emit(client_id, json.dumps(data, indent=2)[:500])

        except json.JSONDecodeError:
            # Not valid JSON, log as raw string
            self.log_signal.emit(f"[{client_id}] Non-JSON message: {str(message)[:200]}")
            self.message_received.emit(client_id, str(message)[:200])

    async def _handle_binary_audio(self, client_id: str, data: bytes) -> None:
        """Handle binary audio data with AUD1 protocol support

        Protocol format:
        - [0-3]   "AUD1" magic bytes
        - [4-7]   uint32_t data length (little-endian)
        - [8-n]   Opus encoded audio data
        """
        if len(data) < 8:
            self.log_signal.emit(f"[{client_id}] Binary message too short: {len(data)} bytes")
            return

        # Check magic bytes
        magic = data[:4]
        if magic == b'AUD1':
            # Parse AUD1 header
            payload_len = struct.unpack('<I', data[4:8])[0]
            opus_data = data[8:8 + payload_len]

            if len(opus_data) != payload_len:
                self.log_signal.emit(f"[{client_id}] Length mismatch: expected {payload_len}, got {len(opus_data)}")
                return

            # Decode and play Opus
            pcm_size = self._play_opus_frame(client_id, opus_data)
            self.audio_received.emit(client_id, payload_len, pcm_size)

        else:
            # Unknown format, try to play as raw PCM or Opus
            self.log_signal.emit(f"[{client_id}] Unknown binary format, trying Opus decode")
            pcm_size = self._play_opus_frame(client_id, data)
            self.audio_received.emit(client_id, len(data), pcm_size)

    def _play_opus_frame(self, client_id: str, opus_data: bytes) -> int:
        """Buffer Opus frame for later echo. Returns expected PCM bytes."""
        # Buffer the frame
        self.audio_buffer.add_frame(opus_data, is_opus=True)
        self.audio_player.frame_buffer.append(opus_data)
        # Return expected PCM size (320 samples * 2 bytes = 640 bytes)
        return FRAME_SIZE * 2

    def _echo_audio_to_esp32(self, client_id: str, opus_frames: List[bytes], websocket: Any) -> None:
        """Echo audio back to ESP32 as binary AUD1 frames.

        Protocol (binary, no JSON):
        - [0-3]   "AUD1" magic bytes
        - [4-7]   uint32_t data length (little-endian)
        - [8-n]   Opus encoded audio data
        """
        try:
            frame_count = len(opus_frames)
            self.log_signal.emit(f"[{client_id}] Echoing {frame_count} frames back to ESP32 (binary AUD1)...")

            sent_count = 0
            for i, frame in enumerate(opus_frames):
                # Build AUD1 binary frame
                frame_len = len(frame)
                aud1_frame = bytearray()
                aud1_frame.extend(b'AUD1')  # Magic bytes
                aud1_frame.extend(struct.pack('<I', frame_len))  # Length (little-endian)
                aud1_frame.extend(frame)  # Opus data

                # Send as binary frame
                asyncio.run_coroutine_threadsafe(
                    websocket.send(bytes(aud1_frame)),
                    self.loop
                )
                sent_count += 1

            self.log_signal.emit(f"[{client_id}] Echo complete: {sent_count} binary frames sent")

        except Exception as e:
            self.log_signal.emit(f"[{client_id}] Echo error: {e}")

    def _save_opus_to_file(self, client_id: str, opus_frames: List[bytes]) -> Optional[str]:
        """Save Opus frames to an Ogg Opus file for offline processing."""
        try:
            # Create output directory
            output_dir = SCRIPT_DIR / "recordings"
            output_dir.mkdir(exist_ok=True)

            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_client = client_id.replace(":", "_").replace(".", "_")
            output_file = output_dir / f"{timestamp}_{safe_client}.opus"

            # Wrap frames in Ogg container
            if self.audio_player.ogg_wrapper:
                self.audio_player.ogg_wrapper.reset()
                ogg_data = self.audio_player.ogg_wrapper.wrap_frames(opus_frames)
                with open(output_file, 'wb') as f:
                    f.write(ogg_data)
                return str(output_file)
            else:
                # Fallback: save raw frames (for debugging)
                raw_file = output_dir / f"{timestamp}_{safe_client}.raw"
                with open(raw_file, 'wb') as f:
                    for frame in opus_frames:
                        f.write(frame)
                return str(raw_file)

        except Exception as e:
            self.log_signal.emit(f"Error saving file: {e}")
            return None

    def _decode_opus_file(self, opus_file: str) -> Optional[str]:
        """Decode an Ogg Opus file to WAV using opusdec.exe."""
        if not OPUSDEC_AVAILABLE:
            return None

        try:
            wav_file = opus_file.rsplit('.', 1)[0] + '.wav'
            result = subprocess.run(
                [str(OPUSDEC_PATH), '--rate', str(SAMPLE_RATE), opus_file, wav_file],
                capture_output=True,
                timeout=30
            )

            if result.returncode == 0 and os.path.exists(wav_file):
                return wav_file
            else:
                error = result.stderr.decode() if result.stderr else "unknown error"
                self.log_signal.emit(f"opusdec error: {error}")
                return None

        except Exception as e:
            self.log_signal.emit(f"Decode error: {e}")
            return None

    def _play_wav_file(self, wav_file: str) -> bool:
        """Play a WAV file through PyAudio."""
        return self.audio_player.play_wav(wav_file)

    async def async_main(self) -> None:
        """Main async function"""
        self.running = True

        try:
            async with websockets.serve(self.handle_client, self.host, self.port):
                self.server_started.emit(self.port)
                self.log_signal.emit(f"Server started on ws://{self.host}:{self.port}")
                while self.running:
                    await asyncio.sleep(0.1)
        except Exception as e:
            self.log_signal.emit(f"Server error: {e}")
        finally:
            self.server_stopped.emit()

    def run(self) -> None:
        """Run the thread"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self.async_main())
        finally:
            self.loop.close()

    def stop(self) -> None:
        """Stop the server"""
        self.running = False
        self.audio_player.close()

    async def broadcast(self, message: str) -> None:
        """Broadcast message to all clients"""
        if not self.clients:
            return
        for ws in list(self.clients.keys()):
            try:
                await ws.send(message)
            except websockets.exceptions.ConnectionClosed:
                pass  # Expected - client disconnected
            except Exception as e:
                self.log_signal.emit(f"Broadcast error: {e}")


class MainWindow(QMainWindow):
    """Main application window"""

    def __init__(self, host: str = '0.0.0.0', port: int = 8766) -> None:
        super().__init__()
        self.host = host
        self.port = port
        self.ws_thread: Optional[WebSocketThread] = None

        self.setWindowTitle("MVP-W Test Server")
        self.setMinimumSize(700, 550)

        # Stats
        self.audio_packets = 0
        self.opus_bytes = 0
        self.pcm_bytes = 0

        # Servo random test
        self.servo_random_running = False
        self.servo_random_count = 0
        self.servo_random_timer = QTimer()
        self.servo_random_timer.timeout.connect(self.send_random_servo)

        self.setup_ui()

    def setup_ui(self) -> None:
        """Setup the UI"""
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Server control
        server_group = QGroupBox("Server Control")
        server_layout = QHBoxLayout(server_group)

        self.start_btn = QPushButton("Start Server")
        self.start_btn.clicked.connect(self.start_server)
        server_layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton("Stop Server")
        self.stop_btn.clicked.connect(self.stop_server)
        self.stop_btn.setEnabled(False)
        server_layout.addWidget(self.stop_btn)

        self.status_label = QLabel("Stopped")
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        server_layout.addWidget(self.status_label)

        self.client_label = QLabel("Clients: 0")
        server_layout.addWidget(self.client_label)

        layout.addWidget(server_group)

        # Test commands
        cmd_group = QGroupBox("Test Commands")
        cmd_layout = QHBoxLayout(cmd_group)

        self.servo_btn = QPushButton("Send Servo Cmd")
        self.servo_btn.clicked.connect(self.send_servo_command)
        self.servo_btn.setEnabled(False)
        cmd_layout.addWidget(self.servo_btn)

        self.display_btn = QPushButton("Send Display Cmd")
        self.display_btn.clicked.connect(self.send_display_command)
        self.display_btn.setEnabled(False)
        cmd_layout.addWidget(self.display_btn)

        self.status_btn = QPushButton("Send Status Cmd")
        self.status_btn.clicked.connect(self.send_status_command)
        self.status_btn.setEnabled(False)
        cmd_layout.addWidget(self.status_btn)

        layout.addWidget(cmd_group)

        # Servo random sequence test
        servo_group = QGroupBox("Servo Random Sequence Test")
        servo_layout = QHBoxLayout(servo_group)

        self.servo_random_btn = QPushButton("Start Random")
        self.servo_random_btn.clicked.connect(self.toggle_servo_random)
        self.servo_random_btn.setEnabled(False)
        self.servo_random_btn.setCheckable(True)
        servo_layout.addWidget(self.servo_random_btn)

        # Interval control
        servo_layout.addWidget(QLabel("Interval(ms):"))
        self.servo_interval_spin = QSpinBox()
        self.servo_interval_spin.setRange(100, 5000)
        self.servo_interval_spin.setValue(500)
        self.servo_interval_spin.setSingleStep(100)
        servo_layout.addWidget(self.servo_interval_spin)

        # X range
        servo_layout.addWidget(QLabel("X:"))
        self.servo_x_min = QSpinBox()
        self.servo_x_min.setRange(0, 180)
        self.servo_x_min.setValue(30)
        servo_layout.addWidget(self.servo_x_min)
        servo_layout.addWidget(QLabel("-"))
        self.servo_x_max = QSpinBox()
        self.servo_x_max.setRange(0, 180)
        self.servo_x_max.setValue(150)
        servo_layout.addWidget(self.servo_x_max)

        # Y range
        servo_layout.addWidget(QLabel("Y:"))
        self.servo_y_min = QSpinBox()
        self.servo_y_min.setRange(0, 180)
        self.servo_y_min.setValue(30)
        servo_layout.addWidget(self.servo_y_min)
        servo_layout.addWidget(QLabel("-"))
        self.servo_y_max = QSpinBox()
        self.servo_y_max.setRange(0, 180)
        self.servo_y_max.setValue(150)
        servo_layout.addWidget(self.servo_y_max)

        # Counter
        self.servo_count_label = QLabel("Count: 0")
        servo_layout.addWidget(self.servo_count_label)

        layout.addWidget(servo_group)

        # Audio stats
        audio_group = QGroupBox("Audio Statistics (Opus → PCM)")
        audio_layout = QHBoxLayout(audio_group)

        self.packets_label = QLabel("Frames: 0")
        audio_layout.addWidget(self.packets_label)

        self.opus_label = QLabel("Opus: 0 B")
        audio_layout.addWidget(self.opus_label)

        self.pcm_label = QLabel("PCM: 0 B")
        audio_layout.addWidget(self.pcm_label)

        self.reset_btn = QPushButton("Reset")
        self.reset_btn.clicked.connect(self.reset_stats)
        audio_layout.addWidget(self.reset_btn)

        layout.addWidget(audio_group)

        # Codec status
        codec_group = QGroupBox("Audio Processing")
        codec_layout = QHBoxLayout(codec_group)

        # Show processing mode
        if OPUSLIB_AVAILABLE:
            mode_text = "opuslib (real-time) ✅"
            mode_tip = "Using libopus DLL for instant decoding"
        elif OPUSDEC_AVAILABLE:
            mode_text = "opusdec.exe (offline) ✅"
            mode_tip = "Saving to file, then decoding with opusdec.exe"
        else:
            mode_text = "save only ⚠️"
            mode_tip = "Saving raw Opus frames - need external decoder"

        self.codec_mode_label = QLabel(f"Mode: {mode_text}")
        self.codec_mode_label.setToolTip(mode_tip)
        codec_layout.addWidget(self.codec_mode_label)

        pyaudio_status = "✅" if PYAUDIO_AVAILABLE else "❌"
        self.pyaudio_status_label = QLabel(f"PyAudio: {pyaudio_status}")
        codec_layout.addWidget(self.pyaudio_status_label)

        # Show recordings directory
        recordings_dir = SCRIPT_DIR / "recordings"
        dir_label = QLabel(f"📁 recordings/")
        dir_label.setToolTip(str(recordings_dir))
        codec_layout.addWidget(dir_label)

        layout.addWidget(codec_group)

        # Log
        log_group = QGroupBox("Log")
        log_layout = QVBoxLayout(log_group)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        log_layout.addWidget(self.log_text)

        self.clear_btn = QPushButton("Clear Log")
        self.clear_btn.clicked.connect(lambda: self.log_text.clear())
        log_layout.addWidget(self.clear_btn)

        layout.addWidget(log_group)

    def start_server(self) -> None:
        """Start WebSocket server"""
        if not WEBSOCKETS_AVAILABLE:
            self.add_log("Error: websockets library not available")
            return

        # Create server with echo mode (audio files saved for debugging)
        self.ws_thread = WebSocketThread(self.host, self.port, save_audio=True)
        self.ws_thread.client_connected.connect(self.on_client_connected)
        self.ws_thread.client_disconnected.connect(self.on_client_disconnected)
        self.ws_thread.message_received.connect(self.on_message_received)
        self.ws_thread.audio_received.connect(self.on_audio_received)
        self.ws_thread.log_signal.connect(self.add_log)
        self.ws_thread.server_started.connect(self.on_server_started)
        self.ws_thread.server_stopped.connect(self.on_server_stopped)

        self.ws_thread.start()

        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

    def stop_server(self) -> None:
        """Stop WebSocket server"""
        if self.ws_thread:
            self.ws_thread.stop()
            self.ws_thread.wait(2000)

        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

    def on_server_started(self, port: int) -> None:
        """Handle server started"""
        self.status_label.setText(f"Running on :{port}")
        self.status_label.setStyleSheet("color: green; font-weight: bold;")
        self.servo_btn.setEnabled(True)
        self.display_btn.setEnabled(True)
        self.status_btn.setEnabled(True)
        self.servo_random_btn.setEnabled(True)

    def on_server_stopped(self) -> None:
        """Handle server stopped"""
        self.status_label.setText("Stopped")
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        self.client_label.setText("Clients: 0")
        self.servo_btn.setEnabled(False)
        self.display_btn.setEnabled(False)
        self.status_btn.setEnabled(False)
        self.servo_random_btn.setEnabled(False)
        # Stop random test if running
        if self.servo_random_running:
            self.toggle_servo_random()

    def on_client_connected(self, client_id: str) -> None:
        """Handle client connection"""
        self.add_log(f"✅ Connected: {client_id}")
        self.update_client_count()

    def on_client_disconnected(self, client_id: str) -> None:
        """Handle client disconnection"""
        self.add_log(f"❌ Disconnected: {client_id}")
        self.update_client_count()

    def update_client_count(self) -> None:
        """Update client count label"""
        if self.ws_thread:
            count = len(self.ws_thread.clients)
            self.client_label.setText(f"Clients: {count}")

    def on_message_received(self, client_id: str, message: str) -> None:
        """Handle received message"""
        self.add_log(f"[{client_id}] {message}")

    def on_audio_received(self, client_id: str, opus_size: int, pcm_size: int) -> None:
        """Handle received audio with Opus and PCM byte counts"""
        self.audio_packets += 1
        self.opus_bytes += opus_size
        self.pcm_bytes += pcm_size

        self.packets_label.setText(f"Frames: {self.audio_packets}")
        self.opus_label.setText(f"Opus: {self.opus_bytes:,} B")
        self.pcm_label.setText(f"PCM: {self.pcm_bytes:,} B")

        # Log every 10 frames
        if self.audio_packets % 10 == 0:
            ratio = self.pcm_bytes / self.opus_bytes if self.opus_bytes > 0 else 0
            self.add_log(f"[{client_id}] {self.audio_packets} frames, compression: {ratio:.1f}x")

    def reset_stats(self) -> None:
        """Reset audio statistics"""
        self.audio_packets = 0
        self.opus_bytes = 0
        self.pcm_bytes = 0
        self.packets_label.setText("Frames: 0")
        self.opus_label.setText("Opus: 0 B")
        self.pcm_label.setText("PCM: 0 B")

    def send_servo_command(self) -> None:
        """Send servo test command"""
        msg = json.dumps({"type": "servo", "code": 0, "data": {"x": 90, "y": 120}})
        self.send_command(msg)

    def send_display_command(self) -> None:
        """Send display test command"""
        msg = json.dumps({"type": "display", "text": "Hello from PC!", "emoji": "happy", "size": 24})
        self.send_command(msg)

    def send_status_command(self) -> None:
        """Send status test command"""
        msg = json.dumps({"type": "status", "state": "thinking", "message": "Processing audio..."})
        self.send_command(msg)

    def send_command(self, msg: str) -> None:
        """Send command to all clients"""
        if self.ws_thread and self.ws_thread.loop:
            asyncio.run_coroutine_threadsafe(
                self.ws_thread.broadcast(msg),
                self.ws_thread.loop
            )
            self.add_log(f"Sent: {msg[:100]}")

    def toggle_servo_random(self) -> None:
        """Toggle servo random sequence test"""
        if self.servo_random_running:
            # Stop
            self.servo_random_running = False
            self.servo_random_timer.stop()
            self.servo_random_btn.setText("Start Random")
            self.servo_random_btn.setChecked(False)
            self.add_log(f"Servo random test stopped (sent {self.servo_random_count} commands)")
        else:
            # Start
            self.servo_random_running = True
            self.servo_random_count = 0
            interval = self.servo_interval_spin.value()
            self.servo_random_timer.start(interval)
            self.servo_random_btn.setText("Stop Random")
            self.servo_random_btn.setChecked(True)
            self.add_log(f"Servo random test started (interval: {interval}ms)")

    def send_random_servo(self) -> None:
        """Send a random servo command"""
        # Get range from UI
        x_min = self.servo_x_min.value()
        x_max = self.servo_x_max.value()
        y_min = self.servo_y_min.value()
        y_max = self.servo_y_max.value()

        # Ensure min <= max
        if x_min > x_max:
            x_min, x_max = x_max, x_min
        if y_min > y_max:
            y_min, y_max = y_max, y_min

        # Generate random positions
        x = random.randint(x_min, x_max)
        y = random.randint(y_min, y_max)

        # Send command with v2.0 protocol format
        msg = json.dumps({"type": "servo", "code": 0, "data": {"x": x, "y": y}})

        if self.ws_thread and self.ws_thread.loop:
            asyncio.run_coroutine_threadsafe(
                self.ws_thread.broadcast(msg),
                self.ws_thread.loop
            )

            self.servo_random_count += 1
            self.servo_count_label.setText(f"Count: {self.servo_random_count}")

            # Log every 5 commands
            if self.servo_random_count % 5 == 0:
                self.add_log(f"Servo #{self.servo_random_count}: X={x}° Y={y}°")

        # Update interval if changed
        current_interval = self.servo_interval_spin.value()
        if self.servo_random_timer.interval() != current_interval:
            self.servo_random_timer.setInterval(current_interval)

    def add_log(self, message: str) -> None:
        """Add log message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")

    def closeEvent(self, event: Any) -> None:
        """Handle window close"""
        # Stop servo random test if running
        if self.servo_random_running:
            self.servo_random_timer.stop()
            self.servo_random_running = False
        self.stop_server()
        event.accept()


def main() -> int:
    """Main entry point"""
    parser = argparse.ArgumentParser(description='MVP-W Test Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8766, help='Port to listen on')
    args = parser.parse_args()

    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    window = MainWindow(args.host, args.port)
    window.show()

    return app.exec()


if __name__ == '__main__':
    main()
