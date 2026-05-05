#!/usr/bin/env python3
"""Feishu Pet Daemon - main process for the Feishu Pet skill."""

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config_manager import load_config, save_config, Config
from state_manager import StateManager
from llm_client import LLMClient
from event_listener import EventListener
from message_handler import MessageHandler

MOOD_FRAME_MAP = {
    "online": "idle:0",
    "happy": "idle:1",
    "busy": "waiting:0",
    "away": "idle:5",
    "sad": "failed:0",
    "thinking": "review:0",
}


class FeishuPetDaemon:
    def __init__(self, config_path):
        self.config_path = os.path.abspath(config_path)
        self.config = load_config(self.config_path)
        self.state = StateManager(self.config.state_file)
        self.llm = LLMClient(self.config.llm)
        self.handler = MessageHandler(self.llm, self.state, self.config)
        self.listener = None
        self.running = False

        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        print(f"\n[{self.pet_name}] 正在优雅退出...")
        self.running = False

    @property
    def pet_name(self):
        return self.state.get_pet_name()

    def start(self):
        self.state.load()
        self.state.state["status"] = "online"
        self.state.set_mood("online")
        self.state.save()

        print(f"[{self.pet_name}] 宠物已上线！")
        print(f"[{self.pet_name}] LLM: {self.config.llm.get('provider')}/{self.config.llm.get('model')}")
        print(f"[{self.pet_name}] 情绪切换: {'启用' if self.config.mood.get('enabled') else '关闭'}")

        self.listener = EventListener(self.config.feishu.get("event_types"))
        self.listener.start()
        print(f"[{self.pet_name}] 正在监听消息... (Ctrl+C 退出)")

        event_count = 0
        reply_count = 0
        last_mood_check = time.time()
        self.running = True

        while self.running:
            event = self.listener.get_event(timeout=1)
            if event:
                event_count += 1
                self.handler.handle(event)
                reply_count += 1

            if self.config.mood.get("enabled", True):
                now = time.time()
                if now - last_mood_check > self.config.mood.get("update_interval", 60):
                    self._update_avatar()
                    last_mood_check = now

            if event_count % 100 == 0 and event_count > 0:
                self.state.save()
                print(
                    f"[{self.pet_name}] 心跳: {event_count} 事件, {reply_count} 回复, "
                    f"情绪: {self.state.get_mood()}"
                )

        self.stop()
        print(f"[{self.pet_name}] 下线。共处理 {event_count} 个事件，{reply_count} 次回复。")

    def stop(self):
        if self.listener:
            self.listener.stop()
        self.state.state["status"] = "offline"
        self.state.save()
        print(f"[{self.pet_name}] 状态已保存到 {self.state.state_file}")

    def _update_avatar(self):
        mood = self.state.get_mood()
        frame_spec = self.config.mood.get("mapping", MOOD_FRAME_MAP).get(mood, "idle:0")

        avatar_info = self.state.get_avatar_info()
        spritesheet_path = avatar_info.get("spritesheet_path")
        if not spritesheet_path or not os.path.exists(spritesheet_path):
            return

        current_frame = avatar_info.get("current_frame")
        if current_frame == frame_spec:
            return

        try:
            row_name, col = frame_spec.split(":")
            col = int(col)

            from PIL import Image

            with Image.open(spritesheet_path) as img:
                atlas = img.convert("RGBA")

            ROW_MAP = {
                "idle": 0, "running-right": 1, "running-left": 2,
                "waving": 3, "jumping": 4, "failed": 5,
                "waiting": 6, "running": 7, "review": 8,
            }
            row = ROW_MAP.get(row_name, 0)
            left = col * 192
            top = row * 208
            frame = atlas.crop((left, top, left + 192, top + 208))

            avatar_path = os.path.join(
                os.path.dirname(spritesheet_path), "avatar-current.png"
            )
            frame.save(avatar_path)
            self.state.set_avatar_info({"current_frame": frame_spec})
        except Exception as e:
            print(f"[{self.pet_name}] 头像更新失败: {e}")


def cmd_init(args):
    config_path = os.path.abspath(args.config)
    if os.path.exists(config_path):
        print(f"配置文件已存在: {config_path}")
        overwrite = (
            input("覆盖已有配置？(y/N): ").strip().lower() if not args.force else "y"
        )
        if overwrite != "y":
            return

    from config_manager import save_config

    config_data = {
        "pet": {
            "name": args.name or "小 Lark",
            "personality": args.personality or "活泼、乐于助人、技术专家",
        },
        "llm": {
            "provider": "deepseek",
            "model": "deepseek-chat",
            "api_key": "${DEEPSEEK_API_KEY}",
            "temperature": 0.7,
            "max_tokens": 2000,
        },
        "feishu": {
            "app_id": "${FEISHU_APP_ID}",
            "app_secret": "${FEISHU_APP_SECRET}",
            "event_types": ["im.message.receive_v1"],
        },
        "image_generation": {
            "provider": "volcengine",
            "model": "doubao-seedream-5-0-260128",
            "api_key": "${ARK_API_KEY}",
            "size": "2K",
            "atlas": {
                "columns": 8,
                "rows": 9,
                "cell_width": 192,
                "cell_height": 208,
            },
            "chroma_key": "#00FF00",
            "chroma_threshold": 30,
        },
        "behavior": {
            "auto_reply": True,
            "reply_delay": 1,
            "context_window": 10,
        },
        "mood": {
            "enabled": True,
            "update_interval": 60,
            "mapping": MOOD_FRAME_MAP,
        },
        "state_file": "./pet-state.json",
    }

    save_config(config_path, config_data)
    print(f"配置文件已创建: {config_path}")
    print(f"请编辑文件填入你的 API keys。")


def main():
    parser = argparse.ArgumentParser(description="Feishu Pet Daemon")
    subparsers = parser.add_subparsers(dest="command", help="命令")

    start_parser = subparsers.add_parser("start", help="启动宠物")
    start_parser.add_argument("--config", required=True, help="配置文件路径")

    init_parser = subparsers.add_parser("init", help="初始化配置")
    init_parser.add_argument("--config", default="pet-config.yaml", help="配置文件路径")
    init_parser.add_argument("--name", help="宠物名称")
    init_parser.add_argument("--personality", help="宠物性格描述")
    init_parser.add_argument("--force", action="store_true", help="覆盖已有配置")

    status_parser = subparsers.add_parser("status", help="查看状态")
    status_parser.add_argument("--config", required=True, help="配置文件路径")

    args = parser.parse_args()

    if args.command == "init":
        cmd_init(args)
    elif args.command == "start":
        config_path = os.path.abspath(args.config)
        if not os.path.exists(config_path):
            print(f"配置文件未找到: {config_path}")
            print(f"运行 'python {sys.argv[0]} init' 创建配置文件。")
            sys.exit(1)
        daemon = FeishuPetDaemon(config_path)
        daemon.start()
    elif args.command == "status":
        config = load_config(os.path.abspath(args.config))
        state = StateManager(config.state_file)
        state.load()
        print(json.dumps(state.state, indent=2, ensure_ascii=False))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
