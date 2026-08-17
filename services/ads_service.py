import json
import os

CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'ads_config.json')

DEFAULT_CONFIG = {
    "admin_password": "admin",
    "top_ad": {
        "enabled": False,
        "type": "custom",
        "image_url": "",
        "link_url": "",
        "alt_text": "פרסומת",
        "html_code": ""
    },
    "bottom_ad": {
        "enabled": False,
        "type": "custom",
        "image_url": "",
        "link_url": "",
        "alt_text": "פרסומת",
        "html_code": ""
    }
}

def load_ads_config():
    if not os.path.exists(CONFIG_FILE):
        save_ads_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error reading ads config: {e}")
        return DEFAULT_CONFIG

def save_ads_config(config_data):
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Error saving ads config: {e}")
        return False
