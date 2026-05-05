#!/usr/bin/env python3
"""Message handler for Feishu Pet - parse, route, and respond to messages."""

import json
import re
import subprocess


class MessageHandler:
    def __init__(self, llm_client, state_manager, config):
        self.llm = llm_client
        self.state = state_manager
        self.config = config
        self.pet_name = state_manager.get_pet_name()
        self.conversation_system_prompt = (
            f"你是{self.pet_name}，一个飞书智能宠物助手。你的性格是{config.pet.get('personality', '活泼、乐于助人')}。"
            "请用简洁友好的中文回复，必要时使用 Markdown 格式。"
        )

    def parse_event(self, event):
        return {
            "content": event.get("content", ""),
            "message_id": event.get("message_id") or event.get("id", ""),
            "chat_id": event.get("chat_id", ""),
            "chat_type": event.get("chat_type", "p2p"),
            "sender_id": event.get("sender_id", ""),
            "event_type": event.get("type", ""),
        }

    def should_respond(self, msg):
        content = msg.get("content", "")

        if f"@{self.pet_name}" in content:
            return True

        if msg.get("chat_type") == "p2p":
            return True

        if self._is_urgent(msg):
            return True

        return False

    def _is_urgent(self, msg):
        content = msg.get("content", "")
        urgent_keywords = ["加急", "紧急", "urgent", "urgently", "急！", "危！"]
        return any(kw in content.lower() for kw in urgent_keywords)

    def handle(self, event):
        msg = self.parse_event(event)

        if not self.should_respond(msg):
            return

        intent = self.llm.detect_intent(msg["content"], self.pet_name)

        if intent == "generate":
            response = self._handle_generation_request(msg)
        elif intent == "urgent":
            self.state.increment_urgent()
            response = self._handle_urgent(msg)
        else:
            response = self._handle_chat(msg)

        self._send_reply(msg, response)
        mood = self.llm.analyze_mood(msg["content"])
        self.state.set_mood(mood)
        self.state.save()

    def _handle_chat(self, msg):
        history = self.state.get_conversation(msg["chat_id"])
        messages = []
        for h in history:
            messages.append({"role": "user", "content": h["user"]})
            messages.append({"role": "assistant", "content": h["assistant"]})
        messages.append({"role": "user", "content": msg["content"]})

        return self.llm.chat(messages, system_prompt=self.conversation_system_prompt)

    def _handle_generation_request(self, msg):
        self.state.increment_generation()
        return (
            "收到形象生成请求！🎨\n\n"
            "请通过命令行执行：\n"
            "```bash\n"
            f"python scripts/prepare_pet_run.py --pet-name \"{self.pet_name}\" --output-dir ./pet-run\n"
            "python scripts/generate_pet_images.py --run-dir ./pet-run --states base\n"
            "```\n\n"
            "生成完成后我会自动更新头像！"
        )

    def _handle_urgent(self, msg):
        content = msg["content"].replace(f"@{self.pet_name}", "").strip()
        response = self.llm.chat(
            [
                {
                    "role": "user",
                    "content": f"这是加急消息，请认真回复：{content}",
                }
            ],
            system_prompt=f"你是{self.pet_name}，这是一个加急消息，请认真并以最有效的方式回答。使用简洁的 Markdown 格式。",
        )
        self.state.increment_urgent()
        return f"🚨 收到加急！\n\n{response}"

    def _send_reply(self, msg, response):
        try:
            cmd = [
                "lark-cli",
                "im",
                "+messages-reply",
                "--message-id",
                msg["message_id"],
                "--content",
                response,
                "--as",
                "bot",
            ]
            subprocess.run(cmd, check=True, capture_output=True, timeout=15)
        except Exception as e:
            print(f"[reply error] {e}")
