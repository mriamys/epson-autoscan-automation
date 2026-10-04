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
    import urllib.request, ssl, datetime
    config = get_config()
    ip = config.get("printer_ip", "192.168.0.122")
    dpi = config.get("dpi", 300)
    save_dir = config.get("save_dir", r"C:\Users\Administrator\Pictures")
    color = config.get("color_mode", "RGB24")
    
    # Just launch a simple python script in background to do the scan so tray doesn't freeze
    script = f"""
import urllib.request, ssl, time, datetime, os
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

job_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<scan:ScanSettings xmlns:scan="http://schemas.hp.com/imaging/escl/2011/05/03" xmlns:pwg="http://www.pwg.org/schemas/2010/12/sm">
    <pwg:Version>2.9</pwg:Version>
    <scan:Intent>Document</scan:Intent>
    <scan:DocumentFormat>image/jpeg</scan:DocumentFormat>
    <scan:InputSource>Platen</scan:InputSource>
    <scan:ColorMode>{color}</scan:ColorMode>
    <scan:XResolution>{dpi}</scan:XResolution>
    <scan:YResolution>{dpi}</scan:YResolution>
</scan:ScanSettings>'''

try:
    req = urllib.request.Request('https://{ip}/eSCL/ScanJobs', data=job_xml.encode('utf-8'), headers={{'Content-Type': 'text/xml'}}, method='POST')
    with urllib.request.urlopen(req, context=ctx) as r:
        url = r.headers['Location']
    time.sleep(1)
    req2 = urllib.request.Request(url + '/NextDocument')
    with urllib.request.urlopen(req2, context=ctx, timeout=60) as r:
        data = r.read()
    if not os.path.exists(r'{save_dir}'): os.makedirs(r'{save_dir}')
    path = os.path.join(r'{save_dir}', f'EpsonScan_{{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}}.jpg')
    with open(path, 'wb') as f: f.write(data)
except Exception as e:
    pass
"""
    with open(r"D:\EpsonAutoScan\manual_scan.py", "w", encoding="utf-8") as f:
        f.write(script)
    subprocess.Popen(['pythonw.exe', r"D:\EpsonAutoScan\manual_scan.py"])

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
