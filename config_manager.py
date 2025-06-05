import yaml
import os

CONFIG_PATH = "config.yaml"

default_config = {
    "video_path": "",
    "output_folder": "",
    "yolo_model_path": "",
    "segment_length_sec": 30
}

def load_config():
    if not os.path.exists(CONFIG_PATH):
        save_config(default_config)
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def save_config(config):
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, allow_unicode=True)
