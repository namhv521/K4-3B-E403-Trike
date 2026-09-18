"""Fullscreen video renderer and keyboard-driven recap interaction."""

import time
import uuid
from pathlib import Path

from engine import Session
from logger import append_event


def is_finished(position, duration):
    return float(position) >= float(duration) - 1e-3


class PlaybackClock:
    def __init__(self, duration, position=0.0):
        self.duration = float(duration)
        self.position = max(0.0, min(float(position), self.duration))
        self.anchor = None
        self.playing = False

    def current(self, now=None):
        now = time.monotonic() if now is None else now
        value = self.position + (now - self.anchor if self.playing else 0)
        return max(0.0, min(value, self.duration))

    def play(self, now=None):
        if not self.playing:
            self.anchor = time.monotonic() if now is None else now
            self.playing = True

    def pause(self, now=None):
        if self.playing:
            now = time.monotonic() if now is None else now
            self.position = self.current(now)
            self.anchor = None
            self.playing = False

    def seek(self, position, now=None):
        self.position = max(0.0, min(float(position), self.duration))
        self.anchor = time.monotonic() if self.playing and now is None else now if self.playing else None


class InteractivePlayer:
    def __init__(self, lesson, video_path, audio_path, log_dir, fullscreen=True):
        import cv2
        import pygame

        self.cv2 = cv2
        self.pygame = pygame
        self.lesson = lesson
        self.video_path = Path(video_path)
        self.audio_path = Path(audio_path)
        self.log_dir = Path(log_dir)
        self.session = Session(lesson, str(uuid.uuid4()), time.time())
        self.logged_events = 0
        self.correct_feedback_until = None
        self.completed = False

        pygame.init()
        pygame.mixer.init()
        flags = pygame.FULLSCREEN if fullscreen else pygame.RESIZABLE
        self.screen = pygame.display.set_mode((1280, 720), flags)
        pygame.display.set_caption("Interactive Recap")
        pygame.mouse.set_visible(not fullscreen)
        self.cap = cv2.VideoCapture(str(self.video_path))
        if not self.cap.isOpened():
            raise RuntimeError(f"Cannot open video: {self.video_path}")
        fps = self.cap.get(cv2.CAP_PROP_FPS) or 24
        frames = self.cap.get(cv2.CAP_PROP_FRAME_COUNT) or lesson["duration_seconds"] * fps
        self.duration = min(float(lesson["duration_seconds"]), frames / fps)
        self.clock = PlaybackClock(self.duration)
        pygame.mixer.music.load(str(self.audio_path))
        self.font = pygame.font.SysFont("Segoe UI", 30)
        self.small_font = pygame.font.SysFont("Segoe UI", 22)
        self.title_font = pygame.font.SysFont("Segoe UI", 44, bold=True)
        self.last_frame = None

    def _flush_events(self):
        for event in self.session.events[self.logged_events:]:
            append_event(self.log_dir, event)
        self.logged_events = len(self.session.events)

    def _play(self):
        position = self.clock.current()
        self.pygame.mixer.music.play(start=position)
        self.clock.play()

    def _pause(self):
        self.clock.pause()
        self.pygame.mixer.music.stop()

    def _seek(self, position, autoplay=True):
        self._pause()
        self.clock.seek(min(position, self.duration))
        self.cap.set(self.cv2.CAP_PROP_POS_MSEC, self.clock.position * 1000)
        if is_finished(self.clock.position, self.duration):
            self._complete_session()
        elif autoplay:
            self._play()

    def _complete_session(self):
        if self.completed:
            return
        self._pause()
        self.completed = True
        self.session._event(
            "session_completed",
            time.time(),
            video_time=self.duration,
            score=self.session.summary()["score"],
        )
        self._flush_events()

    def _apply_action(self):
        action = self.session.next_action
        if action:
            self.session.next_action = None
            self._seek(action["time"], action.get("autoplay", False))

    def _handle_key(self, key):
        pygame = self.pygame
        if key == pygame.K_ESCAPE:
            return False
        if self.completed:
            if key == pygame.K_r:
                self.session = Session(self.lesson, str(uuid.uuid4()), time.time())
                self.logged_events = 0
                self.completed = False
                self._seek(0, True)
            return True
        if self.session.active_checkpoint_id:
            if self.correct_feedback_until is not None:
                return True
            if self.session.feedback_until is not None:
                if time.time() >= self.session.feedback_until and key in (pygame.K_0, pygame.K_1, pygame.K_KP0, pygame.K_KP1):
                    command = "0" if key in (pygame.K_0, pygame.K_KP0) else "1"
                    self.session.choose_recovery(command, time.time())
                    self._flush_events()
                    self._apply_action()
                return True
            answer_keys = {pygame.K_a: "A", pygame.K_b: "B", pygame.K_c: "C", pygame.K_d: "D"}
            if key in answer_keys:
                attempt = self.session.submit_answer(answer_keys[key], time.time())
                self._flush_events()
                if attempt["is_correct"]:
                    self.correct_feedback_until = time.monotonic() + 0.9
                return True
        elif key == pygame.K_SPACE:
            self._pause() if self.clock.playing else self._play()
        return True

    def _update(self):
        if self.correct_feedback_until and time.monotonic() >= self.correct_feedback_until:
            self.correct_feedback_until = None
            self.session.active_checkpoint_id = None
            self._apply_action()
        if not self.clock.playing:
            return
        current = self.clock.current()
        checkpoint = self.session.due_checkpoint(current)
        if checkpoint:
            self._pause()
            self.session.open_checkpoint(checkpoint["id"], time.time())
            self._flush_events()
            return
        if is_finished(current, self.duration):
            self._complete_session()

    def _video_surface(self):
        target = self.clock.current()
        self.cap.set(self.cv2.CAP_PROP_POS_MSEC, target * 1000)
        ok, frame = self.cap.read()
        if ok:
            frame = self.cv2.cvtColor(frame, self.cv2.COLOR_BGR2RGB)
            self.last_frame = self.pygame.image.frombuffer(frame.tobytes(), (frame.shape[1], frame.shape[0]), "RGB")
        if self.last_frame is None:
            return self.pygame.Surface((1280, 720))
        width, height = self.screen.get_size()
        scale = min(width / self.last_frame.get_width(), height / self.last_frame.get_height())
        size = (round(self.last_frame.get_width() * scale), round(self.last_frame.get_height() * scale))
        return self.pygame.transform.smoothscale(self.last_frame, size)

    def _text(self, text, font, color, x, y, max_width):
        words, lines, line = text.split(), [], ""
        for word in words:
            candidate = f"{line} {word}".strip()
            if font.size(candidate)[0] <= max_width:
                line = candidate
            else:
                lines.append(line)
                line = word
        if line:
            lines.append(line)
        for item in lines:
            self.screen.blit(font.render(item, True, color), (x, y))
            y += font.get_linesize()
        return y

    def _draw_overlay(self):
        pygame = self.pygame
        width, height = self.screen.get_size()
        report = self.session.summary()
        status = self.small_font.render(f"{self.clock.current():05.1f}s   Điểm {report['score']}/10", True, (225, 237, 246))
        self.screen.blit(status, (24, 20))
        if self.completed:
            shade = pygame.Surface((width, height), pygame.SRCALPHA)
            shade.fill((4, 13, 24, 235))
            self.screen.blit(shade, (0, 0))
            self.screen.blit(self.title_font.render("Hoàn thành bài recap", True, (65, 217, 180)), (width // 2 - 220, 150))
            self.screen.blit(self.title_font.render(f"{report['score']}/10", True, (255, 244, 194)), (width // 2 - 75, 230))
            lines = [f"Lần trả lời: {report['total_attempts']}", f"Sửa đúng sau ôn: {report['corrected_after_review']}", "Nhấn R để học lại · Esc để thoát"]
            for index, line in enumerate(lines):
                self.screen.blit(self.font.render(line, True, (210, 222, 234)), (width // 2 - 180, 330 + index * 50))
            return
        if not self.session.active_checkpoint_id:
            return
        checkpoint = self.session._checkpoint(self.session.active_checkpoint_id)
        shade = pygame.Surface((width, height), pygame.SRCALPHA)
        shade.fill((4, 13, 24, 220))
        self.screen.blit(shade, (0, 0))
        x, y, panel_width = max(40, width // 10), max(45, height // 10), min(1000, width - 120)
        self.screen.blit(self.small_font.render(f"CHECKPOINT · {checkpoint['concept']}", True, (255, 189, 89)), (x, y))
        y = self._text(checkpoint["question"], self.title_font, (246, 244, 236), x, y + 40, panel_width)
        y += 20
        for option in checkpoint["options"]:
            color = (20, 55, 82)
            if self.correct_feedback_until and option["is_correct"]:
                color = (18, 78, 68)
            pygame.draw.rect(self.screen, color, (x, y, panel_width, 58), border_radius=10)
            self.screen.blit(self.font.render(f"{option['id']}   {option['text']}", True, (244, 242, 234)), (x + 18, y + 12))
            y += 68
        if self.correct_feedback_until:
            self.screen.blit(self.font.render(f"Chính xác. {checkpoint['explanation']}", True, (113, 235, 202)), (x, y + 8))
        elif self.session.feedback_until is not None:
            remaining = max(0, self.session.feedback_until - time.time())
            y = self._text(f"Chưa chính xác. {checkpoint['explanation']}", self.font, (255, 145, 128), x, y + 8, panel_width)
            prompt = f"Đọc lời giải: {remaining:.1f}s" if remaining > 0 else "Nhấn 0 để học lại · Nhấn 1 để tới checkpoint tiếp theo"
            self.screen.blit(self.font.render(prompt, True, (255, 211, 128)), (x, y + 12))

    def run(self):
        self._play()
        timer = self.pygame.time.Clock()
        running = True
        try:
            while running:
                for event in self.pygame.event.get():
                    if event.type == self.pygame.QUIT:
                        running = False
                    elif event.type == self.pygame.KEYDOWN:
                        running = self._handle_key(event.key)
                self._update()
                self.screen.fill((2, 7, 13))
                frame = self._video_surface()
                self.screen.blit(frame, frame.get_rect(center=self.screen.get_rect().center))
                self._draw_overlay()
                self.pygame.display.flip()
                timer.tick(30)
        finally:
            self.pygame.mixer.music.stop()
            self.cap.release()
            self.pygame.quit()
