#!/usr/bin/env python3
"""LLM client for Feishu Pet - unified interface for multiple providers."""

import json
import requests


PROVIDERS = {
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "models": ["deepseek-chat", "deepseek-reasoner"],
    },
    "kimi": {
        "base_url": "https://api.moonshot.cn/v1",
        "models": ["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"],
    },
    "glm": {
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "models": ["glm-4", "glm-4-plus"],
    },
    "volcengine": {
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "models": ["doubao-pro", "doubao-lite"],
    },
}


class LLMClient:
    def __init__(self, llm_config):
        self.provider = llm_config.get("provider", "deepseek")
        self.model = llm_config.get("model", "deepseek-chat")
        self.api_key = llm_config.get("api_key")
        self.base_url = llm_config.get(
            "base_url", PROVIDERS.get(self.provider, {}).get("base_url", "")
        )
        self.temperature = llm_config.get("temperature", 0.7)
        self.max_tokens = llm_config.get("max_tokens", 2000)

    def chat(self, messages, system_prompt=None):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        full_messages = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        full_messages.extend(messages)

        data = {
            "model": self.model,
            "messages": full_messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=data,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    def analyze_mood(self, message):
        moods = ["online", "happy", "sad", "busy", "thinking", "away"]
        prompt = (
            f"分析以下消息的情绪，只回复一个词（{', '.join(moods)}）：\n\n{message}"
        )
        try:
            result = self.chat(
                [{"role": "user", "content": prompt}],
                system_prompt=f"你是一个情绪分析器，只回复以下词语之一：{', '.join(moods)}。不要解释。",
            )
            result = result.strip().lower()
            if result in moods:
                return result
        except Exception:
            pass
        return "online"

    def detect_intent(self, message, pet_name):
        prompt = (
            f"用户对名为「{pet_name}」的宠物说了：\n"
            f"「{message}」\n\n"
            f"判断用户意图，只回复一个词：chat（普通聊天）、generate（生成形象）、"
            f"urgent（紧急求助）、question（技术问题）。不要解释。"
        )
        try:
            result = self.chat(
                [{"role": "user", "content": prompt}],
                system_prompt="你是一个意图识别器，只回复：chat, generate, urgent, question 之一。不要解释。",
            )
            return result.strip().lower()
        except Exception:
            return "chat"
