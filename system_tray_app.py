#!/usr/bin/env python3
"""
Media Management System Tray Application
Provides visual indicator and quick controls for the Windows service
"""

import sys
import os
import subprocess
import webbrowser
import threading
import time
from pathlib import Path

try:
    from PyQt5.QtWidgets import (QApplication, QSystemTrayIcon, QMenu, QAction, 
                                  QMessageBox, QDialog, QVBoxLayout, QLabel, 
                                  QTextEdit, QPushButton)
    from PyQt5.QtGui import QIcon, QPixmap, QColor
    from PyQt5.QtCore import QTimer, pyqtSignal, QObject
except ImportError:
    print("PyQt5 not installed. Installing...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "PyQt5"])
    from PyQt5.QtWidgets import (QApplication, QSystemTrayIcon, QMenu, QAction, 
                                  QMessageBox, QDialog, QVBoxLayout, QLabel, 
                                  QTextEdit, QPushButton)
    from PyQt5.QtGui import QIcon, QPixmap, QColor
    from PyQt5.QtCore import QTimer, pyqtSignal, QObject

SERVICE_NAME = "MediaManagement"
APP_URL = "http://localhost:5000"
LOG_FILE = Path(__file__).parent / "service.log"


class ServiceMonitor(QObject):
    """Background thread to monitor service status."""
    status_changed = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.running = True
        self.last_status = None
        
    def check_service_status(self):
        """Check if the Windows service is running."""
        try:
            result = subprocess.run(
                ['powershell', '-Command', 
                 f'(Get-Service -Name {SERVICE_NAME}).Status'],
                capture_output=True,
                text=True,
                timeout=5
            )
            status = result.stdout.strip()
            return status
        except Exception:
            return "Unknown"
    
    def run(self):
        """Monitor service status in background."""
        while self.running:
            status = self.check_service_status()
            if status != self.last_status:
                self.last_status = status
                self.status_changed.emit(status)
            time.sleep(5)  # Check every 5 seconds


class LogViewerDialog(QDialog):
    """Dialog to view service logs."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Service Logs")
        self.setGeometry(100, 100, 800, 600)
        
        layout = QVBoxLayout()
        
        # Log text area
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("font-family: Consolas; font-size: 10pt;")
        layout.addWidget(self.log_text)
        
        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_logs)
        layout.addWidget(refresh_btn)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)
        self.load_logs()
    
    def load_logs(self):
        """Load and display logs."""
        try:
            if LOG_FILE.exists():
                with open(LOG_FILE, 'r', encoding='utf-8') as f:
                    # Read last 1000 lines
                    lines = f.readlines()
                    content = ''.join(lines[-1000:])
                    self.log_text.setPlainText(content)
                    # Scroll to bottom
                    self.log_text.verticalScrollBar().setValue(
                        self.log_text.verticalScrollBar().maximum()
                    )
            else:
                self.log_text.setPlainText("No log file found")
        except Exception as e:
            self.log_text.setPlainText(f"Error loading logs: {e}")


class MediaManagementTray(QSystemTrayIcon):
    """System tray application for Media Management service."""
    
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.service_status = "Unknown"
        
        # Create icon
        self.create_icon()
        
        # Create menu
        self.menu = QMenu()
        self.create_menu()
        self.setContextMenu(self.menu)
        
        # Status indicator
        self.status_action = QAction("Status: Checking...", self.menu)
        self.status_action.setEnabled(False)
        self.menu.insertAction(self.menu.actions()[0], self.status_action)
        self.menu.insertSeparator(self.menu.actions()[1])
        
        # Start service monitor
        self.monitor = ServiceMonitor()
        self.monitor.status_changed.connect(self.update_status)
        self.monitor_thread = threading.Thread(target=self.monitor.run, daemon=True)
        self.monitor_thread.start()
        
        # Initial status check
        QTimer.singleShot(1000, self.check_initial_status)
        
        # Show tray icon
        self.show()
        self.showMessage(
            "Media Management",
            "Service monitor started",
            QSystemTrayIcon.Information,
            2000
        )
    
    def create_icon(self):
        """Create system tray icon."""
        # Create a simple colored circle icon
        pixmap = QPixmap(64, 64)
        pixmap.fill(QColor(0, 0, 0, 0))  # Transparent background
        
        from PyQt5.QtGui import QPainter, QBrush
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw circle
        painter.setBrush(QBrush(QColor(52, 152, 219)))  # Blue
        painter.setPen(QColor(255, 255, 255))
        painter.drawEllipse(4, 4, 56, 56)
        
        # Draw "M" in center
        from PyQt5.QtGui import QFont
        font = QFont("Arial", 32, QFont.Bold)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), 0x84, "M")  # Qt.AlignCenter
        
        painter.end()
        
        icon = QIcon(pixmap)
        self.setIcon(icon)
    
    def create_menu(self):
        """Create context menu."""
        # Open Web Interface
        open_action = QAction("Open Web Interface", self.menu)
        open_action.triggered.connect(self.open_web_interface)
        self.menu.addAction(open_action)
        
        self.menu.addSeparator()
        
        # Service controls
        start_action = QAction("Start Service", self.menu)
        start_action.triggered.connect(self.start_service)
        self.menu.addAction(start_action)
        
        stop_action = QAction("Stop Service", self.menu)
        stop_action.triggered.connect(self.stop_service)
        self.menu.addAction(stop_action)
        
        restart_action = QAction("Restart Service", self.menu)
        restart_action.triggered.connect(self.restart_service)
        self.menu.addAction(restart_action)
        
        self.menu.addSeparator()
        
        # View logs
        logs_action = QAction("View Logs", self.menu)
        logs_action.triggered.connect(self.view_logs)
        self.menu.addAction(logs_action)
        
        # Run tests
        test_action = QAction("Run Tests", self.menu)
        test_action.triggered.connect(self.run_tests)
        self.menu.addAction(test_action)
        
        self.menu.addSeparator()
        
        # About
        about_action = QAction("About", self.menu)
        about_action.triggered.connect(self.show_about)
        self.menu.addAction(about_action)
        
        # Exit
        exit_action = QAction("Exit", self.menu)
        exit_action.triggered.connect(self.exit_app)
        self.menu.addAction(exit_action)
    
    def check_initial_status(self):
        """Check service status on startup."""
        status = self.monitor.check_service_status()
        self.update_status(status)
    
    def update_status(self, status):
        """Update status display and icon."""
        self.service_status = status
        
        if status == "Running":
            self.status_action.setText("● Status: Running")
            self.setToolTip("Media Management - Running")
            # Could change icon color to green here
        elif status == "Stopped":
            self.status_action.setText("○ Status: Stopped")
            self.setToolTip("Media Management - Stopped")
            # Could change icon color to red here
        else:
            self.status_action.setText(f"? Status: {status}")
            self.setToolTip(f"Media Management - {status}")
    
    def open_web_interface(self):
        """Open web interface in default browser."""
        webbrowser.open(APP_URL)
    
    def start_service(self):
        """Start the Windows service."""
        try:
            subprocess.run(
                ['powershell', '-Command', f'Start-Service -Name {SERVICE_NAME}'],
                check=True,
                capture_output=True
            )
            self.showMessage(
                "Service Started",
                "Media Management service has been started",
                QSystemTrayIcon.Information,
                2000
            )
        except subprocess.CalledProcessError as e:
            QMessageBox.warning(
                None,
                "Error",
                f"Failed to start service:\n{e.stderr.decode()}"
            )
    
    def stop_service(self):
        """Stop the Windows service."""
        try:
            subprocess.run(
                ['powershell', '-Command', f'Stop-Service -Name {SERVICE_NAME}'],
                check=True,
                capture_output=True
            )
            self.showMessage(
                "Service Stopped",
                "Media Management service has been stopped",
                QSystemTrayIcon.Information,
                2000
            )
        except subprocess.CalledProcessError as e:
            QMessageBox.warning(
                None,
                "Error",
                f"Failed to stop service:\n{e.stderr.decode()}"
            )
    
    def restart_service(self):
        """Restart the Windows service."""
        try:
            subprocess.run(
                ['powershell', '-Command', f'Restart-Service -Name {SERVICE_NAME}'],
                check=True,
                capture_output=True
            )
            self.showMessage(
                "Service Restarted",
                "Media Management service has been restarted",
                QSystemTrayIcon.Information,
                2000
            )
        except subprocess.CalledProcessError as e:
            QMessageBox.warning(
                None,
                "Error",
                f"Failed to restart service:\n{e.stderr.decode()}"
            )
    
    def view_logs(self):
        """Show log viewer dialog."""
        dialog = LogViewerDialog()
        dialog.exec_()
    
    def run_tests(self):
        """Run classification tests."""
        try:
            # Run tests in separate window
            script_dir = Path(__file__).parent
            test_script = script_dir / "test_classifier.py"
            
            if test_script.exists():
                subprocess.Popen(
                    ['python', str(test_script)],
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
            else:
                QMessageBox.warning(
                    None,
                    "Error",
                    "test_classifier.py not found"
                )
        except Exception as e:
            QMessageBox.warning(
                None,
                "Error",
                f"Failed to run tests: {e}"
            )
    
    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            None,
            "About Media Management",
            "<h2>Media Management System</h2>"
            "<p><b>Intelligent *arr Routing Service</b></p>"
            "<p>Version 1.0.0</p>"
            "<p>Automatically classifies and routes media requests to:</p>"
            "<ul>"
            "<li>Sonarr (TV Shows)</li>"
            "<li>Radarr (Movies)</li>"
            "<li>Lidarr (Music)</li>"
            "</ul>"
            "<p><a href='https://github.com/zy538324/Media_management'>GitHub Repository</a></p>"
        )
    
    def exit_app(self):
        """Exit the tray application."""
        reply = QMessageBox.question(
            None,
            "Exit",
            "Exit system tray application?\n\n(Service will continue running)",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.monitor.running = False
            self.hide()
            self.app.quit()


def main():
    """Main entry point."""
    # Check if already running
    import socket
    try:
        # Try to bind to a unique port to ensure single instance
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('127.0.0.1', 48127))  # Random high port
    except OSError:
        print("System tray application already running")
        return 1
    
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # Keep running with no windows
    
    # Create tray icon
    tray = MediaManagementTray(app)
    
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
