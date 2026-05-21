import sys
import math
from PyQt5.QtWidgets import QApplication, QMainWindow, QSystemTrayIcon, QMenu, QAction, qApp
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QPainter, QColor, QRadialGradient, QIcon, QPixmap

class ThreadSafeSignaler(QObject):
    """Permite que los hilos de Jarvis actualicen la interfaz de forma segura."""
    state_changed = pyqtSignal(str)

class JarvisUI(QMainWindow):
    def __init__(self, event_bus, shutdown_callback):
        super().__init__()
        self.event_bus = event_bus
        self.shutdown_callback = shutdown_callback
        
        # --- CONFIGURACIÓN DE VENTANA FLOTANTE ---
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(300, 300)
        
        # Centrar en pantalla
        screen = QApplication.primaryScreen().geometry()
        self.move((screen.width() - 300) // 2, (screen.height() - 300) // 2)

        # --- ESTADO Y ANIMACIÓN ---
        self.current_state = "idle"  # idle, listening, processing, speaking
        self.pulse_phase = 0.0
        
        # Timer a 60 FPS para animaciones súper fluidas
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(16) 
        
        # --- COMUNICACIÓN SEGURA ENTRE HILOS ---
        self.signaler = ThreadSafeSignaler()
        self.signaler.state_changed.connect(self._apply_state_change)
        
        # Nos suscribimos al EventBus para escuchar los cambios de estado
        self.event_bus.subscribe("STATE_CHANGE", lambda data: self.signaler.state_changed.emit(data["state"]))

        # --- SYSTEM TRAY (SEGUNDO PLANO) ---
        self.tray_icon = QSystemTrayIcon(self)
        # Creamos un icono azul genérico en memoria para la barra de tareas
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setBrush(QColor(0, 150, 255))
        painter.drawEllipse(2, 2, 28, 28)
        painter.end()
        self.tray_icon.setIcon(QIcon(pixmap))
        
        # Menú del System Tray
        tray_menu = QMenu()
        show_action = QAction("Mostrar Esfera de Jarvis", self)
        show_action.triggered.connect(self.showNormal)
        quit_action = QAction("Apagar Jarvis", self)
        quit_action.triggered.connect(self.quit_application)
        
        tray_menu.addAction(show_action)
        tray_menu.addAction(quit_action)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def _apply_state_change(self, new_state):
        self.current_state = new_state
        # Si Jarvis empieza a escuchar, mostramos la esfera si estaba oculta
        if new_state == "listening" and self.isHidden():
            self.showNormal()

    def update_animation(self):
        # Avanzamos la fase matemática dependiendo del estado
        if self.current_state == "idle":
            self.pulse_phase += 0.03
        elif self.current_state == "listening":
            self.pulse_phase += 0.15  # Pulso rápido
        elif self.current_state == "processing":
            self.pulse_phase += 0.2   # Pulso errático/muy rápido
        elif self.current_state == "speaking":
            self.pulse_phase += 0.08  # Pulso moderado
            
        self.update() # Fuerza a repintar el frame

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        center_x = self.width() / 2
        center_y = self.height() / 2

        # --- LÓGICA DE COLORES Y TAMAÑOS SEGÚN ESTADO ---
        base_radius = 80
        
        if self.current_state == "idle":
            color_centro = QColor(0, 200, 255, 200)   # Azul celeste
            color_borde = QColor(0, 100, 255, 0)
            radius = base_radius + math.sin(self.pulse_phase) * 10
            
        elif self.current_state == "listening":
            color_centro = QColor(0, 255, 200, 230)   # Cian brillante / Aguamarina
            color_borde = QColor(0, 200, 200, 0)
            radius = base_radius + 20 + math.sin(self.pulse_phase) * 15
            
        elif self.current_state == "processing":
            color_centro = QColor(150, 50, 255, 220)  # Púrpura "pensando"
            color_borde = QColor(100, 0, 255, 0)
            radius = base_radius + 5 + math.sin(self.pulse_phase) * 5
            
        elif self.current_state == "speaking":
            color_centro = QColor(0, 150, 255, 220)   # Azul intenso
            color_borde = QColor(0, 50, 200, 0)
            radius = base_radius + 10 + math.sin(self.pulse_phase) * 25
        else:
            color_centro = QColor(100, 100, 100, 200)
            color_borde = QColor(50, 50, 50, 0)
            radius = base_radius

        # Dibujamos el degradado radial para que parezca luz de neón
        gradient = QRadialGradient(center_x, center_y, radius)
        gradient.setColorAt(0, color_centro)
        gradient.setColorAt(1, color_borde)

        painter.setBrush(gradient)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(int(center_x - radius), int(center_y - radius), int(radius * 2), int(radius * 2))

    def mousePressEvent(self, event):
        """Permite arrastrar la esfera por la pantalla."""
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

    def closeEvent(self, event):
        """¡MAGIA! En lugar de cerrarse, se esconde y sigue corriendo en el System Tray."""
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            "Jarvis Activo",
            "La interfaz se ha minimizado. Jarvis sigue escuchando en segundo plano.",
            QSystemTrayIcon.Information,
            2000
        )

    def quit_application(self):
        """Cierra el programa definitivamente."""
        self.shutdown_callback()
        qApp.quit()