import sys
import uvicorn
from PySide6.QtCore import QThread, Signal
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MSA-API")

class ServerWorker(QThread):
    status_changed = Signal(str)
    error_occurred = Signal(str)

    def __init__(self, host="0.0.0.0", port=8000):
        super().__init__()
        self.host = host
        self.port = port
        self.server = None
        self._should_run = True

    def run(self):
        try:
            from api.main import app
            
            config = uvicorn.Config(
                app=app, 
                host=self.host, 
                port=self.port, 
                log_level="info",
                loop="asyncio"
            )
            self.server = uvicorn.Server(config)
            
            logger.info(f"Starting API server on {self.host}:{self.port}")
            self.status_changed.emit(f"Running on {self.host}:{self.port}")
            
            # Run the server
            self.server.run()
            
        except Exception as e:
            logger.error(f"API Server error: {e}")
            self.error_occurred.emit(str(e))
            self.status_changed.emit("Error")

    def stop(self):
        if not self.isRunning():
            return
            
        logger.info("Stopping API server...")
        self._should_run = False
        if self.server:
            self.server.should_exit = True
        
        # Wait for thread to finish gracefully with a timeout
        if not self.wait(5000):  # Wait up to 5 seconds
            logger.warning("API server did not stop gracefully, terminating...")
            self.terminate()
            self.wait()
            
        logger.info("API server stopped.")
