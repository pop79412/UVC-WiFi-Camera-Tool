import tkinter as tk
from tkinter import scrolledtext
import serial
import serial.tools.list_ports
import time
import json
import os
import re
import subprocess
import winreg
import pyautogui
import pygetwindow as gw

CONFIG_FILE = "wifi_config.json"


class POC_Controller:
    def __init__(self, root):
        self.root = root
        self.root.title("Device Controller")
        self.ser = None
        self.last_query = ""
        self.potplayer_path = self.find_potplayer()

        # 0. UVC
        frame_uvc = tk.LabelFrame(root, text="UVC")
        frame_uvc.pack(fill="x", padx=10, pady=5)

        tk.Button(
            frame_uvc,
            text="UVCmode",
            bg="#add8e6",
            command=self.cmd_set_uvc_mode
        ).grid(row=0, column=0, padx=10, pady=5)

        tk.Button(
            frame_uvc,
            text="Open PotPlayer Preview ( UVC )",
            bg="#90ee90",
            command=self.open_potplayer_uvc
        ).grid(row=0, column=1, padx=10, pady=5)

        # 1. WiFi & IP
        frame_wifi = tk.LabelFrame(root, text="WiFi")
        frame_wifi.pack(fill="x", padx=10, pady=5)

        tk.Label(frame_wifi, text="SSID:").grid(row=0, column=0)
        self.ent_ssid = tk.Entry(frame_wifi)
        self.ent_ssid.grid(row=0, column=1)

        tk.Label(frame_wifi, text="PWD:").grid(row=0, column=2)
        self.ent_pwd = tk.Entry(frame_wifi, show="*")
        self.ent_pwd.grid(row=0, column=3)

        tk.Button(frame_wifi, text="Setting WiFi", command=self.cmd_wifi_save).grid(row=0, column=4, padx=5)

        tk.Label(frame_wifi, text="Wifi IP:").grid(row=1, column=0)
        self.lbl_ip = tk.Label(frame_wifi, text="0.0.0.0", fg="green", font=("Arial", 9, "bold"))
        self.lbl_ip.grid(row=1, column=1, sticky="w")

        tk.Button(
            frame_wifi,
            text="Open PotPlayer Preview  ( WIFI )",
            bg="#90ee90",
            command=self.open_potplayer_wifi
        ).grid(row=1, column=4, padx=5, pady=5)

        # 2. AE Control
        frame_ae = tk.LabelFrame(root, text="AE Control")
        frame_ae.pack(fill="x", padx=10, pady=5)

        tk.Button(
            frame_ae,
            text="Auto AE",
            command=lambda: self.send_cmd("command=ISP_CTRL,1,0x0012,1")
        ).grid(row=0, column=0, padx=5)

        tk.Label(frame_ae, text="Shutter:").grid(row=0, column=1)
        self.ent_shutter = tk.Entry(frame_ae, width=10)
        self.ent_shutter.grid(row=0, column=2)

        tk.Label(frame_ae, text="Gain:").grid(row=0, column=3)
        self.ent_gain = tk.Entry(frame_ae, width=10)
        self.ent_gain.grid(row=0, column=4)

        tk.Button(frame_ae, text="Manual AE", command=self.cmd_manual_ae).grid(row=0, column=5, padx=5)

        tk.Button(
            frame_ae,
            text="Get AE Info",
            command=self.cmd_get_ae_info,
            bg="#e1e1e1"
        ).grid(row=1, column=0, padx=5, pady=5)

        tk.Label(frame_ae, text="Current Shutter:").grid(row=1, column=1)
        self.lbl_cur_shutter = tk.Label(frame_ae, text="---", fg="blue", font=("Arial", 10, "bold"))
        self.lbl_cur_shutter.grid(row=1, column=2)

        tk.Label(frame_ae, text="Current Gain:").grid(row=1, column=3)
        self.lbl_cur_gain = tk.Label(frame_ae, text="---", fg="blue", font=("Arial", 10, "bold"))
        self.lbl_cur_gain.grid(row=1, column=4)

        # 3. Day / Night mode switch
        frame_mode = tk.LabelFrame(root, text="Day / Night Mode Switch")
        frame_mode.pack(fill="x", padx=10, pady=5)

        tk.Button(
            frame_mode,
            text="Night Mode",
            bg="black",
            fg="white",
            command=self.cmd_night_mode
        ).grid(row=0, column=2, padx=(20, 5))

        tk.Label(frame_mode, text="IRLED: (Duty %)").grid(row=0, column=0, padx=(5, 2))
        self.ent_irled = tk.Entry(frame_mode, width=8)
        self.ent_irled.grid(row=0, column=1, padx=(2, 20))
        self.ent_irled.insert(0, "100")

        tk.Button(
            frame_mode,
            text="Day Mode",
            bg="yellow",
            command=self.cmd_day_mode
        ).grid(row=0, column=3, padx=20)

        # 4. Manual command
        frame_action_container = tk.Frame(root)
        frame_action_container.pack(fill="x", padx=10, pady=5)

        frame_manual = tk.LabelFrame(frame_action_container, text="Manual Command Input")
        frame_manual.pack(side="left", fill="both", expand=True, padx=(0, 5))

        self.ent_manual = tk.Entry(frame_manual, width=50)
        self.ent_manual.grid(row=0, column=0, padx=5, pady=5)

        tk.Button(
            frame_manual,
            text="commit",
            command=lambda: self.send_cmd(self.ent_manual.get())
        ).grid(row=0, column=1, padx=5)

        frame_capture = tk.LabelFrame(frame_action_container, text="Image Capture")
        frame_capture.pack(side="left", fill="y", padx=(5, 0))

        tk.Button(
            frame_capture,
            text="PotPlayer Capture",
            bg="#f0ad4e",
            command=self.cmd_pot_capture
        ).pack(padx=10, pady=5)

        # 5. Log textview
        self.log_area = scrolledtext.ScrolledText(root, width=85, height=18)
        self.log_area.pack(padx=10, pady=10)

        self.load_config()
        self.init_serial()

    # ----------------------------
    # PotPlayer path
    # ----------------------------
    def find_potplayer(self):
        try:
            paths = [
                r"SOFTWARE\Clients\Media\PotPlayer64\shell\open\command",
                r"SOFTWARE\Clients\Media\PotPlayer\shell\open\command",
                r"SOFTWARE\WOW6432Node\DAUM\PotPlayer",
            ]
            for path in paths:
                try:
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path)
                    value, _ = winreg.QueryValueEx(key, "")
                    exec_path = value.split('"')[1] if '"' in value else value
                    if os.path.exists(exec_path):
                        return exec_path
                except Exception:
                    continue
        except Exception:
            pass

        default_paths = [
            r"C:\Program Files\DAUM\PotPlayer\PotPlayerMini64.exe",
            r"C:\Program Files (x86)\DAUM\PotPlayer\PotPlayerMini.exe",
        ]
        for p in default_paths:
            if os.path.exists(p):
                return p
        return ""

    # ----------------------------
    # Config
    # ----------------------------
    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    config = json.load(f)
                self.ent_ssid.insert(0, config.get("ssid", ""))
                self.ent_pwd.insert(0, config.get("pwd", ""))
                last_ip = config.get("ip", "0.0.0.0")
                self.lbl_ip.config(text=last_ip)
            except Exception:
                pass

    def save_config(self):
        config_data = {
            "ssid": self.ent_ssid.get(),
            "pwd": self.ent_pwd.get(),
            "ip": self.lbl_ip.cget("text"),
        }
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config_data, f, ensure_ascii=False, indent=2)

    # ----------------------------
    # Log parse
    # ----------------------------
    def parse_log(self, msg):
        ip_match = re.search(r"IP->\s*(\d+\.\d+\.\d+\.\d+)", msg)
        if ip_match:
            new_ip = ip_match.group(1)
            self.lbl_ip.config(text=new_ip)
            self.write_log(f"System：Get IP: {new_ip} and write to config")
            self.save_config()

        ae_match = re.search(r"result\s+0x[0-9a-fA-F]+\s+(\d+)", msg)
        if ae_match:
            value = ae_match.group(1)

            if "0x0013" in self.last_query and "ISP_CTRL,0" in self.last_query:
                self.lbl_cur_gain.config(text=value)
            elif "0x0011" in self.last_query and "ISP_CTRL,0" in self.last_query:
                self.lbl_cur_shutter.config(text=value)

    # ----------------------------
    # Buttons
    # ----------------------------
    def cmd_set_uvc_mode(self):
        self.send_cmd("command=MFMODE,3")

    def cmd_wifi_save(self):
        ssid, pwd = self.ent_ssid.get(), self.ent_pwd.get()
        self.save_config()
        self.send_cmd(f"command=WIFI,{ssid},{pwd}")
        self.root.after(3000, lambda: self.send_cmd("command=GET_IP"))

    def open_potplayer_wifi(self):
        self.root.after(2000, lambda: self.send_cmd("command=RTSP"))
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
            current_ip = config.get("ip", "0.0.0.0")
        else:
            current_ip = self.lbl_ip.cget("text")

        if current_ip == "0.0.0.0":
            self.write_log("error：no network ip connected")
            return

        rtsp_url = f"rtsp://{current_ip}:554/"
        if self.potplayer_path and os.path.exists(self.potplayer_path):
            try:
                subprocess.Popen([self.potplayer_path, rtsp_url])
                self.write_log(f"System：Open potplayer -> {rtsp_url}")
            except Exception as e:
                self.write_log(f"Error：potplayer execute failure! {e}")
        else:
            self.write_log("error：cannot find PotPlayer")

    def open_potplayer_uvc(self):
        if not (self.potplayer_path and os.path.exists(self.potplayer_path)):
            self.write_log("error：cannot find PotPlayer")
            return

        try:
            subprocess.Popen([self.potplayer_path, "/cam"])
            self.write_log("System：Start UVC preview ")
            self.root.after(1500, self._open_uvc_device_in_potplayer)
        except Exception as e:
            self.write_log(f"error：UVC preview Failure {e}")

    def _open_uvc_device_in_potplayer(self):
        try:
            pot_windows = [w for w in gw.getWindowsWithTitle("PotPlayer") if w.visible]
            if not pot_windows:
                self.write_log("error：cannot find PotPlayer window")
                return

            pot_win = pot_windows[0]
            if pot_win.isMinimized:
                pot_win.restore()
            pot_win.activate()
            time.sleep(0.3)
            pyautogui.hotkey("alt", "d")

        except Exception as e:
            self.write_log(f"error：Open Potplayer failed {e}")

    def cmd_pot_capture(self):
        try:
            pot_windows = None
            all_pot_wins = gw.getWindowsWithTitle("PotPlayer")
            for w in all_pot_wins:
                if w.visible and "PotPlayer" in w.title and "\\" not in w.title:
                    pot_windows = w
                    break

            if pot_windows:
                pot_win = pot_windows
                if pot_win.isMinimized:
                    pot_win.restore()
                pot_win.activate()
                time.sleep(0.2)
                pyautogui.hotkey("ctrl", "e")

            else:
                self.write_log("error：Open Potplayer failed")
        except Exception as e:
            self.write_log(f"Snapshot Failed ：{e}")

        controller = [w for w in gw.getWindowsWithTitle("VKP Controller") if w.visible]
        if controller:
            controller_win = controller[0]
            if controller_win.isMinimized:
                controller_win.restore()
            controller_win.activate()

    # ----------------------------
    # Serial
    # ----------------------------
    def init_serial(self):
        ports = serial.tools.list_ports.comports()
        for p in ports:
            print(p.hwid)

        target_port = next((p.device for p in ports if "USB" in p.hwid and "LOCATION" not in p.hwid), None)
        if target_port:
            try:
                self.ser = serial.Serial(target_port, 115200, timeout=0.2)
                self.write_log(f"System：connect to {target_port}")
            except Exception as e:
                self.write_log(f"error：{e}")
        else:
            self.write_log("System：Cannot find USB devices。")

    def write_log(self, msg):
        self.log_area.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {msg}\n")
        self.log_area.see(tk.END)
        self.parse_log(msg)

    def send_cmd(self, command):
        if not self.ser or not self.ser.is_open:
            self.write_log("error：Serial not connected。")
            return

        command = command.strip()
        if not command:
            return

        self.last_query = command
        self.ser.write(f"{command}\r\n".encode("utf-8"))
        self.write_log(f"TX -> {command}")
        time.sleep(0.1)

        while self.ser.in_waiting:
            line = self.ser.readline().decode("utf-8", errors="ignore").strip()
            if line:
                self.write_log(f"RX <- {line}")

    # ----------------------------
    # AE / Mode Commands
    # ----------------------------
    def cmd_manual_ae(self):
        shutter = self.ent_shutter.get().strip()
        gain = self.ent_gain.get().strip()

        self.send_cmd("command=ISP_CTRL,1,0x0012,0")
        if shutter:
            self.send_cmd(f"command=ISP_CTRL,1,0x0011,{shutter}")
        if gain:
            self.send_cmd(f"command=ISP_CTRL,1,0x0013,{gain}")

    def cmd_get_ae_info(self):
        self.send_cmd("command=ISP_CTRL,0,0x0013")
        self.root.after(300, lambda: self.send_cmd("command=ISP_CTRL,0,0x0011"))

    def cmd_night_mode(self):
        ir_value = self.ent_irled.get().strip()

        if not ir_value:
            ir_value = "100"

        try:
            ir_int = int(ir_value)
            if ir_int < 0 or ir_int > 100:
                self.write_log("Error：IRLED value please input: 0~100")
                return
        except ValueError:
            self.write_log("Error：IRLED value must be an integer")
            return

        self.send_cmd("command=ICR_CTRL,0")
        self.send_cmd(f"command=IRLED,{ir_int},{ir_int}")
        self.send_cmd("command=ISP_CTRL,1,0xF009,1")

    def cmd_day_mode(self):
        self.send_cmd("command=ICR_CTRL,1")
        self.send_cmd("command=IRLED,0,0")
        self.send_cmd("command=ISP_CTRL,1,0xF009,0")
        self.ent_irled.delete(0, tk.END)
        self.ent_irled.insert(0, "100")


if __name__ == "__main__":
    root = tk.Tk()
    app = POC_Controller(root)
    root.mainloop()
