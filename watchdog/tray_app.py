# -*- coding: utf-8 -*-
import pystray
from PIL import Image, ImageDraw
import subprocess
import os
import json

CONFIG_FILE = r"D:\EpsonAutoScan\config.json"

def get_config():
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except:
        pass
    return {"enabled": True}

def is_autoscan_enabled(item):
    return get_config().get("enabled", True)

def toggle_autoscan(icon, item):
    config = get_config()
    config["enabled"] = not config.get("enabled", True)
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
    except:
        pass
    # Force update the menu in some pystray versions
    icon.update_menu()

def force_scan_now(icon, item):
    subprocess.Popen(['pythonw.exe', r"D:\EpsonAutoScan\epson_autoscan_service.py", "--scan-now"])

def create_image():
    image = Image.new('RGB', (64, 64), color=(0, 120, 215))
    d = ImageDraw.Draw(image)
    d.rectangle([20, 15, 44, 45], fill=(255,255,255))
    d.rectangle([24, 19, 40, 25], fill=(0, 120, 215))
    return image

def restart_spooler(icon, item):
    subprocess.Popen(['powershell.exe', '-WindowStyle', 'Hidden', '-Command', 
                      'Start-Process cmd -ArgumentList \'/c net stop spooler & net start spooler & echo Spooler Restarted! & timeout /t 2\' -Verb RunAs'])

def run_diagnostics(icon, item):
    subprocess.Popen(['powershell.exe', '-ExecutionPolicy', 'Bypass', '-File', r'C:\ProgramData\EpsonSpoolerWatchdog\diagnose.ps1'], creationflags=subprocess.CREATE_NEW_CONSOLE)

def exit_app(icon, item):
    icon.stop()

image = create_image()
menu = pystray.Menu(
    pystray.MenuItem("Перезапустить печать", restart_spooler, default=True),
    pystray.MenuItem("Забрать скан сейчас", force_scan_now),
    pystray.MenuItem("Автосканирование", toggle_autoscan, checked=is_autoscan_enabled),
    pystray.MenuItem("Диагностика печати", run_diagnostics),
    pystray.MenuItem("Выход", exit_app)
)

icon = pystray.Icon("EpsonTools", image, "Epson Tools", menu)
icon.run()
