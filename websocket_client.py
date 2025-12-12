"""
PCI Compliance Agent - WebSocket Client
Handles real-time communication with the server
"""

import logging
import socketio
import threading
import time
from typing import Callable, Optional
import json

logger = logging.getLogger(__name__)

class AgentWebSocketClient:
    """WebSocket client for real-time communication with the server"""
    
    def __init__(self, config: dict, agent_id: str):
        self.config = config
        self.agent_id = agent_id
        self.websocket_url = config.get('reporting', {}).get('websocket_url', 'http://192.168.56.1:3001')
        
        # Initialize SocketIO client
        self.sio = socketio.Client(
            reconnection=True,
            reconnection_attempts=5,
            reconnection_delay=2,
            logger=False,  # Disable socketio logging to avoid noise
            engineio_logger=False
        )
        
        # Callback handlers
        self.scan_command_handler: Optional[Callable] = None
        self.connected = False
        self.heartbeat_thread = None
        self.stop_heartbeat = False
        
        # Setup event handlers
        self._setup_event_handlers()
        
    def _setup_event_handlers(self):
        """Setup WebSocket event handlers"""
        
        @self.sio.event
        def connect():
            logger.info("Connected to WebSocket server")
            self.connected = True
            # Join the agent room for receiving commands
            self.sio.emit('join-agent', self.agent_id)
            # Start heartbeat
            self._start_heartbeat()
            
        @self.sio.event
        def disconnect():
            logger.info("Disconnected from WebSocket server")
            self.connected = False
            # Stop heartbeat
            self._stop_heartbeat()
            
        @self.sio.event
        def connect_error(data):
            logger.error(f"WebSocket connection error: {data}")
            self.connected = False
            self._stop_heartbeat()
        
        @self.sio.on('heartbeat-ack')
        def handle_heartbeat_ack(data):
            """Handle heartbeat acknowledgment from server"""
            logger.debug(f"Heartbeat acknowledged by server")
            
        @self.sio.on('scan-command')
        def handle_scan_command(data):
            """Handle scan commands from the server/GUI"""
            logger.info(f"Received scan command: {data}")
            
            if self.scan_command_handler:
                try:
                    self.scan_command_handler(data)
                except Exception as e:
                    logger.error(f"Error handling scan command: {e}")
                    self.emit_scan_error(str(e))
    
    def _start_heartbeat(self):
        """Start sending heartbeats to server every 30 seconds"""
        self.stop_heartbeat = False
        
        def send_heartbeat():
            while not self.stop_heartbeat and self.connected:
                try:
                    self.sio.emit('heartbeat', {
                        'agent_id': self.agent_id,
                        'timestamp': time.time()
                    })
                    logger.debug("Sent heartbeat to server")
                except Exception as e:
                    logger.error(f"Failed to send heartbeat: {e}")
                
                # Wait 30 seconds before next heartbeat
                for _ in range(30):
                    if self.stop_heartbeat:
                        break
                    time.sleep(1)
        
        self.heartbeat_thread = threading.Thread(target=send_heartbeat, daemon=True)
        self.heartbeat_thread.start()
        logger.info("Heartbeat thread started")
    
    def _stop_heartbeat(self):
        """Stop the heartbeat thread"""
        self.stop_heartbeat = True
        if self.heartbeat_thread:
            logger.info("Stopping heartbeat thread")
    
    def connect(self) -> bool:
        """Connect to the WebSocket server"""
        try:
            logger.info(f"Connecting to WebSocket server at {self.websocket_url}")
            self.sio.connect(self.websocket_url)
            
            # Wait a moment for connection to establish
            time.sleep(1)
            return self.connected
            
        except Exception as e:
            logger.error(f"Failed to connect to WebSocket server: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from the WebSocket server"""
        try:
            if self.connected:
                self.sio.disconnect()
                logger.info("Disconnected from WebSocket server")
        except Exception as e:
            logger.error(f"Error disconnecting from WebSocket: {e}")
    
    def set_scan_command_handler(self, handler: Callable):
        """Set the handler function for scan commands"""
        self.scan_command_handler = handler
    
    def emit_scan_progress(self, progress_data: dict):
        """Emit scan progress update to the server"""
        try:
            if self.connected:
                self.sio.emit('scan-progress', {
                    'agent_id': self.agent_id,
                    'progress': progress_data,
                    'timestamp': time.time()
                })
        except Exception as e:
            logger.error(f"Failed to emit scan progress: {e}")
    
    def emit_scan_completed(self, results: dict):
        """Emit scan completion notification"""
        try:
            if self.connected:
                self.sio.emit('scan-completed', {
                    'agent_id': self.agent_id,
                    'results': results,
                    'timestamp': time.time()
                })
        except Exception as e:
            logger.error(f"Failed to emit scan completion: {e}")
    
    def emit_scan_error(self, error_message: str):
        """Emit scan error notification"""
        try:
            if self.connected:
                self.sio.emit('scan-error', {
                    'agent_id': self.agent_id,
                    'error': error_message,
                    'timestamp': time.time()
                })
        except Exception as e:
            logger.error(f"Failed to emit scan error: {e}")
    
    def emit_scan_status(self, status: dict):
        """Emit current scan status"""
        try:
            if self.connected:
                self.sio.emit('scan-status-response', {
                    'agent_id': self.agent_id,
                    'status': status,
                    'timestamp': time.time()
                })
        except Exception as e:
            logger.error(f"Failed to emit scan status: {e}")
    
    def start_background_connection(self):
        """Start WebSocket client in background thread"""
        def run_client():
            try:
                self.connect()
                # Keep the connection alive
                self.sio.wait()
            except Exception as e:
                logger.error(f"WebSocket background thread error: {e}")
        
        thread = threading.Thread(target=run_client, daemon=True)
        thread.start()
        logger.info("WebSocket client started in background thread")
        return thread