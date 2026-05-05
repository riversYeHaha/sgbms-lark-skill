#!/usr/bin/env python3
"""State manager for Feishu Pet - JSON file persistence."""

import json
import os
import time
from datetime import datetime, timezone


class StateManager:
    def __init__(self, state_file):
        self.state_file = os.path.abspath(state_file)
        self.state = {}

    def load(self):
        if os.path.exists(self.state_file):
            with open(self.state_file, "r") as f:
                self.state = json.load(f)
        else:
            self.state = self._default_state()
            self.save()

    def save(self):
        self.state["last_saved"] = datetime.now(timezone.utc).isoformat()
        os.makedirs(os.path.dirname(self.state_file) or ".", exist_ok=True)
        with open(self.state_file, "w") as f:
            json.dump(self.state, f, indent=2, ensure_ascii=False)

    def _default_state(self):
        return {
            "pet_name": "小 Lark",
            "status": "offline",
            "mood": "online",
            "conversations": {},
            "stats": {
                "total_messages": 0,
                "total_replies": 0,
                "urgent_handled": 0,
                "generations_triggered": 0,
            },
            "last_active": None,
            "last_saved": None,
            "avatar_info": {
                "spritesheet_path": None,
                "current_frame": "idle:0",
                "last_generation": None,
            },
        }

    def get_pet_name(self):
        return self.state.get("pet_name", "小 Lark")

    def set_pet_name(self, name):
        self.state["pet_name"] = name

    def get_mood(self):
        return self.state.get("mood", "online")

    def set_mood(self, mood):
        self.state["mood"] = mood
        self._touch()

    def get_conversation(self, chat_id, max_history=10):
        conversations = self.state.get("conversations", {})
        history = conversations.get(chat_id, [])
        return history[-max_history:]

    def update_conversation(self, chat_id, user_msg, assistant_msg):
        if "conversations" not in self.state:
            self.state["conversations"] = {}
        if chat_id not in self.state["conversations"]:
            self.state["conversations"][chat_id] = []

        self.state["conversations"][chat_id].append(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "user": user_msg,
                "assistant": assistant_msg,
            }
        )

        max_history = 50
        if len(self.state["conversations"][chat_id]) > max_history:
            self.state["conversations"][chat_id] = self.state["conversations"][
                chat_id
            ][-max_history:]

        self.state["stats"]["total_messages"] = self.state["stats"].get(
            "total_messages", 0
        ) + 1
        self.state["stats"]["total_replies"] = self.state["stats"].get(
            "total_replies", 0
        ) + 1
        self._touch()

    def increment_urgent(self):
        self.state["stats"]["urgent_handled"] = self.state["stats"].get(
            "urgent_handled", 0
        ) + 1
        self._touch()

    def increment_generation(self):
        self.state["stats"]["generations_triggered"] = self.state["stats"].get(
            "generations_triggered", 0
        ) + 1
        self._touch()

    def get_avatar_info(self):
        return self.state.get("avatar_info", {})

    def set_avatar_info(self, info):
        self.state["avatar_info"] = {**self.state.get("avatar_info", {}), **info}
        self._touch()

    def _touch(self):
        self.state["last_active"] = datetime.now(timezone.utc).isoformat()
