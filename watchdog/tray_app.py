import pystray
from PIL import Image, ImageDraw
import subprocess
import os

def create_image():
    image = Image.new('RGB', (64, 64), color=(0, 120, 215))
    d = ImageDraw.Draw(image)
    # Simple icon drawing (a letter P for Print)
    d.rectangle([20, 15, 44, 45], fill=(255,255,255))
    d.rectangle([24, 19, 40, 25], fill=(0, 120, 215))
    return image

def restart_spooler(icon, item):
    subprocess.Popen(['powershell.exe', '-WindowStyle', 'Hidden', '-Command', 
                      'Start-Process cmd -ArgumentList \'/c net stop spooler & net start spooler & echo Успешно перезапущено! & timeout /t 2\' -Verb RunAs'])

def run_diagnostics(icon, item):
    subprocess.Popen(['powershell.exe', '-ExecutionPolicy', 'Bypass', '-File', r'C:\ProgramData\EpsonSpoolerWatchdog\diagnose.ps1'], creationflags=subprocess.CREATE_NEW_CONSOLE)

def open_autoscan(icon, item):
    if os.path.exists(r'D:\EpsonAutoScan\epson_autoscan_gui.py'):
        subprocess.Popen(['pythonw.exe', r'D:\EpsonAutoScan\epson_autoscan_gui.py'])

def exit_app(icon, item):
    icon.stop()

image = create_image()
menu = pystray.Menu(
    pystray.MenuItem("Перезапустить печать", restart_spooler, default=True),
    pystray.MenuItem("Диагностика печати", run_diagnostics),
    pystray.MenuItem("Настройки автосканирования", open_autoscan),
    pystray.MenuItem("Выход", exit_app)
)

icon = pystray.Icon("EpsonTools", image, "Epson Tools", menu)
icon.run()
