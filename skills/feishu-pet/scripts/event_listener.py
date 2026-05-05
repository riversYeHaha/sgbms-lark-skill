#!/usr/bin/env python3
"""Event listener for Feishu Pet - wraps lark-cli event +subscribe."""

import json
import subprocess
import threading
from queue import Queue, Empty


class EventListener:
    def __init__(self, event_types=None):
        self.event_types = event_types or ["im.message.receive_v1"]
        self.process = None
        self.queue = Queue()
        self.running = False
        self.thread = None

    def start(self):
        self.running = True
        cmd = [
            "lark-cli",
            "event",
            "+subscribe",
            "--event-types",
            ",".join(self.event_types),
            "--compact",
            "--quiet",
        ]
        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        self.thread = threading.Thread(target=self._read_events, daemon=True)
        self.thread.start()

    def _read_events(self):
        for line in self.process.stdout:
            if not self.running:
                break
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
                self.queue.put(event)
            except json.JSONDecodeError:
                pass

    def get_event(self, timeout=1):
        try:
            return self.queue.get(timeout=timeout)
        except Empty:
            return None

    def stop(self):
        self.running = False
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=3)
