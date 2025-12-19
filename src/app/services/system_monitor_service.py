"""SystemMonitorService - Application Health and Performance Monitoring.

This service gathers system statistics including uptime, memory usage,
disk space, OS details, and database connectivity metrics.
"""

import os
import sys
import time
import shutil
import platform
from datetime import datetime
from typing import Dict, Any
from config.database import db


class SystemMonitorService:
    """Service class for System Monitoring metrics."""
    
    def __init__(self):
        """Initialize SystemMonitorService."""
        self.start_time = datetime.now()
        
    def get_system_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics.
        
        Returns:
            Dict containing uptime, memory, disk, system, and database stats.
        """
        return {
            "uptime": self._get_uptime(),
            "memory": self._get_memory_usage(),
            "disk": self._get_disk_usage(),
            "system": self._get_os_info(),
            "database": self._get_db_status()
        }

    def _get_uptime(self) -> Dict[str, Any]:
        """Calculate application uptime."""
        delta = datetime.now() - self.start_time
        days = delta.days
        hours, remainder = divmod(delta.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        return {
            "days": days,
            "hours": hours,
            "minutes": minutes,
            "seconds": seconds,
            "formatted": f"{days}d {hours}h {minutes}m {seconds}s",
            "start_time": self.start_time.strftime("%Y-%m-%d %H:%M:%S")
        }

    def _get_memory_usage(self) -> Dict[str, Any]:
        """Get memory usage (RSS) in MB.
        
        Attempts to use 'resource' module on Unix-like systems, falls back
        to 'psutil' if available, or returns zero if neither works.
        """
        try:
            # Using standard library resource module for Unix/Mac
            import resource
            usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            # MacOS returns in bytes, Linux in KB usually.
            # Python docs say: "on OS X ... expressed in bytes."
            if sys.platform == 'darwin':
                usage_mb = usage / (1024 * 1024)
            else:
                usage_mb = usage / 1024
        except ImportError:
            # Windows fallback or if resource module is missing
            try:
                import psutil
                process = psutil.Process(os.getpid())
                usage_mb = process.memory_info().rss / (1024 * 1024)
            except ImportError:
                # If neither is available, return 0
                return {"used_mb": 0, "status": "Unknown (Install psutil)"}
                
        return {
            "used_mb": round(usage_mb, 2),
            "status": "Normal" if usage_mb < 500 else "High"
        }

    def _get_disk_usage(self) -> Dict[str, Any]:
        """Get disk usage of the current volume."""
        try:
            total, used, free = shutil.disk_usage(".")
            
            total_gb = total / (1024**3)
            used_gb = used / (1024**3)
            free_gb = free / (1024**3)
            percent = (used / total) * 100
            
            return {
                "total_gb": round(total_gb, 2),
                "used_gb": round(used_gb, 2),
                "free_gb": round(free_gb, 2),
                "percent": round(percent, 1)
            }
        except Exception:
            return {"total_gb": 0, "used_gb": 0, "free_gb": 0, "percent": 0}

    def _get_os_info(self) -> Dict[str, str]:
        """Get OS Information."""
        return {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "processor": platform.processor(),
            "python_version": sys.version.split()[0]
        }
        
    def _get_db_status(self) -> Dict[str, Any]:
        """Check database connection and latency."""
        try:
            start = time.perf_counter()
            # Simple query to check connection
            db.execute_sql('SELECT 1')
            latency = (time.perf_counter() - start) * 1000 # ms
            
            # Get DB size (SQLite specific)
            db_size_mb = 0
            if hasattr(db, 'database'):
                try:
                    db_size_mb = os.path.getsize(db.database) / (1024 * 1024)
                except OSError:
                    pass
            
            return {
                "status": "Connected",
                "latency_ms": round(latency, 2),
                "size_mb": round(db_size_mb, 2),
                "path": db.database if hasattr(db, 'database') else "Unknown"
            }
        except Exception as e:
            return {
                "status": "Error",
                "latency_ms": 0,
                "error": str(e),
                "size_mb": 0,
                "path": "Unknown"
            }
