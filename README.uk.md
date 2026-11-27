<p align="center">
  <a href="README.md">🇬🇧 English</a> • <a href="README.ru.md">🇷🇺 Русский</a> • <b>🇺🇦 Українська</b>
</p>

# Epson AutoScan Automation

[![Python](https://img.shields.io/badge/Python-3.x-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?logo=windows&logoColor=white)](https://www.microsoft.com/windows)
[![Protocol](https://img.shields.io/badge/Protocol-eSCL-green.svg)](https://mopria.org/spec-download)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

Фонова служба Windows, графічна панель на Tkinter, утиліта в системному треї та watchdog диспетчера друку (Print Spooler) для автоматичного збереження сканів із мережевих БФП Epson через протокол eSCL.

## Огляд

Коли на мережевому БФП Epson (наприклад, Epson L3350 Series) виконується копіювання з панелі пристрою, `epson_autoscan_service.py` відстежує перехід статусу eSCL (`ScannerStatus`) із `Processing` у `Idle`, відфільтровує звичайні завдання друку з ПК/телефона, запускає мережеве сканування у JPEG через HTTPS eSCL, відсіює порожні аркуші та зберігає скан на комп'ютер зі сповіщенням Windows.

## Можливості

- **Автосканування після копіювання (`epson_autoscan_service.py`)**:
  - Щосекунди опитує `https://<printer_ip>/eSCL/ScannerStatus`.
  - Відрізняє автономне копіювання від друку чи сканування з ПК за веб-інтерфейсом принтера (`INFO_PRTINFO/TOP`), чергою друку Windows (`Win32_PrintJob`) та активними TCP-з'єднаннями (`Get-NetTCPConnection`).
  - Надсилає завдання eSCL `ScanSettings` на повну область A4 (`2550x3510`, з налаштовуваними DPI та режимом кольору), завантажує JPEG через `/NextDocument`, зберігає як `EpsonScan_YYYYMMDD_HHMMSS.jpg` і звільняє завдання (`DELETE`).
- **Визначення порожніх сторінок**: за допомогою Pillow (`PIL`) підраховує темні пікселі на автоматичних сканах і переміщує порожні аркуші (наприклад, після друку з телефона) до Кошика Windows (`SHFileOperationW`).
- **Ручне сканування**: прапорець `--scan-now` запускає негайне сканування без автовидалення порожніх сторінок.
- **Панель налаштувань GUI (`epson_autoscan_gui.py`)**: інтерфейс Tkinter для редагування `printer_ip`, `save_dir`, `dpi` (`100`/`200`/`300`/`600`/`1200`), `color_mode` (`RGB24`, `Grayscale8`, `BlackAndWhite1`) і прапорця `enabled` у `config.json`.
- **Трей-утиліта та Watchdog диспетчера друку (`watchdog/`)**:
  - `tray_app.py`: іконка в системному треї («Epson Tools») для перезапуску Print Spooler, примусового сканування, перемикання автосканування та запуску діагностики.
  - `watchdog.ps1`: PowerShell-моніторинг (інтервал 10 сек, кулдаун 60 сек), що перезапускає службу `Spooler` у разі її зупинки, події PrintService ID `842` (`0x80004005`) або зависання завдання друку понад 40 секунд.
  - `install.ps1` / `Install.bat` і `diagnose.ps1`: реєструє завдання у Планувальнику завдань (`EpsonSpoolerWatchdog` від `SYSTEM` під час старту системи), вмикає журнал PrintService Operational, створює ярлики на Робочому столі та виводить діагностику.

## Використання

### Служба та ручне сканування

```powershell
# Запуск фонової служби автосканування
python epson_autoscan_service.py

# Негайне ручне сканування
python epson_autoscan_service.py --scan-now
```

### GUI та іконка в треї

```powershell
# Відкрити панель налаштувань Tkinter
python epson_autoscan_gui.py

# Запустити утиліту в системному треї
pythonw watchdog/tray_app.py
```

### Встановлення Watchdog (від імені адміністратора)

Розмістіть файли watchdog у `C:\ProgramData\EpsonSpoolerWatchdog\` і запустіть `watchdog/Install.bat` (або `powershell -ExecutionPolicy Bypass -File watchdog/install.ps1` від адміністратора).

## Стек технологій

- **Python 3.x** (`urllib`, `ssl`, `xml.etree.ElementTree`, `tkinter`, `ctypes`)
- **Pillow (`PIL`)** — визначення порожніх сторінок і генерація іконки трея
- **pystray** — інтеграція із системним треєм Windows
- **PowerShell та Планувальник завдань Windows** — watchdog диспетчера друку та діагностика
- **eSCL (AirScan)** — мережеве сканування через HTTPS

## Налаштування та конфігурація

Відредагуйте `config.json` (або скористайтеся `epson_autoscan_gui.py`):

```json
{
  "printer_ip": "<YOUR_PRINTER_IP>",
  "save_dir": "C:\\Users\\<YourUser>\\Pictures",
  "dpi": 300,
  "color_mode": "RGB24",
  "enabled": true
}
```

Встановіть залежності Python для перевірки порожніх сторінок і трея:

```powershell
pip install pillow pystray
```

> **Примітка:** у `watchdog/tray_app.py`, `watchdog/install.ps1`, `watchdog/watchdog.ps1` і `watchdog/diagnose.ps1` зазначені локальні шляхи (`D:\EpsonAutoScan\`, `C:\ProgramData\EpsonSpoolerWatchdog\`) та назва принтера (`L3350 Series(Сеть)`). За потреби адаптуйте їх під вашу систему.

## Структура проєкту

```text
epson-autoscan-automation/
├── watchdog/
│   ├── Install.bat              # Запуск інсталятора з підвищеними правами
│   ├── diagnose.ps1             # Діагностика Spooler та подій PrintService
│   ├── install.ps1              # Налаштування завдання планувальника та ярликів
│   ├── tray_app.py              # Утиліта в системному треї Windows
│   └── watchdog.ps1             # Цикл моніторингу Print Spooler
├── config.json                  # IP принтера, папка збереження, DPI, колір
├── epson_autoscan_gui.py        # Панель керування на Tkinter
├── epson_autoscan_service.py    # Фонова служба автосканування eSCL
├── LICENSE                      # Ліцензія Apache 2.0
├── NOTICE                       # Повідомлення про авторство
├── README.md                    # Документація англійською
├── README.ru.md                 # Документація російською
└── README.uk.md                 # Документація українською
```

## Ліцензія та атрибуція

Проєкт поширюється за ліцензією [Apache License 2.0](LICENSE) — деталі щодо зазначення авторства див. у файлі [NOTICE](NOTICE).

Якщо проєкт став вам у пригоді, поставте зірочку або зробіть [Fork на GitHub](https://github.com/mriamys/epson-autoscan-automation), зберігаючи посилання на оригінальний репозиторій: [https://github.com/mriamys/epson-autoscan-automation](https://github.com/mriamys/epson-autoscan-automation).
