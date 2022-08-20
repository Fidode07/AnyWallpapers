"""
    Author: Fido_de07
    Discord: Fido_de07#9227
    My GitHub: https://github.com/Fidode07
    Project Repository: https://github.com/Fidode07/AnyWallpapers

    This program is free. You can redistribute it and/or modify. But don't remove the author's name or sell it.
    If you have any questions, please contact me.

    Not enough Performance? Don't worry. I create a C# Version of this program.
    In the Future I'll upload the C# Version on Steam.
"""
import sys

from ext.BackgroundWindows import Helper
import os
import winshell
from win32com.client import Dispatch
import psutil
import json


if __name__ == '__main__':
    if not os.path.isfile("settings.json"):
        with open("settings.json", "w", encoding="utf-8") as f:
            f.write('{ "python_path": "" }')
    if not os.path.isfile("data.json"):
        with open("data.json", "w", encoding="utf-8") as f:
            f.write('{ "last_pid": 0 }')
    last_pid: int = json.load(open("data.json", "r", encoding="utf-8"))["last_pid"]
    for proc in psutil.process_iter():
        if proc.pid == last_pid and last_pid != 0:
            print(f"{proc.name()} is running.\n")
            import tkinter, tkinter.messagebox
            root = tkinter.Tk()
            root.withdraw()
            tkinter.messagebox.showerror("Warning", "Another instance of AnyWallpapers is running. Please start the app via the tray icon in the taskbar.")
            root.destroy()
            sys.exit()

    with open("data.json", "w", encoding="utf-8") as f:
        f.write(json.dumps({"last_pid": os.getpid()}))

    desktop = winshell.desktop()
    path = os.path.join(desktop, "AnyWallpapers.lnk")
    if not os.path.isfile(path):
        target = str(os.getcwd())+r"\AnyWallpapers.exe"
        wDir = str(os.getcwd())
        icon = str(os.getcwd())+r"\src\img\logo.ico"
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(path)
        shortcut.Targetpath = target
        shortcut.WorkingDirectory = wDir
        shortcut.IconLocation = icon
        shortcut.save()

    helper = Helper()
    helper.start_helper()
