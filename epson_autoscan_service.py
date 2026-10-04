import urllib.request
import ssl
import time
import datetime
import os
import json
import xml.etree.ElementTree as ET

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "log.txt")

def log(msg):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")
    try:
        print(msg)
    except:
        pass

def load_config():
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {
            "printer_ip": "192.168.0.122",
            "save_dir": r"C:\Users\Administrator\Pictures",
            "dpi": 300,
            "color_mode": "RGB24",
            "enabled": True
        }

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

def get_escl_state(ip):
    url = f"https://{ip}/eSCL/ScannerStatus"
    try:
        with urllib.request.urlopen(url, context=CTX, timeout=3) as resp:
            data = resp.read()
            root = ET.fromstring(data)
            state_el = root.find(".//{http://www.pwg.org/schemas/2010/12/sm}State")
            if state_el is not None:
                return state_el.text
    except Exception:
        pass
    return None

def show_notification(title, msg):
    try:
        import subprocess
        ps = f"""
Add-Type -AssemblyName System.Windows.Forms
$balloon = New-Object System.Windows.Forms.NotifyIcon
$balloon.Icon = [System.Drawing.SystemIcons]::Information
$balloon.BalloonTipIcon = 'Info'
$balloon.BalloonTipTitle = '{title}'
$balloon.BalloonTipText = '{msg}'
$balloon.Visible = $True
$balloon.ShowBalloonTip(5000)
Start-Sleep -Seconds 5
$balloon.Dispose()
"""
        subprocess.Popen(['powershell', '-WindowStyle', 'Hidden', '-Command', ps], creationflags=subprocess.CREATE_NO_WINDOW)
    except Exception as e:
        log(f"Notify error: {e}")

def send_to_trash(path):
    try:
        import ctypes
        from ctypes import wintypes
        import os
        class SHFILEOPSTRUCTW(ctypes.Structure):
            _fields_ = [('hwnd', wintypes.HWND), ('wFunc', wintypes.UINT),
                        ('pFrom', wintypes.LPCWSTR), ('pTo', wintypes.LPCWSTR),
                        ('fFlags', wintypes.UINT), ('fAnyOperationsAborted', wintypes.BOOL),
                        ('hNameMappings', wintypes.LPVOID), ('lpszProgressTitle', wintypes.LPCWSTR)]
        path = os.path.abspath(path) + '\0\0'
        shf = SHFILEOPSTRUCTW()
        shf.hwnd = 0
        shf.wFunc = 3 # FO_DELETE
        shf.pFrom = path
        shf.pTo = None
        shf.fFlags = 64 | 16 # FOF_ALLOWUNDO | FOF_NOCONFIRMATION
        shf.fAnyOperationsAborted = 0
        shf.hNameMappings = 0
        shf.lpszProgressTitle = None
        ctypes.windll.shell32.SHFileOperationW(ctypes.byref(shf))
    except Exception as e:
        log(f"Trash error: {e}")

def is_blank_page(filepath):
    try:
        from PIL import Image
        im = Image.open(filepath).convert('L')
        # Check standard deviation
        from PIL import ImageStat
        stat = ImageStat.Stat(im)
        stddev = stat.stddev[0]
        mean = stat.mean[0]
        # A totally blank page usually has low stddev and high mean
        # Even with shadows, if it's very blank (stddev < 30 and mean > 200)
        # But wait, earlier blank had stddev 50! Let's just use the bounding box logic.
        
        # Ink detection
        im.thumbnail((500, 500))
        ink = im.point(lambda p: 255 if p < 230 else 0)
        data = list(ink.getdata())
        ink_pixels = sum(1 for p in data if p == 255)
        # 500x500 thumbnail = 250,000 pixels. Blank page has very few ink pixels.
        if ink_pixels < 2500:
            return True
        return False
    except Exception as e:
        log(f"Error checking blank page: {e}")
        return False

def trigger_scan(config):
    ip = config["printer_ip"]
    dpi = config["dpi"]
    save_dir = config["save_dir"]
    color_mode = config.get("color_mode", "RGB24")
    
    log(f"[{datetime.datetime.now()}] Triggering network scan at {dpi} DPI...")
    
    # 2454 x 3414 is max scan region for 300 DPI, but since it's generic let's ask for the max the scanner handles. 
    # eSCL usually figures out the resolution.
    xml_data = f"""<?xml version="1.0" encoding="UTF-8"?>
<scan:ScanSettings xmlns:scan="http://schemas.hp.com/imaging/escl/2011/05/03" xmlns:pwg="http://www.pwg.org/schemas/2010/12/sm">
    <pwg:Version>2.9</pwg:Version>
    <scan:Intent>Document</scan:Intent>
    <scan:DocumentFormat>image/jpeg</scan:DocumentFormat>
    <scan:InputSource>Platen</scan:InputSource>
    <scan:ColorMode>{color_mode}</scan:ColorMode>
    <scan:XResolution>{dpi}</scan:XResolution>
    <scan:YResolution>{dpi}</scan:YResolution>
    <scan:ScanRegions>
        <scan:ScanRegion>
            <scan:Width>2454</scan:Width>
            <scan:Height>3414</scan:Height>
        </scan:ScanRegion>
    </scan:ScanRegions>
</scan:ScanSettings>"""

    req = urllib.request.Request(
        f'https://{ip}/eSCL/ScanJobs',
        data=xml_data.encode('utf-8'),
        headers={'Content-Type': 'text/xml'},
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req, context=CTX, timeout=5) as response:
            location = response.getheader('Location')
            if not location:
                log("Failed to get scan job location.")
                return
                
            time.sleep(1)
            doc_url = location + "/NextDocument"
            if doc_url.startswith("http://"):
                doc_url = doc_url.replace(f"http://{ip}:80", f"https://{ip}")
                doc_url = doc_url.replace(f"http://{ip}", f"https://{ip}")
            
            log(f"Downloading from: {doc_url}")
            req_doc = urllib.request.Request(doc_url)
            
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"EpsonScan_{timestamp}.jpg"
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
            filepath = os.path.join(save_dir, filename)
            
            with urllib.request.urlopen(req_doc, context=CTX, timeout=60) as doc_resp:
                with open(filepath, 'wb') as f:
                    f.write(doc_resp.read())
                    
            if is_blank_page(filepath):
                log(f"[{datetime.datetime.now()}] Blank scan detected! Trashing {filepath}")
                send_to_trash(filepath)
                show_notification("Epson AutoScan", "Бланк скана удалён (печать с телефона).")
            else:
                log(f"[{datetime.datetime.now()}] Successfully saved to: {filepath}")
                show_notification("Epson AutoScan", "Новый скан успешно сохранён!")
            
            try:
                delete_url = location
                if delete_url.startswith("http://"):
                    delete_url = delete_url.replace(f"http://{ip}:80", f"https://{ip}")
                    delete_url = delete_url.replace(f"http://{ip}", f"https://{ip}")
                req_del = urllib.request.Request(delete_url, method='DELETE')
                urllib.request.urlopen(req_del, context=CTX, timeout=3)
                log(f"[{datetime.datetime.now()}] Scan job released on printer.")
            except Exception as e:
                log(f"[{datetime.datetime.now()}] Warning: failed to release job: {e}")
            
    except Exception as e:
        log(f"[{datetime.datetime.now()}] Error during scan: {e}")
        if hasattr(e, 'read'):
            log(e.read().decode())

def main():
    log(f"[{datetime.datetime.now()}] Epson AutoScan Service Started!")
    
    copy_in_progress = False
    was_pc_printing = False
    last_state = None
    
    while True:
        config = load_config()
        if not config.get("enabled", True):
            time.sleep(2)
            continue
            
        ip = config["printer_ip"]
        state = get_escl_state(ip)
        
        if state is None:
            time.sleep(2)
            continue
            
        if state != last_state:
            log(f"[{datetime.datetime.now()}] State changed: {last_state} -> {state}")
            last_state = state
            
        if state == "Processing" and not copy_in_progress:
            log(f"[{datetime.datetime.now()}] Printer is now active.")
            copy_in_progress = True
            was_pc_printing = False
            
        if copy_in_progress and not was_pc_printing:
            # Check Printer Web UI to see if it's printing
            try:
                import urllib.request, ssl, re
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                url = f"http://{ip}/PRESENTATION/ADVANCED/INFO_PRTINFO/TOP"
                with urllib.request.urlopen(url, context=ctx, timeout=3) as r:
                    html = r.read().decode('utf-8', errors='ignore')
                    m = re.search(r'Printer Status.*?<li[^>]*>\s*([^<]+)\s*</li>', html, re.IGNORECASE | re.DOTALL)
                    if m:
                        web_status = m.group(1).strip()
                        if web_status != "Available." and web_status != "Доступен.":
                            log(f"[{datetime.datetime.now()}] Web UI Printer Status: {web_status}")
                        if 'print' in web_status.lower() or 'печать' in web_status.lower() or 'печат' in web_status.lower():
                            was_pc_printing = True
                            log(f"[{datetime.datetime.now()}] Detected Printing via Web UI! Will ignore scan.")
            except Exception:
                pass
            
            # Backup check for PC Spooler
            if not was_pc_printing:
                try:
                    import subprocess
                    res = subprocess.run(['powershell', '-Command', '(Get-WmiObject -Class Win32_PrintJob | Measure-Object).Count'], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
                    if int(res.stdout.strip()) > 0:
                        was_pc_printing = True
                        log(f"[{datetime.datetime.now()}] Detected active PC print job via Spooler. Will ignore scan.")
                except Exception:
                    pass
            
        elif state == "Idle" and copy_in_progress:
            log(f"[{datetime.datetime.now()}] Printer returned to Idle.")
            copy_in_progress = False
            
            if was_pc_printing:
                log("Printer finished a PC print job. Skipping scan.")
            else:
                log("Printer finished a Copy. Waiting 1 second for mechanisms to settle...")
                time.sleep(1)
                trigger_scan(config)
            
        time.sleep(1)

if __name__ == "__main__":
    main()
