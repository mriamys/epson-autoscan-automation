import urllib.request
import ssl
import time

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

job_xml = b"""<?xml version="1.0" encoding="UTF-8"?>
<scan:ScanSettings xmlns:scan="http://schemas.hp.com/imaging/escl/2011/05/03" xmlns:pwg="http://www.pwg.org/schemas/2010/12/sm">
    <pwg:Version>2.0</pwg:Version>
    <scan:Intent>Document</scan:Intent>
    <pwg:InputSource>Platen</pwg:InputSource>
    <scan:DocumentFormat>image/jpeg</scan:DocumentFormat>
    <scan:ColorMode>RGB24</scan:ColorMode>
    <scan:XResolution>100</scan:XResolution>
    <scan:YResolution>100</scan:YResolution>
</scan:ScanSettings>"""

try:
    req = urllib.request.Request('https://192.168.0.122/eSCL/ScanJobs', data=job_xml, headers={'Content-Type': 'text/xml'}, method='POST')
    with urllib.request.urlopen(req, context=ctx) as r:
        job_url = r.headers['Location']
        print("Job URL:", job_url)
        
    time.sleep(1)
    
    req_doc = urllib.request.Request(job_url + '/NextDocument', method='GET')
    with urllib.request.urlopen(req_doc, context=ctx) as r:
        with open('D:/EpsonAutoScan/test_blank.jpg', 'wb') as f:
            f.write(r.read())
    print("Saved blank scan")
except Exception as e:
    print(e)
