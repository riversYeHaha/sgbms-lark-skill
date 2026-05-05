#!/usr/bin/env python3
"""Desktop Pet App - Main entry point for Feishu Desktop Pet with messaging."""

import argparse
import os
import sys
import threading
import time
import webbrowser
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import pygame
except ImportError:
    print("请先安装 pygame: pip install pygame")
    sys.exit(1)

from pet_display import PetDisplay, ROW_MAP, DEFAULT_FRAME_TIMES
from config_manager import load_config
from state_manager import StateManager
from llm_client import LLMClient
from event_listener import EventListener
from message_handler import MessageHandler


class DesktopPetApp:
    def __init__(self, config_path):
        self.config_path = os.path.abspath(config_path)
        self.config = None
        self.state = None
        self.llm = None
        self.handler = None
        self.listener = None
        self.pet = None
        self.listener_thread = None
        self.running = True

    def _load_config(self):
        if not os.path.exists(self.config_path):
            print(f"[error] 配置文件未找到: {self.config_path}")
            print(f"请运行: python scripts/pet_daemon.py init --config {self.config_path}")
            sys.exit(1)

        self.config = load_config(self.config_path)
        self.state = StateManager(self.config.state_file)
        self.state.load()
        self.llm = LLMClient(self.config.llm)
        self.handler = MessageHandler(self.llm, self.state, self.config)

        print(f"[desktop_pet] 配置加载成功")
        print(f"[desktop_pet] 宠物名称: {self.state.get_pet_name()}")
        print(f"[desktop_pet] LLM: {self.config.llm.get('provider')}/{self.config.llm.get('model')}")

    def _find_spritesheet(self):
        spritesheet_paths = [
            os.path.join(os.path.dirname(self.config_path), "pet-run", "final", "spritesheet.png"),
            os.path.join(os.path.dirname(self.config_path), "spritesheet.png"),
            "./spritesheet.png",
        ]
        for path in spritesheet_paths:
            if os.path.exists(path):
                return path
        return None

    def _setup_pet_display(self):
        spritesheet = self._find_spritesheet()
        initial_state = "idle"

        self.pet = PetDisplay(spritesheet, initial_state)

        def on_single_click(state):
            print(f"[desktop_pet] 点击! 状态: {state}")
            self._show_status_menu()

        def on_double_click(state):
            print(f"[desktop_pet] 双击! 切换到 idle")
            self.pet.set_state("idle")
            self.state.set_mood("online")
            self.state.save()

        def on_idle_transition():
            mood = self.state.get_mood()
            if mood in ROW_MAP:
                new_state = self._mood_to_state(mood)
                if new_state != self.pet.current_state:
                    self.pet.set_state(new_state)

        self.pet.on_click(on_single_click)
        self.pet.on_double_click(on_double_click)

        return spritesheet

    def _mood_to_state(self, mood):
        mood_map = {
            "online": "idle",
            "happy": "idle",
            "busy": "waiting",
            "away": "idle",
            "sad": "failed",
            "thinking": "review",
        }
        return mood_map.get(mood, "idle")

    def _show_status_menu(self):
        print("\n" + "=" * 40)
        print(f"  🐾 {self.state.get_pet_name()} 状态菜单")
        print("=" * 40)
        print("  1. 🎮 切换到 idle (待机)")
        print("  2. 🏃 切换到 running (奔跑)")
        print("  3. 👋 切换到 waving (挥手)")
        print("  4. ⏳ 切换到 waiting (等待)")
        print("  5. 🔄 刷新状态")
        print("  0. ❌ 关闭宠物")
        print("=" * 40)

        try:
            choice = input("请选择 (0-5): ").strip()
            if choice == "1":
                self.pet.set_state("idle")
            elif choice == "2":
                self.pet.set_state("running")
            elif choice == "3":
                self.pet.set_state("waving")
            elif choice == "4":
                self.pet.set_state("waiting")
            elif choice == "5":
                self._refresh_mood()
            elif choice == "0":
                self.running = False
        except (EOFError, KeyboardInterrupt):
            pass

    def _refresh_mood(self):
        mood = self.state.get_mood()
        state = self._mood_to_state(mood)
        self.pet.set_state(state)
        print(f"[desktop_pet] 状态已刷新: {mood} -> {state}")

    def _message_listener_loop(self):
        self.listener = EventListener(self.config.feishu.get("event_types"))
        self.listener.start()
        print("[desktop_pet] 飞书消息监听已启动")

        while self.running:
            event = self.listener.get_event(timeout=1)
            if event:
                self._handle_feishu_event(event)

        if self.listener:
            self.listener.stop()

    def _handle_feishu_event(self, event):
        try:
            if event.get("event_type") != "im.message.receive_v1":
                return

            msg = self.handler.parse_event(event)

            if not self.handler.should_respond(msg):
                return

            intent = self.llm.detect_intent(msg["content"], self.state.get_pet_name())

            if intent == "urgent":
                self.pet.set_state("failed")
                self.state.increment_urgent()
            elif intent == "question":
                self.pet.set_state("review")
            else:
                self.pet.set_state("waving")

            self.handler.handle(event)

            time.sleep(1)
            self._refresh_mood()

        except Exception as e:
            print(f"[desktop_pet] 处理消息异常: {e}")

    def run(self):
        print("\n" + "=" * 50)
        print("  🐾 Feishu Desktop Pet 启动中...")
        print("=" * 50 + "\n")

        self._load_config()
        spritesheet = self._setup_pet_display()

        if spritesheet:
            print(f"[desktop_pet] 已加载 spritesheet: {spritesheet}")
        else:
            print("[desktop_pet] 警告: 未找到 spritesheet，使用占位符")

        self.listener_thread = threading.Thread(
            target=self._message_listener_loop,
            daemon=True,
        )
        self.listener_thread.start()

        mood = self.state.get_mood()
        initial_state = self._mood_to_state(mood)
        self.pet.set_state(initial_state)
        print(f"[desktop_pet] 初始状态: {mood} -> {initial_state}")

        print("\n" + "=" * 50)
        print("  🐾 桌面宠物已上线!")
        print("  操作说明:")
        print("    - 拖动: 按住鼠标拖动宠物")
        print("    - 单击: 显示状态菜单")
        print("    - 双击: 切换到 idle")
        print("    - ESC: 退出程序")
        print("=" * 50 + "\n")

        self.pet.run()

        print("\n[desktop_pet] 保存状态...")
        if self.state:
            self.state.state["status"] = "offline"
            self.state.save()
        print("[desktop_pet] 已关闭")


def main():
    parser = argparse.ArgumentParser(description="Feishu Desktop Pet")
    parser.add_argument(
        "--config",
        required=True,
        help="配置文件路径 (pet-config.yaml)",
    )
    parser.add_argument(
        "--spritesheet",
        help="手动指定 spritesheet 路径",
        default=None,
    )
    args = parser.parse_args()

    app = DesktopPetApp(args.config)

    if args.spritesheet:
        if app.pet:
            app.pet.set_spritesheet(args.spritesheet)

    app.run()


if __name__ == "__main__":
    main()
