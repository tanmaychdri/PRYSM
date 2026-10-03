import sys
import math
import ctypes
import random
import traceback
import threading
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer, QPoint, QPointF, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPolygonF, QCursor, QPen

# For tracking active windows on Windows OS
user32 = ctypes.windll.user32
class RECT(ctypes.Structure):
    _fields_ = [
        ('left', ctypes.c_long),
        ('top', ctypes.c_long),
        ('right', ctypes.c_long),
        ('bottom', ctypes.c_long)
    ]

def get_window_rect(hwnd):
    if user32.IsWindow(hwnd) and user32.IsWindowVisible(hwnd) and not user32.IsIconic(hwnd):
        rect = RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
        return rect.left, rect.top, rect.right, rect.bottom
    return None

def get_random_window():
    hwnds = []
    def enum_win_cb(hwnd, lparam):
        if user32.IsWindowVisible(hwnd) and not user32.IsIconic(hwnd) and user32.GetWindowTextLengthW(hwnd) > 0:
            rect = RECT()
            user32.GetWindowRect(hwnd, ctypes.byref(rect))
            w, h = rect.right - rect.left, rect.bottom - rect.top
            # Filter out tiny windows, huge desktop-sized windows
            if w > 200 and h > 200 and w < 3000 and h < 2000:
                hwnds.append(hwnd)
        return True
    
    EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    cb = EnumWindowsProc(enum_win_cb)
    user32.EnumWindows(cb, 0)
    if hwnds:
        return random.choice(hwnds)
    return None

class PrysmMascot(QWidget):
    # Thread-safe signal to receive events from async PRYSM core
    prysm_event = pyqtSignal(str, str)  # (event_type, detail)
    
    def __init__(self):
        super().__init__()
        
        # Connect the signal to the handler
        self.prysm_event.connect(self._on_prysm_event)
        
        # Transparent, frameless window that stays on top
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Fixed size for the drawing area
        self.scale_factor = 0.3
        self.resize(int(200 * self.scale_factor), int(240 * self.scale_factor))
        
        # Internal State
        self.state = "waving"  # Start by waving hello!
        self.is_grabbed = False
        self.tick_count = 0
        
        QTimer.singleShot(2500, self._end_waving)
        
        # Animation states
        self.dizzy_level = 0
        self.look_offset_x = 0
        self.look_timer = 0
        self.dash_velocity_x = 0
        self.hand_swing_x = 0
        self.left_hand_y = 0
        self.right_hand_y = 0
        self.left_hand_angle = 0.0
        self.right_hand_angle = 0.0
        self.eye_rotation_angle = 0.0
        self.body_bounce_y = 0.0
        self.last_pos = self.pos()
        self.dizzy_center = self.pos()
        self.press_global_pos = None
        
        # Window tracking state
        self.target_hwnd = None
        self.last_window_rect = (0, 0, 0, 0)
        self.window_still_frames = 0
        self.follow_mouse_mode = False
        
        # Animation timer for redrawing
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self.animate_frame)
        self.anim_timer.start(30) # ~33fps
        
        # Initial position
        screen = QApplication.primaryScreen().geometry()
        self.exact_x = float(screen.width() // 2)
        self.exact_y = float(screen.height() // 2)
        self.move(int(self.exact_x), int(self.exact_y))
        self.target_pos = QPoint(int(self.exact_x), int(self.exact_y))
        self.drag_pos = None
        self._connected_to_prysm = False
        
    def _end_waving(self):
        if self.state == "waving":
            self.state = "idle"
            
    def connect_to_prysm(self, event_bus):
        """Subscribe to PRYSM EventBus events. Call from the async side."""
        import asyncio
        from prysm.core.events import (
            ListeningStarted, ListeningCompleted,
            AssistantThinkingStarted, AssistantThinkingCompleted,
            ResponseGenerated, SpeakingStarted, SpeakingCompleted,
            ProcessingStarted, ProcessingCompleted,
            StateChanged,
        )
        
        self._connected_to_prysm = True
        
        async def on_listening_started(ev):
            self.prysm_event.emit("listening_started", "")
        
        async def on_listening_completed(ev):
            self.prysm_event.emit("listening_completed", ev.transcript)
            
        async def on_thinking_started(ev):
            self.prysm_event.emit("thinking_started", "")
            
        async def on_thinking_completed(ev):
            self.prysm_event.emit("thinking_completed", "")

        async def on_response(ev):
            text = ev.response_text[:60] + "..." if len(ev.response_text) > 60 else ev.response_text
            self.prysm_event.emit("response", text)
            
        async def on_speaking_started(ev):
            self.prysm_event.emit("speaking_started", "")
            
        async def on_speaking_completed(ev):
            self.prysm_event.emit("speaking_completed", "")
        
        event_bus.subscribe(ListeningStarted, on_listening_started)
        event_bus.subscribe(ListeningCompleted, on_listening_completed)
        event_bus.subscribe(AssistantThinkingStarted, on_thinking_started)
        event_bus.subscribe(AssistantThinkingCompleted, on_thinking_completed)
        event_bus.subscribe(ResponseGenerated, on_response)
        event_bus.subscribe(SpeakingStarted, on_speaking_started)
        event_bus.subscribe(SpeakingCompleted, on_speaking_completed)
    
    def _on_prysm_event(self, event_type: str, detail: str):
        """Handle PRYSM events on the Qt UI thread."""
        if event_type == "listening_started":
            self.state = "listening"
        elif event_type == "listening_completed":
            self.state = "idle"
            if detail:
                import re
                text = re.sub(r'[^a-z\s]', '', detail.lower()).strip()
                words = text.split()
                
                if getattr(self, 'is_standby', False):
                    if "prism" in text or "wake up" in text:
                        self.is_standby = False
                        self.state = "waving"
                        QTimer.singleShot(2500, self._end_waving)
                else:
                    if "sleep" in text or "stand by" in text:
                        self.going_to_standby = True
                
                if "follow my mouse" in text or "fmm" in words:
                    self.follow_mouse_mode = True
                elif "stop following my mouse" in text or "stop following" in text or "sf" in words:
                    self.follow_mouse_mode = False
        elif event_type == "thinking_started":
            self.state = "thinking"
        elif event_type == "thinking_completed":
            self.state = "idle"
        elif event_type == "response":
            pass  # speaking_started will handle it
        elif event_type == "speaking_started":
            self.state = "speaking"
        elif event_type == "speaking_completed":
            if getattr(self, 'going_to_standby', False):
                self.going_to_standby = False
                self.is_standby = True
                self.state = "sleep"
            else:
                self.state = "idle"

    def list_behaviours(self):
        """Return a dictionary describing all possible mascot behaviours."""
        return {
            "idle": "Default roaming/looking around.",
            "happy": "Eyes ^ ^, reacts to mouse hover.",
            "sleep": "Floats up/down, eyes closed.",
            "grabbed": "Hands raised while being dragged.",
            "dizzy": "Crossed X X eyes, circles while confused.",
            "listening": "Pulsing eyes, awaiting input.",
            "speaking": "Animated mouth, body bounces.",
            "dashing": "Fast movement towards a target window.",
            "looking": "Turns head toward active window when it changes."
        }
        
    def animate_frame(self):
        self.tick_count += 1
        
        # Decay dizzy level
        if self.dizzy_level > 0:
            self.dizzy_level -= 1
        if self.state == "dizzy" and self.dizzy_level == 0:
            self.state = "idle"
            
        # Check active window for looking
        fg_hwnd = user32.GetForegroundWindow()
        if fg_hwnd and fg_hwnd != getattr(self, 'active_hwnd', None):
            self.active_hwnd = fg_hwnd
            # Ignore self
            if fg_hwnd != int(self.winId()):
                rect = get_window_rect(fg_hwnd)
                if rect:
                    left, top, right, bottom = rect
                    win_center_x = left + (right - left) // 2
                    mascot_center_x = self.x() + self.width() // 2
                    if win_center_x < mascot_center_x - 50:
                        self.look_offset_x = -15
                    elif win_center_x > mascot_center_x + 50:
                        self.look_offset_x = 15
                    else:
                        self.look_offset_x = 0
                    
                    self.look_timer = 60 # look for 2 seconds
                    if self.state == "sleep":
                        self.state = "idle" # Wake up to look
            
        # Idle looking around logic
        if self.state == "idle" or self.state == "sleep":
            if self.look_timer > 0:
                self.look_timer -= 1
            elif self.state == "idle":
                r = random.random()
                if r < 0.2: self.look_offset_x = -15
                elif r < 0.4: self.look_offset_x = 15
                else: self.look_offset_x = 0
                self.look_timer = random.randint(30, 90) # hold look for 1-3 seconds
        else:
            self.look_offset_x = 0

        # Hand animation positions based on state
        self.left_hand_y = 0
        self.right_hand_y = 0
        self.hand_swing_x = 0
        
        if self.state == "idle":
            self.left_hand_y = math.sin(self.tick_count * 0.1) * 5
            self.right_hand_y = math.sin(self.tick_count * 0.1) * 5
        elif self.state == "grabbed":
            self.left_hand_y = 15
            self.right_hand_y = 15
        elif self.state == "sleep":
            self.left_hand_y = 10
            self.right_hand_y = 10
        elif self.state == "happy":
            self.left_hand_y = math.sin(self.tick_count * 0.4) * 10
            self.right_hand_y = math.sin(self.tick_count * 0.4) * 10
        elif self.state == "dizzy":
            self.left_hand_y = math.sin(self.tick_count * 0.5) * 12
            self.right_hand_y = math.cos(self.tick_count * 0.5) * 12
        elif self.state in ["listening", "thinking"]:
            self.left_hand_y = math.sin(self.tick_count * 0.2) * 5
            self.right_hand_y = math.sin(self.tick_count * 0.2) * 5
        elif self.state == "speaking":
            # Bouncy hands while speaking
            self.left_hand_y = math.sin(self.tick_count * 0.3) * 8
            self.right_hand_y = math.cos(self.tick_count * 0.3) * 8
            # Bob the head up and down
            self.body_bounce_y = abs(math.sin(self.tick_count * 0.4)) * 12
        elif self.state == "dashing":
            self.left_hand_y = 5
            self.right_hand_y = 5
            # Swing hands backwards while dashing
            self.hand_swing_x = -15 if self.dash_velocity_x > 0 else 15
        elif self.state == "waving":
            self.left_hand_y = 5
            self.right_hand_y = -10 # lift shoulder slightly
            self.body_bounce_y = abs(math.sin(self.tick_count * 0.2)) * 5
            
        # Target angles for hand rotation
        target_l_angle = 0
        target_r_angle = 0
        
        if self.state == "sleep":
            target_l_angle = 75 + math.sin(self.tick_count * 0.05) * 10
            target_r_angle = -75 - math.sin(self.tick_count * 0.05) * 10
        elif self.state == "speaking":
            target_l_angle = 30 + math.sin(self.tick_count * 0.4) * 30
            target_r_angle = -30 - math.sin(self.tick_count * 0.4) * 30
        elif self.state == "grabbed":
            target_l_angle = 120
            target_r_angle = -120
        elif self.state == "dashing":
            target_l_angle = -45
            target_r_angle = 45
        elif self.state == "happy":
            target_l_angle = 45 + math.sin(self.tick_count * 0.5) * 20
            target_r_angle = -45 - math.sin(self.tick_count * 0.5) * 20
        elif self.state == "waving":
            target_l_angle = 15
            # Right hand raised and waving energetically
            target_r_angle = -150 + math.sin(self.tick_count * 0.6) * 40
            
        # Smooth interpolation
        self.left_hand_angle += (target_l_angle - self.left_hand_angle) * 0.2
        self.right_hand_angle += (target_r_angle - self.right_hand_angle) * 0.2
            
        # Reset bounce when not speaking
        if self.state != "speaking":
            self.body_bounce_y = max(0, self.body_bounce_y - 2)
            
        if self.state == "thinking":
            self.eye_rotation_angle += 10
        else:
            self.eye_rotation_angle = 0
        
        # Movement interpolation and logic
        self.update_movement_and_logic()
        
        # Trigger paintEvent to redraw with new coordinates
        self.update() 
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Scale all coordinates down
        painter.scale(self.scale_factor, self.scale_factor)
        
        # Colors
        body_color = QColor(220, 220, 220)
        eye_color = QColor(0, 0, 0) # Eyes are always black
        
        painter.setPen(Qt.PenStyle.NoPen)
        
        # --- Draw Head and Eyes ---
        painter.save()
        if getattr(self, 'body_bounce_y', 0) > 0:
            painter.translate(0, self.body_bounce_y)
            
        painter.setBrush(body_color)
        head_poly = QPolygonF([
            QPointF(100, 0),
            QPointF(200, 50),
            QPointF(200, 150),
            QPointF(100, 200),
            QPointF(0, 150),
            QPointF(0, 50)
        ])
        painter.drawPolygon(head_poly)
        
        # --- Draw Eyes ---
        if self.state in ["grabbed", "happy", "dizzy", "waving"]:
            pen = QPen(eye_color, 12 if self.state == "grabbed" else 10, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            
            if self.state == "grabbed":
                # > < Eyes
                left_eye_lines = QPolygonF([QPointF(40, 80), QPointF(65, 95), QPointF(40, 110)])
                right_eye_lines = QPolygonF([QPointF(160, 80), QPointF(135, 95), QPointF(160, 110)])
                painter.drawPolyline(left_eye_lines)
                painter.drawPolyline(right_eye_lines)
            elif self.state in ["happy", "waving"]:
                # ^ ^ Happy Eyes
                left_eye_lines = QPolygonF([QPointF(35, 95), QPointF(55, 75), QPointF(75, 95)])
                right_eye_lines = QPolygonF([QPointF(125, 95), QPointF(145, 75), QPointF(165, 95)])
                painter.drawPolyline(left_eye_lines)
                painter.drawPolyline(right_eye_lines)
            elif self.state == "dizzy":
                # X X Dizzy Eyes
                painter.drawLine(40, 80, 70, 110)
                painter.drawLine(70, 80, 40, 110)
                painter.drawLine(130, 80, 160, 110)
                painter.drawLine(160, 80, 130, 110)
                
            painter.setPen(Qt.PenStyle.NoPen) # reset for hands
            
        elif self.state == "listening":
            # Big round pulsing eyes for listening
            pulse = math.sin(self.tick_count * 0.2) * 5
            lx = 40 - pulse/2
            rx = 130 - pulse/2
            size = 30 + pulse
            
            left_eye_rect = [lx, 80 - pulse/2, size, size]
            right_eye_rect = [rx, 80 - pulse/2, size, size]
            
            painter.setBrush(eye_color)
            painter.drawEllipse(int(lx), int(80 - pulse/2), int(size), int(size))
            painter.drawEllipse(int(rx), int(80 - pulse/2), int(size), int(size))
        else:
            painter.setBrush(eye_color)
            
            # Base eye size with looking offset
            lx = 40 + self.look_offset_x
            rx = 130 + self.look_offset_x
            
            # Default eye rectangles
            left_eye_rect = [lx, 80, 30, 30]
            right_eye_rect = [rx, 80, 30, 30]
            
            if self.state == "sleep":
                # Closed eyes (horizontal lines)
                left_eye_rect = [lx, 95, 30, 5]
                right_eye_rect = [rx, 95, 30, 5]
            elif self.state == "dashing":
                # Narrow eyes leaning into the dash
                shift = 15 if self.dash_velocity_x > 0 else -15
                left_eye_rect = [lx + shift, 85, 20, 20]
                right_eye_rect = [rx + shift, 85, 20, 20]
            elif self.state == "dizzy":
                # Crossed X eyes for dizzy state
                # We'll draw X over the eye area later
                pass
            elif self.state == "idle":
                # Occasional blink
                if self.tick_count % 100 < 4:
                    left_eye_rect = [lx, 95, 30, 5]
                    right_eye_rect = [rx, 95, 30, 5]
            
            # Draw eye shapes (rectangles or ellipses as appropriate)
            if self.state == "thinking":
                # Rotate eyes around their own centers
                painter.save()
                painter.translate(lx + 15, 80 + 15)  # center of left eye
                painter.rotate(self.eye_rotation_angle)
                painter.drawRect(-15, -15, 30, 30)
                painter.restore()
                
                painter.save()
                painter.translate(rx + 15, 80 + 15)  # center of right eye
                painter.rotate(self.eye_rotation_angle)
                painter.drawRect(-15, -15, 30, 30)
                painter.restore()
            else:
                painter.drawRect(*left_eye_rect)
                painter.drawRect(*right_eye_rect)
            
            # If dizzy, overlay X marks
            if self.state == "dizzy":
                pen = QPen(QColor(255, 0, 0), 3)
                painter.setPen(pen)
                # Left eye X
                painter.drawLine(int(lx), int(80), int(lx + 30), int(110))
                painter.drawLine(int(lx + 30), int(80), int(lx), int(110))
                # Right eye X
                painter.drawLine(int(rx), int(80), int(rx + 30), int(110))
                painter.drawLine(int(rx + 30), int(80), int(rx), int(110))
                
        painter.restore() # Restore translation for hands
        
        # --- Draw Hands ---
        painter.setBrush(body_color)
        painter.setPen(Qt.PenStyle.NoPen)
        
        # Left Hand
        painter.save()
        painter.translate(30 + self.hand_swing_x, 175 + self.left_hand_y)
        painter.rotate(self.left_hand_angle)
        left_hand_poly = QPolygonF([
            QPointF(-30, -15),
            QPointF(0, 0),
            QPointF(0, 50),
            QPointF(-30, 35)
        ])
        painter.drawPolygon(left_hand_poly)
        painter.restore()
        
        # Right Hand
        painter.save()
        painter.translate(170 + self.hand_swing_x, 175 + self.right_hand_y)
        painter.rotate(self.right_hand_angle)
        right_hand_poly = QPolygonF([
            QPointF(30, -15),
            QPointF(0, 0),
            QPointF(0, 50),
            QPointF(30, 35)
        ])
        painter.drawPolygon(right_hand_poly)
        painter.restore()

    def update_movement_and_logic(self):
        if getattr(self, 'is_standby', False):
            self.state = "sleep"
            self.dizzy_level = 0
            if self.is_grabbed:
                self.last_pos = self.pos()
            return
            
        if self.is_grabbed:
            # Check if being dragged fast to make it dizzy
            moved = math.hypot(self.x() - self.last_pos.x(), self.y() - self.last_pos.y())
            if moved > 20:
                self.dizzy_level = min(60, self.dizzy_level + int(moved * 0.5))
                
            if self.dizzy_level > 15:
                self.state = "dizzy"
            elif self.state != "dizzy":
                self.state = "idle"
                
            self.last_pos = self.pos()
            return 
            
        mouse_pos = QCursor.pos()
        center_x = self.x() + self.width() // 2
        center_y = self.y() + self.height() // 2
        dist = math.hypot(mouse_pos.x() - center_x, mouse_pos.y() - center_y)
        
        # Priority states that override hover/window tracking
        if self.state in ["listening", "waving", "speaking", "thinking"]:
            pass  # Keep state until finished
        elif self.state == "dizzy":
            # Circular jitter around current position
            radius = 12
            angle = (self.tick_count * 0.2) % (2 * math.pi)
            offset_x = radius * math.cos(angle)
            offset_y = radius * math.sin(angle)
            self.target_pos = QPoint(int(self.exact_x + offset_x), int(self.exact_y + offset_y))
        elif getattr(self, 'follow_mouse_mode', False):
            # Follow mouse overrides happy hover and window tracking
            self.target_pos = QPoint(mouse_pos.x() + 30, mouse_pos.y() + 30)
            if self.state in ["sleep", "happy"]:
                self.state = "idle"
        elif dist < 60:
            self.state = "happy"
            # Don't change target_pos so it stays put while being hovered
        else:
            # Reset happy state when mouse moves away
            if self.state == "happy":
                self.state = "idle"
            # Random Window Tracking
            # Wake up and find a new window if bored/sleeping too long
            if self.state == "sleep" and self.window_still_frames > 1500: 
                self.target_hwnd = get_random_window()
                self.window_still_frames = 0
                self.state = "idle"
                
            if self.target_hwnd is None or get_window_rect(self.target_hwnd) is None:
                self.target_hwnd = get_random_window()
                self.window_still_frames = 0
                self.state = "idle"
                
            if self.target_hwnd:
                rect = get_window_rect(self.target_hwnd)
                if rect:
                    left, top, right, bottom = rect
                    
                    # Target: Top center of the tracked window
                    target_x = left + (right - left) // 2 - self.width() // 2
                    target_y = top - self.height() + int(10 * self.scale_factor)
                    
                    if rect != self.last_window_rect:
                        self.state = "idle"
                        self.last_window_rect = rect
                        self.window_still_frames = 0
                    else:
                        self.window_still_frames += 1
                        if self.window_still_frames > 600 and self.state == "idle": 
                            self.state = "sleep"
                            
                    if self.state == "sleep":
                        # Floating animation (up and down slowly)
                        target_y += int(math.sin(self.tick_count * 0.05) * 15)
                        
                    target_y = max(0, target_y)
                    self.target_pos = QPoint(target_x, target_y)
                else:
                    self.target_hwnd = None
            elif self.state not in ["dashing"]:
                self.state = "idle"

        # Smooth Movement Interpolation & Dashing
        dx = self.target_pos.x() - self.exact_x
        dy = self.target_pos.y() - self.exact_y
        
        # Determine if we should dash (moving a long distance)
        if abs(dx) > 150 and self.state not in ["happy", "dizzy", "grabbed", "listening"]:
            self.state = "dashing"
            self.dash_velocity_x = dx
        elif self.state == "dashing" and abs(dx) < 30:
            self.state = "idle"
        
        speed = 0.15 if self.state == "dashing" else 0.08
        self.exact_x += dx * speed
        self.exact_y += dy * speed
        
        self.move(int(self.exact_x), int(self.exact_y))
        self.last_pos = self.pos()
            
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self.press_global_pos = event.globalPosition()
            self.is_grabbed = True
            # We don't immediately set "grabbed" state to allow for tapping
            self.dizzy_level = 0
            self.last_pos = self.pos()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self.drag_pos is not None:
            new_pos = event.globalPosition().toPoint() - self.drag_pos
            self.move(new_pos)
            self.exact_x = float(new_pos.x())
            self.exact_y = float(new_pos.y())
            self.target_pos = new_pos
            event.accept()
            
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            dist_moved = 0
            if self.press_global_pos:
                dist_moved = math.hypot(event.globalPosition().x() - self.press_global_pos.x(),
                                        event.globalPosition().y() - self.press_global_pos.y())
                                        
            self.drag_pos = None
            self.is_grabbed = False
            self.press_global_pos = None
            
            if dist_moved <= 5:
                # It was a quick tap! Toggle listening mode
                if self.state == "listening":
                    self.state = "idle"
                else:
                    self.state = "listening"
            else:
                # It was a drag, resolve based on dizziness
                if self.dizzy_level > 20:
                    self.state = "dizzy"
                    self.dizzy_center = self.pos()
                else:
                    self.state = "idle"
                
            self.window_still_frames = 0 # reset sleep timer
            event.accept()

if __name__ == '__main__':
    def exception_hook(exctype, value, tb):
        with open("crash.log", "w") as f:
            traceback.print_exception(exctype, value, tb, file=f)
        sys.exit(1)
    sys.excepthook = exception_hook

    app = QApplication(sys.argv)
    mascot = PrysmMascot()
    mascot.show()
    sys.exit(app.exec())
