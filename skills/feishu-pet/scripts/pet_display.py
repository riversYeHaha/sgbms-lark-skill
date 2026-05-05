#!/usr/bin/env python3
"""Desktop Pet Display Module - PyGame based transparent window pet."""

import os
import sys
from pathlib import Path

try:
    import pygame
except ImportError:
    print("请先安装 pygame: pip install pygame")
    sys.exit(1)

pygame.init()

CELL_WIDTH = 192
CELL_HEIGHT = 208

ROW_MAP = {
    "idle": 0,
    "running-right": 1,
    "running-left": 2,
    "waving": 3,
    "jumping": 4,
    "failed": 5,
    "waiting": 6,
    "running": 7,
    "review": 8,
}

DEFAULT_FRAME_TIMES = {
    "idle": [280, 110, 110, 140, 140, 320],
    "running-right": [120] * 8,
    "running-left": [120] * 8,
    "waving": [140] * 4,
    "jumping": [140] * 5,
    "failed": [140] * 8,
    "waiting": [150] * 6,
    "running": [120] * 6,
    "review": [150] * 6,
}


class PetDisplay:
    def __init__(self, spritesheet_path=None, default_state="idle"):
        self.spritesheet_path = spritesheet_path
        self.default_state = default_state

        self.screen = None
        self.clock = pygame.time.Clock()
        self.running = True

        self.current_state = default_state
        self.current_frame = 0
        self.frame_timer = 0
        self.animation_speed = 1.0

        self.position = [100, 100]
        self.dragging = False
        self.drag_offset = [0, 0]

        self.click_callback = None
        self.double_click_callback = None
        self._last_click_time = 0

        self._load_spritesheet()

    def _load_spritesheet(self):
        if self.spritesheet_path and os.path.exists(self.spritesheet_path):
            self.spritesheet = pygame.image.load(self.spritesheet_path).convert_alpha()
        else:
            self.spritesheet = self._create_placeholder()
            print(f"[pet_display] 未找到 spritesheet，使用占位符")

    def _create_placeholder(self):
        surface = pygame.Surface((CELL_WIDTH * 8, CELL_HEIGHT * 9), pygame.SRCALPHA)
        colors = [
            (255, 100, 100),
            (100, 255, 100),
            (100, 100, 255),
            (255, 255, 100),
            (255, 100, 255),
            (100, 255, 255),
            (255, 150, 100),
            (150, 100, 255),
            (200, 200, 200),
        ]
        for row, color in enumerate(colors):
            for col in range(8):
                rect = pygame.Rect(col * CELL_WIDTH, row * CELL_HEIGHT, CELL_WIDTH, CELL_HEIGHT)
                pygame.draw.rect(surface, (*color, 180), rect)
                pygame.draw.circle(surface, (255, 255, 255), rect.center, 30)
        return surface

    def create_window(self):
        os.environ["SDL_VIDEO_WINDOW_POS"] = f"{self.position[0]},{self.position[1]}"
        os.environ["SDL_VIDEO_YUV_SWAP_MODE"] = "0"

        info = pygame.display.Info()
        width, height = CELL_WIDTH, CELL_HEIGHT

        self.screen = pygame.display.set_mode(
            (width, height),
            pygame.NOFRAME | pygame.SRCALPHA | pygame.HIDDEN,
        )
        pygame.display.set_caption("Feishu Pet")

        self._set_window_level()

        self.screen.fill((0, 0, 0, 0))
        pygame.display.update()
        self.screen.set_visible(True)

    def _set_window_level(self):
        if sys.platform == "darwin":
            import ctypes
            import objc

            NSApp = objc.OldStyleMethods.getClass("NSApplication").sharedApplication()
            NSWindowCollectionBehavior = objc.getClass("NSWindow").collectionBehavior
            NSWindow = objc.getClass("NSWindow")

            for window in NSApp.windows():
                window.setCollectionBehavior_(NSWindowCollectionBehavior | (1 << 1))

    def set_spritesheet(self, path):
        if os.path.exists(path):
            self.spritesheet_path = path
            self.spritesheet = pygame.image.load(path).convert_alpha()
            return True
        return False

    def set_state(self, state):
        if state in ROW_MAP and state != self.current_state:
            self.current_state = state
            self.current_frame = 0
            self.frame_timer = 0

    def set_animation_speed(self, speed):
        self.animation_speed = speed

    def set_position(self, x, y):
        self.position = [x, y]
        os.environ["SDL_VIDEO_WINDOW_POS"] = f"{x},{y}"
        if self.screen:
            self._update_window_position()

    def _update_window_position(self):
        os.environ["SDL_VIDEO_WINDOW_POS"] = f"{int(self.position[0])},{int(self.position[1])}"
        self.screen = pygame.display.set_mode(
            (CELL_WIDTH, CELL_HEIGHT),
            pygame.NOFRAME | pygame.SRCALPHA,
        )

    def on_click(self, callback):
        self.click_callback = callback

    def on_double_click(self, callback):
        self.double_click_callback = callback

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    mx, my = event.pos
                    if 0 <= mx < CELL_WIDTH and 0 <= my < CELL_HEIGHT:
                        self.dragging = True
                        self.drag_offset = [
                            mx - self.position[0],
                            my - self.position[1],
                        ]

                        now = pygame.time.get_ticks()
                        if now - self._last_click_time < 300:
                            if self.double_click_callback:
                                self.double_click_callback(self.current_state)
                        else:
                            if self.click_callback:
                                self.click_callback(self.current_state)
                        self._last_click_time = now

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self.dragging = False

            elif event.type == pygame.MOUSEMOTION:
                if self.dragging:
                    mx, my = event.pos
                    self.position = [
                        mx - self.drag_offset[0],
                        my - self.drag_offset[1],
                    ]
                    os.environ["SDL_VIDEO_WINDOW_POS"] = (
                        f"{int(self.position[0])},{int(self.position[1])}"
                    )
                    self._update_window_position()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_SPACE:
                    if self.current_state != "idle":
                        self.set_state("idle")

    def _get_frame_times(self):
        return DEFAULT_FRAME_TIMES.get(
            self.current_state, [200] * 8
        )

    def _update_animation(self, dt):
        frame_times = self._get_frame_times()
        frame_count = len(frame_times)

        self.frame_timer += dt * self.animation_speed
        if self.frame_timer >= frame_times[self.current_frame]:
            self.frame_timer = 0
            self.current_frame = (self.current_frame + 1) % frame_count

    def _render(self):
        self.screen.fill((0, 0, 0, 0))

        row = ROW_MAP.get(self.current_state, 0)
        col = self.current_frame

        frame_rect = pygame.Rect(
            col * CELL_WIDTH,
            row * CELL_HEIGHT,
            CELL_WIDTH,
            CELL_HEIGHT,
        )

        frame_surface = self.spritesheet.subsurface(frame_rect)
        self.screen.blit(frame_surface, (0, 0))

        pygame.display.update()

    def run(self):
        self.create_window()
        self.running = True

        while self.running:
            dt = self.clock.tick(60) / 1000.0

            self._handle_events()
            self._update_animation(dt)
            self._render()

        pygame.quit()

    def stop(self):
        self.running = False


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Feishu Desktop Pet")
    parser.add_argument(
        "--spritesheet",
        help="Spritesheet 路径",
        default=None,
    )
    parser.add_argument(
        "--state",
        help="初始状态",
        default="idle",
    )
    parser.add_argument(
        "--speed",
        type=float,
        help="动画速度倍率",
        default=1.0,
    )
    args = parser.parse_args()

    pet = PetDisplay(args.spritesheet, args.state)
    pet.set_animation_speed(args.speed)

    def on_click(state):
        print(f"[pet] 点击! 当前状态: {state}")

    def on_double_click(state):
        print(f"[pet] 双击! 切换到 idle")
        pet.set_state("idle")

    pet.on_click(on_click)
    pet.on_double_click(on_double_click)

    print("[pet] 桌面宠物已启动，点击宠物或按 ESC 退出")
    pet.run()
    print("[pet] 桌面宠物已关闭")


if __name__ == "__main__":
    main()
