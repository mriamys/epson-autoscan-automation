<p align="center">
  <a href="README.md">🇬🇧 English</a> • <b>🇷🇺 Русский</b> • <a href="README.uk.md">🇺🇦 Українська</a>
</p>

# Epson AutoScan Automation

[![Python](https://img.shields.io/badge/Python-3.x-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?logo=windows&logoColor=white)](https://www.microsoft.com/windows)
[![Protocol](https://img.shields.io/badge/Protocol-eSCL-green.svg)](https://mopria.org/spec-download)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

Фоновая служба Windows, графическая панель на Tkinter, утилита в системном трее и watchdog диспетчера печати (Print Spooler) для автоматического сохранения сканов с сетевых МФУ Epson по протоколу eSCL.

## Обзор

Когда на сетевом МФУ Epson (например, Epson L3350 Series) выполняется копирование с панели устройства, `epson_autoscan_service.py` отслеживает переход статуса eSCL (`ScannerStatus`) из `Processing` в `Idle`, отфильтровывает обычные задания печати с ПК/телефона, запускает сетевое сканирование в JPEG по HTTPS eSCL, отсеивает пустые листы и сохраняет скан на компьютер с уведомлением Windows.

## Возможности

- **Автосканирование после копирования (`epson_autoscan_service.py`)**:
  - Каждую секунду опрашивает `https://<printer_ip>/eSCL/ScannerStatus`.
  - Отличает автономное копирование от печати или сканирования с ПК по веб-интерфейсу принтера (`INFO_PRTINFO/TOP`), очереди печати Windows (`Win32_PrintJob`) и активным TCP-подключениям (`Get-NetTCPConnection`).
  - Отправляет задание eSCL `ScanSettings` на полную область A4 (`2550x3510`, с настраиваемыми DPI и режимом цвета), скачивает JPEG через `/NextDocument`, сохраняет как `EpsonScan_YYYYMMDD_HHMMSS.jpg` и освобождает задание (`DELETE`).
- **Определение пустых страниц**: при помощи Pillow (`PIL`) подсчитывает тёмные пиксели на автоматических сканах и отправляет пустые листы (например, после печати с телефона) в Корзину Windows (`SHFileOperationW`).
- **Ручное сканирование**: флаг `--scan-now` запускает немедленное сканирование без автоудаления пустых страниц.
- **Панель настроек GUI (`epson_autoscan_gui.py`)**: интерфейс Tkinter для редактирования `printer_ip`, `save_dir`, `dpi` (`100`/`200`/`300`/`600`/`1200`), `color_mode` (`RGB24`, `Grayscale8`, `BlackAndWhite1`) и флага `enabled` в `config.json`.
- **Трей-утилита и Watchdog диспетчера печати (`watchdog/`)**:
  - `tray_app.py`: значок в системном трее («Epson Tools») для перезапуска Print Spooler, принудительного сканирования, переключения автосканирования и запуска диагностики.
  - `watchdog.ps1`: PowerShell-мониторинг (интервал 10 сек, кулдаун 60 сек), перезапускающий службу `Spooler` при её остановке, событии PrintService ID `842` (`0x80004005`) или зависании задания печати дольше 40 секунд.
  - `install.ps1` / `Install.bat` и `diagnose.ps1`: регистрирует задачу в Планировщике заданий (`EpsonSpoolerWatchdog` от `SYSTEM` при старте системы), включает журнал PrintService Operational, создаёт ярлыки на Рабочем столе и выводит диагностику.

## Использование

### Служба и ручное сканирование

```powershell
# Запуск фоновой службы автосканирования
python epson_autoscan_service.py

# Немедленное ручное сканирование
python epson_autoscan_service.py --scan-now
```

### GUI и значок в трее

```powershell
# Открыть панель настроек Tkinter
python epson_autoscan_gui.py

# Запустить утилиту в системном трее
pythonw watchdog/tray_app.py
```

### Установка Watchdog (от имени администратора)

Разместите файлы watchdog в `C:\ProgramData\EpsonSpoolerWatchdog\` и запустите `watchdog/Install.bat` (или `powershell -ExecutionPolicy Bypass -File watchdog/install.ps1` от администратора).

## Стек технологий

- **Python 3.x** (`urllib`, `ssl`, `xml.etree.ElementTree`, `tkinter`, `ctypes`)
- **Pillow (`PIL`)** — определение пустых страниц и генерация иконки трея
- **pystray** — интеграция с системным треем Windows
- **PowerShell и Планировщик заданий Windows** — watchdog диспетчера печати и диагностика
- **eSCL (AirScan)** — сетевое сканирование по HTTPS

## Настройка и конфигурация

Отредактируйте `config.json` (или используйте `epson_autoscan_gui.py`):

```json
{
  "printer_ip": "<YOUR_PRINTER_IP>",
  "save_dir": "C:\\Users\\<YourUser>\\Pictures",
  "dpi": 300,
  "color_mode": "RGB24",
  "enabled": true
}
```

Установите зависимости Python для проверки пустых страниц и трея:

```powershell
pip install pillow pystray
```

> **Примечание:** в `watchdog/tray_app.py`, `watchdog/install.ps1`, `watchdog/watchdog.ps1` и `watchdog/diagnose.ps1` указаны локальные пути (`D:\EpsonAutoScan\`, `C:\ProgramData\EpsonSpoolerWatchdog\`) и имя принтера (`L3350 Series(Сеть)`). При необходимости адаптируйте их под свою систему.

## Структура проекта

```text
epson-autoscan-automation/
├── watchdog/
│   ├── Install.bat              # Запуск установщика с повышением прав
│   ├── diagnose.ps1             # Диагностика Spooler и событий PrintService
│   ├── install.ps1              # Настройка задачи планировщика и ярлыков
│   ├── tray_app.py              # Утилита в системном трее Windows
│   └── watchdog.ps1             # Цикл мониторинга Print Spooler
├── config.json                  # IP принтера, папка сохранения, DPI, цвет
├── epson_autoscan_gui.py        # Панель управления на Tkinter
├── epson_autoscan_service.py    # Фоновая служба автосканирования eSCL
├── LICENSE                      # Лицензия Apache 2.0
├── NOTICE                       # Уведомление об авторстве
├── README.md                    # Документация на английском
├── README.ru.md                 # Документация на русском
└── README.uk.md                 # Документация на украинском
```

## Лицензия и атрибуция

Проект распространяется под лицензией [Apache License 2.0](LICENSE) — подробности об указании авторства см. в файле [NOTICE](NOTICE).

Если проект оказался полезным, вы можете поставить звезду или сделать [Fork на GitHub](https://github.com/mriamys/epson-autoscan-automation), сохранив ссылку на оригинальный репозиторий: [https://github.com/mriamys/epson-autoscan-automation](https://github.com/mriamys/epson-autoscan-automation).
