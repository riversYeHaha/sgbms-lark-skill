#!/usr/bin/env python3
"""Configuration manager for Feishu Pet."""

import os
import yaml


class Config:
    def __init__(self, data):
        self.pet = data.get("pet", {})
        self.llm = data.get("llm", {})
        self.feishu = data.get("feishu", {})
        self.image_generation = data.get("image_generation", {})
        self.behavior = data.get("behavior", {})
        self.mood = data.get("mood", {})
        self.state_file = data.get("state_file", "./pet-state.json")


def load_config(config_path):
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    config = _resolve_env(config)
    return Config(config)


def _resolve_env(obj):
    if isinstance(obj, dict):
        return {k: _resolve_env(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_resolve_env(item) for item in obj]
    elif isinstance(obj, str) and obj.startswith("${") and obj.endswith("}"):
        inner = obj[2:-1]
        if ":" in inner:
            env_var, default = inner.split(":", 1)
        else:
            env_var, default = inner, None
        return os.getenv(env_var.strip(), default)
    return obj


def save_config(config_path, config_data):
    with open(config_path, "w") as f:
        yaml.safe_dump(config_data, f, default_flow_style=False, allow_unicode=True)
