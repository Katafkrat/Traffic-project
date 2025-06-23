import sys
import subprocess

required_packages = {
    'PyQt5': 'PyQt5',
    'opencv-python': 'cv2',
    'numpy': 'numpy',
    'ultralytics': 'ultralytics',
    'pyyaml': 'yaml',
    'pyautogui': 'pyautogui',
}

def install_if_missing(pip_name, import_name):
    try:
        __import__(import_name)
    except ImportError:
        print(f"📦 Встановлення пакета: {pip_name} ...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name])

for pip_name, import_name in required_packages.items():
    install_if_missing(pip_name, import_name)

from ui.app_ui import run_ui

if __name__ == "__main__":
    run_ui()
