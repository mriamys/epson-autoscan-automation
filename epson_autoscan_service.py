import urllib.request
import ssl
import time
import datetime
import os
import json
import xml.etree.ElementTree as ET

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

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

def trigger_scan(config):
    ip = config["printer_ip"]
    dpi = config["dpi"]
    save_dir = config["save_dir"]
    color_mode = config.get("color_mode", "RGB24")
    
    print(f"[{datetime.datetime.now()}] Triggering network scan at {dpi} DPI...")
    
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
                print("Failed to get scan job location.")
                return
                
            time.sleep(1)
            doc_url = location + "/NextDocument"
            if doc_url.startswith("http://"):
                doc_url = doc_url.replace(f"http://{ip}:80", f"https://{ip}")
                doc_url = doc_url.replace(f"http://{ip}", f"https://{ip}")
            
            print(f"Downloading from: {doc_url}")
            req_doc = urllib.request.Request(doc_url)
            
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"EpsonScan_{timestamp}.jpg"
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
            filepath = os.path.join(save_dir, filename)
            
            with urllib.request.urlopen(req_doc, context=CTX, timeout=60) as doc_resp:
                with open(filepath, 'wb') as f:
                    f.write(doc_resp.read())
                    
            print(f"[{datetime.datetime.now()}] Successfully saved to: {filepath}")
            
            try:
                delete_url = location
                if delete_url.startswith("http://"):
                    delete_url = delete_url.replace(f"http://{ip}:80", f"https://{ip}")
                    delete_url = delete_url.replace(f"http://{ip}", f"https://{ip}")
                req_del = urllib.request.Request(delete_url, method='DELETE')
                urllib.request.urlopen(req_del, context=CTX, timeout=3)
                print(f"[{datetime.datetime.now()}] Scan job released on printer.")
            except Exception as e:
                print(f"[{datetime.datetime.now()}] Warning: failed to release job: {e}")
            
    except Exception as e:
        print(f"[{datetime.datetime.now()}] Error during scan: {e}")
        if hasattr(e, 'read'):
            print(e.read().decode())

def main():
    print(f"[{datetime.datetime.now()}] Epson AutoScan Service Started!")
    
    copy_in_progress = False
    
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
            
        if state == "Processing" and not copy_in_progress:
            print(f"[{datetime.datetime.now()}] Printer is now active (Copy started).")
            copy_in_progress = True
            
        elif state == "Idle" and copy_in_progress:
            print(f"[{datetime.datetime.now()}] Printer returned to Idle (Copy finished).")
            copy_in_progress = False
            
            print("Waiting 1 second for mechanisms to settle...")
            time.sleep(1)
            trigger_scan(config)
            
        time.sleep(1)

if __name__ == "__main__":
    main()
