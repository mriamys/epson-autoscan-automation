import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os

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

def save_config(config):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4)

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Epson AutoScan Control Panel")
        self.root.geometry("450x300")
        
        self.config = load_config()
        
        # IP
        tk.Label(root, text="IP принтера:").grid(row=0, column=0, sticky="w", padx=10, pady=10)
        self.ip_var = tk.StringVar(value=self.config.get("printer_ip", ""))
        tk.Entry(root, textvariable=self.ip_var, width=20).grid(row=0, column=1, sticky="w")
        
        # Folder
        tk.Label(root, text="Папка сохранения:").grid(row=1, column=0, sticky="w", padx=10, pady=10)
        self.dir_var = tk.StringVar(value=self.config.get("save_dir", ""))
        tk.Entry(root, textvariable=self.dir_var, width=30).grid(row=1, column=1, sticky="w")
        tk.Button(root, text="...", command=self.choose_dir).grid(row=1, column=2, padx=5)
        
        # DPI
        tk.Label(root, text="Качество (DPI скана):").grid(row=2, column=0, sticky="w", padx=10, pady=10)
        self.dpi_var = tk.StringVar(value=str(self.config.get("dpi", 300)))
        ttk.Combobox(root, textvariable=self.dpi_var, values=["100", "200", "300", "600", "1200"], width=10).grid(row=2, column=1, sticky="w")
        
        # Color Mode
        tk.Label(root, text="Режим цвета:").grid(row=3, column=0, sticky="w", padx=10, pady=10)
        self.color_var = tk.StringVar(value=self.config.get("color_mode", "RGB24"))
        ttk.Combobox(root, textvariable=self.color_var, values=["RGB24", "Grayscale8", "BlackAndWhite1"], width=15).grid(row=3, column=1, sticky="w")
        
        # Enabled
        self.enabled_var = tk.BooleanVar(value=self.config.get("enabled", True))
        tk.Checkbutton(root, text="Включить автосканирование (Работает в фоне)", variable=self.enabled_var, font=("Arial", 10, "bold")).grid(row=4, column=0, columnspan=2, sticky="w", padx=10, pady=15)
        
        # Save Button
        tk.Button(root, text="Сохранить настройки", command=self.save, bg="#4CAF50", fg="white", font=("Arial", 10, "bold")).grid(row=5, column=0, columnspan=3, pady=10, ipadx=20)

    def choose_dir(self):
        d = filedialog.askdirectory(initialdir=self.dir_var.get())
        if d:
            self.dir_var.set(d)

    def save(self):
        self.config["printer_ip"] = self.ip_var.get()
        self.config["save_dir"] = self.dir_var.get()
        try:
            self.config["dpi"] = int(self.dpi_var.get())
        except ValueError:
            self.config["dpi"] = 300
        self.config["color_mode"] = self.color_var.get()
        self.config["enabled"] = self.enabled_var.get()
        
        save_config(self.config)
        messagebox.showinfo("Сохранено", "Настройки успешно сохранены! Фоновая служба автоматически их подхватит.")

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
