import yaml
import os

CONFIG_PATH = "config.yaml"

default_config = {
    "video_path": "",
    "rtsp_url": "",
    "output_folder": "",
    "yolo_model_path": "",
    "segment_length_sec": 30,
    "screen_duration_sec": 30,
    "rtsp_duration_sec": 30,
    "source": "file"
}

def load_config():
    if not os.path.exists(CONFIG_PATH):
        save_config(default_config)
        return default_config.copy()
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            if config is None:
                return default_config.copy()
            return config
    except Exception as e:
        print(f"⚠️ Помилка при завантаженні конфігурації: {e}")
        return default_config.copy()

def save_config(config):
    try:
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True)
    except Exception as e:
        print(f"⚠️ Помилка при збереженні конфігурації: {e}")
