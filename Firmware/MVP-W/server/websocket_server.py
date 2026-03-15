#!/usr/bin/env python3
"""
WebSocket Server for MVP-W Test Server
"""

import asyncio
import json
import base64
from datetime import datetime
from typing import Set, Callable, Optional

try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False


class WebSocketServer:
    """Async WebSocket server for ESP32-S3 device"""

    def __init__(self, host: str = '0.0.0.0', port: int = 8766):
        self.host = host
        self.port = port
        self.clients: Set = set()
        self.server = None
        self.running = False

        # Callbacks
        self.on_client_connected: Optional[Callable] = None
        self.on_client_disconnected: Optional[Callable] = None
        self.on_message: Optional[Callable] = None
        self.on_audio: Optional[Callable] = None

        # Audio playback
        if PYAUDIO_AVAILABLE:
            self.audio = pyaudio.PyAudio()
            self.audio_stream = None
        else:
            self.audio = None

    async def start(self):
        """Start the WebSocket server"""
        self.running = True
        self.server = await websockets.serve(
            self.host,
            self.port,
            self._handle_client
        )
        if self.on_server_started:
            self.on_server_started(self.port)

    async def stop(self):
        """Stop the WebSocket server"""
        self.running = False
        if self.server:
            self.server.close()
        if self.audio_stream:
            self.audio_stream.stop_stream()
            self.audio_stream = None
        if self.audio:
            self.audio.terminate()

    async def _handle_client(self, websocket, path):
        """Handle a client connection"""
        client_id = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        self.clients.add(websocket)

        if self.on_client_connected:
            self.on_client_connected(client_id)

        try:
            async for message in websocket:
                await self._process_message(websocket, client_id, message)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.clients.discard(websocket)
            if self.on_client_disconnected:
                self.on_client_disconnected(client_id)

    async def _process_message(self, websocket, client_id: str, message: str):
        """Process incoming message"""
        try:
            # Try to parse as JSON
            if message.startswith('{'):
                data = json.loads(message)
                msg_type = data.get('type', 'unknown')

                if msg_type == 'audio' or msg_type == 'audio_data':
                    # Handle audio data
                    audio_data = data.get('data')
                    if audio_data:
                        # Decode base64
                        raw_audio = base64.b64decode(audio_data)
                        if self.on_audio:
                            self.on_audio(client_id, len(raw_audio), raw_audio)
                        # Play audio
                        self._play_audio(raw_audio)
                else:
                    # Other JSON message
                    if self.on_message:
                        self.on_message(client_id, json.dumps(data))
            else:
                # Non-JSON message (might be binary audio)
                if self.on_audio:
                    self.on_audio(client_id, len(message), message.encode() if isinstance(message, str) else message)

        except json.JSONDecodeError:
            # Not JSON, treat as raw message
            if self.on_message:
                self.on_message(client_id, message)

    def _play_audio(self, data: bytes, sample_rate: int = 16000):
        """Play audio data through speakers"""
        if not PYAUDIO_AVAILABLE or not self.audio:
            return

        try:
            if self.audio_stream is None:
                self.audio_stream = self.audio.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=sample_rate,
                    output=True
                )
            self.audio_stream.write(data)
        except Exception as e:
            print(f"Audio playback error: {e}")

    async def broadcast(self, message: str):
        """Broadcast message to all clients"""
        if not self.clients:
            return

        # Create list to avoid modification during iteration
        clients = list(self.clients)
        for client in clients:
            try:
                await client.send(message)
            except Exception:
                pass

    async def send_to_client(self, websocket, message: str):
        """Send message to specific client"""
        try:
            await websocket.send(message)
        except Exception:
            pass

    @property
    def client_count(self) -> int:
        """Get number of connected clients"""
        return len(self.clients)
