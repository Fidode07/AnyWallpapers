import ctypes
import json
from pathlib import Path
import os
import re
from tkinter import filedialog
import win32api
from bs4 import BeautifulSoup as Bs
import shutil
import tkinter.messagebox
import pystray
from PIL import Image
import threading
# win32gui is in pywin32. Note: Python 3.7 is maybe not compatible with win32gui.
import win32gui
import win32con
import time
import webview
from screeninfo import get_monitors
import cv2


class Helper:

    def __init__(self) -> None:
        # the screen_windows dict will look like the following:
        # 1: {'window': <webview.Window object at 0x7f8f8f8f8f8>, 'handle': <int: 0x7f8f8f8f8f8>,
        #     'name': './/DEVICES//DISPLAY1'}
        self.__booster_thread = None
        self.__screen_windows: dict = {}
        self.__screens: list = get_monitors()
        self.__screen_amount: int = len(self.__screens)
        self.__webview_booted: bool = False
        self.__ui = None
        self.__icon = None
        self.worker: int = 0
        self.all_workers: list = []
        self.__video_path: str = ""
        self.__start_booster: bool = False
        self.__current_wallpaper: str = ""
        self.__filter_types: list = ["blur", "brightness", "contrast", "grayscale", "hue-rotate",
                                     "invert", "saturate", "sepia"]
        self.blacklist: list = ["Microsoft Text Input Application", "Unbenannt ‎- Paint 3D", "Unbenannt - Paint 3D",
                                "Window", ""]
        self.__paused_screens: list = []

    def __get_dominant_color(self, img_path: str) -> dict:
        img = cv2.imread(img_path)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        color: tuple = cv2.mean(img)[:3]
        color = (color[0] + 10, color[1] + 10, color[2] + 10)
        background_color_str: str = f"rgb({color[0]}, {color[1]}, {color[2]})"
        return {"tuple": tuple(int(c) for c in color), "rgb_str": background_color_str}

    def __handle_finder(self) -> None:
        while not self.__webview_booted:
            time.sleep(0.1)

        move: int = 0
        cur_i: int = 0
        for window in self.__screen_windows.values():
            handle = win32gui.FindWindow(None, window['window'].title)
            i: int = 0
            while handle == 0:
                if handle == 0:
                    handle = win32gui.FindWindow(None, window['window'].title)
                    i += 1
                    if i > 10:
                        raise Exception("Couldn't find the window. Look's like a big problem, create an issue on "
                                        "GitHub.")
                    time.sleep(0.1)
            window['handle'] = handle
            self.__send_behind(handle)
            window['window'].hide()
            m = self.__screens[cur_i]
            win32gui.MoveWindow(handle, move, 0, m.width, m.height, True)
            move += window['window'].width
            cur_i += 1

    def __show_ui(self) -> None:
        try:
            self.__ui.show()
        except KeyError:
            self.__ui = webview.create_window("AnyWallpaper's", "src/index.html", width=1100, height=650, js_api=self)
            self.__ui.events.shown += self.__ui_shown
            self.__ui.show()

    def __ui_shown(self) -> None:
        self.__ui.events.shown -= self.__ui_shown
        try:
            self.__set_icon(win32gui.FindWindow(None, "AnyWallpaper's"), "src/img/logo.ico")
        except Exception:
            # The UI is already closed.
            pass

    def __quit(self) -> None:
        if self.__ui is not None:
            try:
                self.__ui.destroy()
            except KeyError:
                # The UI is already closed.
                pass
        for window in self.__screen_windows.values():
            try:
                window["window"].destroy()
            except KeyError:
                # The window is already closed.
                pass
        try:
            self.__icon.stop()
        except Exception:
            # This can happen if the icon doesn't exist (Cuz there was an error before it was created)
            pass
        print("INFO: The KeyError can be ignored. It's normal and happens when a window is already closed.")

    def stop_engine(self) -> None:
        self.__quit()

    def __tray_icon(self) -> None:
        image = Image.open("src/img/logo.png")
        menu = (pystray.MenuItem('Change Wallpaper', self.__show_ui), pystray.MenuItem('Quit', self.__quit))
        self.__icon = pystray.Icon(name="AnyWallpaper", icon=image, title="AnyWallpaper", menu=menu)
        self.__icon.run()

    def start_helper(self) -> None:
        for screen in self.__screens:
            window: webview.Window = webview.create_window(screen.name, "", frameless=True, width=screen.width,
                                                           height=screen.height)
            self.__screen_windows[screen.name.replace("\\", "").replace(".", "")] = {'window': window, 'handle': 0,
                                                                                     'name': screen.name}
        threading.Thread(target=self.__handle_finder).start()
        self.__ui = webview.create_window("AnyWallpaper's", "src/index.html", width=1100, height=650, js_api=self)
        self.__ui.events.shown += self.__ui_shown
        threading.Thread(target=self.__tray_icon).start()
        webview.start(func=self.__set, gui="edgechromium", debug=True)

    def log(self, msg: str) -> None:
        print(msg)

    def build_filter(self, given_filters=None) -> str:
        # The return looks like: blur(10) brightness(10) contrast(10) grayscale(10) hue-rotate(10) invert(10)
        # saturate(10) sepia(10)
        if given_filters is None:
            given_filters = {}
        filter_string: str = ""
        config: dict = json.loads(open(self.__current_wallpaper.replace("index.html", "video_config.json"), "r").read())
        for filter_type in self.__filter_types:
            if filter_type in config:
                if filter_type in given_filters:
                    filter_string += f"{filter_type}({given_filters[filter_type]})"
                else:
                    filter_string += f"{filter_type}({config[filter_type]})"
                if filter_type != self.__filter_types[-1]:
                    filter_string += " "
        return filter_string

    def close_ui(self) -> None:
        try:
            if self.__ui is not None:
                self.__ui.destroy()
        except KeyError:
            # The UI is already closed.
            pass

    def __set_icon(self, hwnd: int, ico_path: str) -> None:
        """
        Set icon for window.
        """
        ico_path = ico_path.replace('\\', '/')
        hicon = win32gui.LoadImage(0, ico_path, win32con.IMAGE_ICON, 0, 0, win32con.LR_LOADFROMFILE)
        win32gui.SendMessage(hwnd, win32con.WM_SETICON, win32con.ICON_SMALL, hicon)
        win32gui.SendMessage(hwnd, win32con.WM_SETICON, win32con.ICON_BIG, hicon)

        win32gui.SendMessage(win32gui.GetWindow(hwnd, win32con.GW_OWNER), win32con.WM_SETICON, win32con.ICON_SMALL,
                             hicon)
        win32gui.SendMessage(win32gui.GetWindow(hwnd, win32con.GW_OWNER), win32con.WM_SETICON, win32con.ICON_BIG, hicon)

    def set_yt_wallpaper(self, url: str) -> None:
        video_id: str = re.findall(r'(?<=v=)[^&#]+', url)[0]
        embed_url: str = f"https://www.youtube.com/embed/{video_id}?autoplay=1&mute=1&loop=1&playlist={video_id}"
        for w in self.__screen_windows.values():
            w["window"].load_url(embed_url)
            w["window"].show()
        if not self.__start_booster:
            self.__start_booster = True
            self.__booster_thread = threading.Thread(target=self.booster)
            self.__booster_thread.start()
        self.__current_wallpaper = ""

    def set_setting(self, wallpaper: str, setting: str, value: str, typ: str, set_json: bool) -> None:
        # If the current wallpaper is the given wallpaper we do evaluate_js and change json. Otherwise we only change
        # the json.
        # What's set_json for? oninput sends too many requests. set_json is only used onchange.
        path: str = f"wallpapers/{wallpaper}"
        if not os.path.isfile(path + "/wallpaper.json"):
            self.__show_error("Error", "The wallpaper doesn't exist.")
            return

        wallpaper_data: dict = json.loads(open(path + "/wallpaper.json", "r", encoding="utf-8").read())
        if set_json:
            setting_config: dict = json.loads(open(path + "/video_config.json", "r", encoding="utf-8").read())

            html = open("src/index.html", "r", encoding="utf-8")
            soup = Bs(html.read(), "html.parser")

            label = soup.find("label", {"id": f"span{wallpaper + setting}"})
            span = label.find("span")
            span.string = value + typ

            slider = soup.find("input", {"id": f"{wallpaper + setting}"})
            slider["value"] = value

            html.close()
            with open("src/index.html", "wb") as f:
                f.write(soup.prettify(encoding="utf-8"))

            setting_config[setting] = value + typ
            with open(path + "/video_config.json", "w", encoding="utf-8") as f:
                f.write(json.dumps(setting_config, indent=4))

        if self.__current_wallpaper == path + "/index.html":
            json_css: dict = json.loads(
                open(path + "/video_config.json", "r", encoding="utf-8").read())
            for window in self.__screen_windows.values():
                # self.__send_behind(window['handle'])
                window['window'].show()
                if setting not in self.__filter_types and setting != "rotation" and setting != "zoom":
                    key_setting = setting.title().replace("-", "")
                    key_setting = key_setting[0].lower() + key_setting[1:]
                    if "gif" in wallpaper_data["extension"]:
                        window['window'].evaluate_js(f"let video = document.getElementsByTagName('img')[0];"
                                                     f"video.style.{key_setting} = '{value + typ}';")
                    else:
                        window['window'].evaluate_js(f"let video = document.getElementsByTagName('video')[0];"
                                                     f"video.style.{key_setting} = '{value + typ}';")
                elif setting in self.__filter_types:
                    if "gif" in wallpaper_data["extension"]:
                        window['window'].evaluate_js(f"let video = document.getElementsByTagName('img')[0];"
                                                     f"video.style.filter = '{self.build_filter({setting: value + typ})}';")
                    else:
                        window['window'].evaluate_js(f"let video = document.getElementsByTagName('video')[0];"
                                                     f"video.style.filter = '{self.build_filter({setting: value + typ})}';")
                elif setting == "rotation":
                    if "gif" in wallpaper_data["extension"]:
                        window['window'].evaluate_js(f"let video = document.getElementsByTagName('img')[0];"
                                                     f"video.style.transform = 'rotate({value + typ})';")
                    else:
                        window['window'].evaluate_js(f"let video = document.getElementsByTagName('video')[0];"
                                                     f"video.style.transform = 'rotate({value + typ}) "
                                                     f"scale({json_css['zoom']})';")
                elif setting == "zoom":
                    if "gif" in wallpaper_data["extension"]:
                        window["window"].evaluate_js(f"let video = document.getElementsByTagName('img')[0];"
                                                     f"video.style.transform = 'rotate({json_css['rotation']}) "
                                                     f"scale({value + typ})';")
                    else:
                        window["window"].evaluate_js(f"let video = document.getElementsByTagName('video')[0];"
                                                     f"video.style.transform = 'rotate({json_css['rotation']}) "
                                                     f"scale({value + typ})';")

    def __show_error(self, title: str, msg: str) -> None:
        try:
            if self.__ui is not None:
                ctypes.windll.user32.MessageBoxW(0, msg, title, 0)
        except KeyError:
            # He Closed the UI
            pass

    def create_wallpaper(self, name: str) -> None:
        if not os.path.isdir("wallpapers"):
            os.mkdir("wallpapers")

        if self.__video_path.strip() == "":
            self.__show_error("Error", "You need to select a video file first.")
            return

        if not os.path.isfile(self.__video_path):
            self.__show_error("Error", "The video file doesn't exist.")
            return

        normal_name = name
        name = name.replace(" ", "-")
        # Remove Numbers and other weird characters from the name
        name = "".join(char for char in name if char.isalnum())
        # Regex Replace for weird characters (@, #, ., +, *, ~, etc)
        name = re.sub(r'[^\w]', '', name)
        name = re.sub(r'[@, #, ., +, *, ~, -]', '', name)
        other_invalid_characters = ["<", ">", ":", "\"", "/", "\\", "|", "?", "*",
                                    ".", ",", ";", "!", "=", "(", ")", "[", "]", "{", "}", "^", "%", "$", "&", "`",
                                    "~", "`", "´", "¬", "¦", "¨", "ª", "º", "¿", "¡", "¥", "£", "¢", "¤", "¥", "¦",
                                    "§", "¨", "©", "ª", "«", "¬", "­", "®", "¯", "°", "±", "²", "³", "´", "µ", "¶",
                                    "·", "¸", "¹", "º", "»", "¼", "½", "¾", "¿", "À", "Á", "Â", "Ã", "Ä", "Å", "Æ", "Ç",
                                    "È", "É", "Ê", "Ë", "Ì", "Í", "Î", "Ï", "Ð", "Ñ", "Ò", "Ó", "Ô", "Õ", "Ö", "×", "Ø",
                                    "Ù",
                                    "Ú", "Û", "Ü", "Ý", "Þ", "ß", "à", "á", "â", "ã", "ä", "å", "æ", "ç", "è", "é", "ê",
                                    "ë",
                                    "ì", "í", "î", "ï", "ð", "ñ", "ò", "ó", "ô", "õ", "ö", "÷", "ø", "ù", "ú", "û", "ü",
                                    "ý",
                                    "þ", "ÿ", "Ā", "ā", "Ă", "ă", "Ą", "ą", "Ć", "ć", "Ĉ", "ĉ", "Ċ", "ċ", "Č", "č", "Ď",
                                    "ď",
                                    "Đ", "đ", "Ē", "ē", "Ĕ", "ĕ", "Ė", "ė", "Ę", "ę", "Ě", "ě"]
        for char in other_invalid_characters:
            name = name.replace(char, "")
        name = name.lower()
        if name == "":
            self.__show_error("Error", "The name is invalid.")
            return

        if os.path.isdir(f"wallpapers/{name}"):
            self.__show_error("Error", "A wallpaper with this name already exists.")
            return

        os.mkdir(f"wallpapers/{name}")
        file_ext: str = self.__video_path.split(".")[-1]
        shutil.copy(self.__video_path, f"wallpapers/{name}/video." + file_ext)
        self.__create_wallpaper_thumbnail(name)
        dominant_color_data: dict = self.__get_dominant_color(f"wallpapers/{name}/thumbnail.png")
        self.__create_wallpaper_html(name, dominant_color_data)
        self.__create_config(video_path=f"wallpapers/{name}/video." + self.__video_path.split(".")[-1], name=name,
                             thumbnail=f"wallpapers/{name}/thumbnail.png", dominant_color_data=dominant_color_data)
        # Create .json file for the wallpaper
        with open(f"wallpapers/{name}/video_config.json", "w", encoding="utf-8") as file:
            settings: dict = {
                "min-width": "100%",
                "min-height": "100%",
                "top": "0",
                "left": "0",
                "border-radius": "0%",
                "opacity": "100%",
                "blur": "0px",
                "brightness": "100%",
                "contrast": "100%",
                "grayscale": "0%",
                "hue-rotate": "0deg",
                "invert": "0%",
                "sepia": "0%",
                "zoom": "100%",
                "saturate": "100%",
                "rotation": "0deg"
            }
            file.write(json.dumps(settings))

        self.__create_wallpaper_tag(name, normal_name)

        self.__video_path = ""

        try:
            # Reload like this: self.__ui.load_url("src/index.html"), is not working. Don't know why.
            self.__ui.evaluate_js("window.location.reload();")
        except KeyError:
            # The UI is already closed.
            pass

    def select_video_file(self) -> None:
        # Here we create a file dialog with tkinter. Which video formats are supported by modern browsers?
        # i dont know, but Edge has: mp4, webm, ogg, avi and i dont know what the others are.
        root = tkinter.Tk()
        root.iconbitmap(default="src/img/logo.ico")
        root.withdraw()

        downloads_path = str(Path.home() / "Downloads")
        file_types = ('Video Files (*.mp4;*.webm;*.ogg;*.gif)', 'Image Files (*.gif)')
        res: str = filedialog.askopenfilename(initialdir=downloads_path, title="Select Video File",
                                              filetypes=((file_types[0], '*.mp4;*.webm;*.ogg;*.gif'),))
        root.destroy()
        if res.strip() == "" or res is None:
            return

        self.__video_path = res

    def incorrect_name(self) -> None:
        self.__show_error("Error", "The name is invalid.")

    def __create_wallpaper_tag(self, name: str, original_name: str) -> None:
        html = open("src/index.html", "r", encoding="utf-8")
        soup = Bs(html, 'html.parser')

        col_sm_4 = soup.new_tag("div", oncontextmenu="show_context_menu('" + str(name) + "ContextMenu');",
                                **{'class': 'col-sm-4', 'id': str(name)})

        target_div = soup.find("div", {"id": "wallpaperContainer"})
        target_div.append(col_sm_4)

        card_tag = soup.new_tag("div", onClick=f'pywebview.api.set_wallpaper("{name}")',
                                **{'class': 'card'})

        col_sm_4.append(card_tag)

        img_tag = soup.new_tag("img", **{'class': 'card-img-top', 'src': f'../wallpapers/{name}/thumbnail.png'},
                               onClick=f'pywebview.api.set_wallpaper("{name}")',
                               style="width: 100%; height: 100%; object-fit: cover;")

        card_tag.append(img_tag)

        br = soup.new_tag("br")
        col_sm_4.append(br)

        content_menu_container = soup.find("div", {"class": "contextmenus"})

        context_menu = soup.new_tag("div", **{'class': 'hide contextMenu', 'id': str(name) + "ContextMenu"},
                                    style="position: fixed; z-index: 1000;")

        content_menu_container.append(context_menu)

        ul = soup.new_tag("ul", style="background: #030B13; padding: 5px 5px; "
                                      "box-shadow: 0 4px 8px 0 rgba(0, 0, 0, 0.2), 0 6px 20px 0 rgba(0, 0, 0, 0.19);")

        context_menu.append(ul)

        heading_li = soup.new_tag("li", style="color: grey; vertical-align: center;")
        heading_text = soup.new_tag("h6", style="text-decoration: underline; text-decoration-color: lightgrey;")
        heading_text.string = original_name

        heading_li.append(heading_text)

        edit_li = soup.new_tag("li", onClick="let tg = document.getElementById('editWallpaper" + name + "'); "
                                                                                                        "tg.style"
                                                                                                        ".display = "
                                                                                                        "'block'; "
                                                                                                        "tg.opacity = "
                                                                                                        "1;",
                               style="color: white;", **{'class': 'context-menu-list-item'})
        edit_li_text = soup.new_tag("h6")
        edit_li_text.string = "Edit"
        edit_li.append(edit_li_text)

        repair_li = soup.new_tag("li", onClick=f'pywebview.api.repair_wallpaper()',
                                 style="color: white;", **{'class': 'context-menu-list-item'})
        repair_li_text = soup.new_tag("h6")
        repair_li_text.string = "Repair"
        repair_li.append(repair_li_text)

        del_li = soup.new_tag("li", onClick=f"pywebview.api.delete_wallpaper('{name}');",
                              style="color: white;", **{'class': 'context-menu-list-item'})

        del_li_text = soup.new_tag("h6")
        del_li_text.string = "Delete"
        del_li.append(del_li_text)

        ul.append(heading_li)
        ul.append(edit_li)
        ul.append(repair_li)
        ul.append(del_li)

        card_img_overlay = soup.new_tag("div", style="max-width: 100%; max-height: 100%;",
                                        **{'class': 'card-img-overlay'})

        card_tag.append(card_img_overlay)

        h5_heading = soup.new_tag("h5", style="background: rgba(0, 0, 0, 0.7); text-align: center; padding: 10px; "
                                              "font-size: 80%; max-width: 100%; max-height: 100%; color: white;",
                                  **{'class': 'card-title'})

        h5_heading.string = original_name
        card_img_overlay.append(h5_heading)

        edit_modals_container = soup.find("div", {"id": "editPapers"})

        edit_modal = soup.new_tag("div", style="display: none;", **{'class': 'modal', 'id': f"editWallpaper{name}"})
        modal_dialog = soup.new_tag("div", **{'class': 'modal-dialog'})
        modal_content = soup.new_tag("div", **{'class': 'modal-content'})

        edit_modal.append(modal_dialog)
        modal_dialog.append(modal_content)

        modal_header = soup.new_tag("div", **{'class': 'modal-header'})
        modal_body = soup.new_tag("div", **{'class': 'modal-body'})
        modal_footer = soup.new_tag("div", **{'class': 'modal-footer'})

        modal_content.append(modal_header)
        modal_content.append(modal_body)
        modal_content.append(modal_footer)

        h4_heading = soup.new_tag("h4", **{'class': 'modal-title'})
        h4_heading.string = "Edit " + original_name

        modal_header.append(h4_heading)

        btn_close = soup.new_tag("button", **{'class': 'close btn-close', 'data-dismiss': 'modal',
                                              'aria-label': 'Close'},
                                 onclick="let tg = document.getElementById('editWallpaper" + name + "'); "
                                                                                                    "tg.style.display "
                                                                                                    "= 'none'; "
                                                                                                    "tg.opacity = 0;")

        modal_header.append(btn_close)

        input_left, label_left = self.create_range_with_label(name=name, label_str="Left", min_val=-1000,
                                                              max_val=1000, step=0.5, value=0, span_str="0%",
                                                              data_type="%", setting="left")

        input_top, label_top = self.create_range_with_label(name=name, label_str="Top", min_val=-1000,
                                                            max_val=1000, step=0.5, value=0, span_str="0%",
                                                            data_type="%", setting="top")

        input_opacity, label_opacity = self.create_range_with_label(name=name, label_str="Opacity", min_val=0,
                                                                    max_val=100, step=1, value=100, span_str="100%",
                                                                    data_type="%", setting="opacity")

        input_rotation, label_rotation = self.create_range_with_label(name=name, label_str="Rotation", min_val=0,
                                                                      max_val=360, step=1, value=0, span_str="0deg",
                                                                      data_type="deg", setting="rotation")

        input_blur, label_blur = self.create_range_with_label(name=name, label_str="Blur", min_val=0,
                                                              max_val=300, step=1, value=0, span_str="0px",
                                                              data_type="px", setting="blur")

        input_brightness, label_brightness = self.create_range_with_label(name=name, label_str="Brightness", min_val=0,
                                                                          max_val=1000, step=1, value=100,
                                                                          span_str="100%",
                                                                          data_type="%", setting="brightness")

        input_contrast, label_contrast = self.create_range_with_label(name=name, label_str="Contrast", min_val=0,
                                                                      max_val=1000, step=1, value=100,
                                                                      span_str="100%", data_type="%",
                                                                      setting="contrast")

        input_saturation, label_saturation = self.create_range_with_label(name=name, label_str="Saturation", min_val=0,
                                                                          max_val=1000, step=1, value=100,
                                                                          span_str="100%", data_type="%",
                                                                          setting="saturate")

        input_hue, label_hue = self.create_range_with_label(name=name, label_str="Hue", min_val=0,
                                                            max_val=360, step=1, value=0, span_str="0deg",
                                                            data_type="deg", setting="hue-rotate")

        input_grayscale, label_grayscale = self.create_range_with_label(name=name, label_str="Grayscale", min_val=0,
                                                                        max_val=100, step=1, value=0, span_str="0%",
                                                                        data_type="%", setting="grayscale")

        input_sepia, label_sepia = self.create_range_with_label(name=name, label_str="Sepia", min_val=0,
                                                                max_val=100, step=1, value=0, span_str="0%",
                                                                data_type="%", setting="sepia")

        input_invert, label_invert = self.create_range_with_label(name=name, label_str="Invert", min_val=0,
                                                                  max_val=100, step=1, value=0, span_str="0%",
                                                                  data_type="%", setting="invert")

        input_border_radius, label_border_radius = self.create_range_with_label(name=name, label_str="Border Radius",
                                                                                min_val=0, max_val=100, step=1,
                                                                                value=0, span_str="0%",
                                                                                data_type="%", setting="border-radius")

        input_zoom, label_zoom = self.create_range_with_label(name=name, label_str="Zoom", min_val=0,
                                                              max_val=1000, step=1, value=100, span_str="100%",
                                                              data_type="%", setting="zoom")

        # To be honest: a method would be better than this. But I'm bored.

        modal_body.append(label_left)
        modal_body.append(input_left)

        for i in range(2):
            modal_body.append(soup.new_tag("br"))

        modal_body.append(label_top)
        modal_body.append(input_top)

        for i in range(2):
            modal_body.append(soup.new_tag("br"))

        modal_body.append(label_opacity)
        modal_body.append(input_opacity)

        for i in range(2):
            modal_body.append(soup.new_tag("br"))

        modal_body.append(label_rotation)
        modal_body.append(input_rotation)

        for i in range(2):
            modal_body.append(soup.new_tag("br"))

        modal_body.append(label_blur)
        modal_body.append(input_blur)

        for i in range(2):
            modal_body.append(soup.new_tag("br"))

        modal_body.append(label_brightness)
        modal_body.append(input_brightness)

        for i in range(2):
            modal_body.append(soup.new_tag("br"))

        modal_body.append(label_contrast)
        modal_body.append(input_contrast)

        for i in range(2):
            modal_body.append(soup.new_tag("br"))

        modal_body.append(label_saturation)
        modal_body.append(input_saturation)

        for i in range(2):
            modal_body.append(soup.new_tag("br"))

        modal_body.append(label_hue)
        modal_body.append(input_hue)

        for i in range(2):
            modal_body.append(soup.new_tag("br"))

        modal_body.append(label_grayscale)
        modal_body.append(input_grayscale)

        for i in range(2):
            modal_body.append(soup.new_tag("br"))

        modal_body.append(label_sepia)
        modal_body.append(input_sepia)

        for i in range(2):
            modal_body.append(soup.new_tag("br"))

        modal_body.append(label_invert)
        modal_body.append(input_invert)

        for i in range(2):
            modal_body.append(soup.new_tag("br"))

        modal_body.append(label_border_radius)
        modal_body.append(input_border_radius)

        for i in range(2):
            modal_body.append(soup.new_tag("br"))

        modal_body.append(label_zoom)
        modal_body.append(input_zoom)

        edit_modals_container.append(edit_modal)

        html.close()

        with open("src/index.html", "wb") as f:
            f.write(soup.prettify(encoding="utf-8"))

    def repair_wallpaper(self) -> None:
        highest_time: int = 0
        for w in self.__screen_windows.values():
            window_time: int = w["window"].evaluate_js("document.getElementsByTagName('video')[0].currentTime;")
            if window_time > highest_time:
                highest_time = window_time

        for window in self.__screen_windows.values():
            self.__send_behind(window["handle"])
            window["window"].evaluate_js("let video = document.getElementsByTagName('video')[0]; video.play(); "
                                         "video.currentTime = {};".format(highest_time))

        self.__paused_screens = []

    def create_range_with_label(self, name: str, label_str: str, span_str: str, min_val: int, max_val: int,
                                value: int, step, data_type: str, setting: str) -> tuple:
        soup = Bs(open("src/index.html", "rb"), "html.parser")

        label_current = soup.new_tag("label", **{'id': 'span' + name + setting, 'style': 'padding-bottom: 10px;'})
        label_current.string = label_str
        label_current_span = soup.new_tag("span")
        label_current_span.string = span_str
        label_current.append(label_current_span)
        input_current = soup.new_tag("input", **{'class': 'slider', 'data-value-type': data_type, 'max': str(max_val),
                                                 'min': str(min_val),
                                                 'onchange': "changed('" + name + "', '" + setting + "')",
                                                 'type': 'range',
                                                 'value': str(value), 'step': str(step), 'id': name + setting,
                                                 'oninput': "update_span(this); changed('"+name+"', '"+setting+"', false);"})
        return input_current, label_current

    def __create_config(self, video_path: str, name: str, thumbnail: str, dominant_color_data: dict) -> None:
        text: json = {
            "video_path": video_path,
            "name": name,
            "thumbnail": thumbnail,
            "extension": Path(video_path).suffix,
            "rgb": dominant_color_data["rgb_str"]
        }
        with open(f"wallpapers/{name}/wallpaper.json", "w", encoding="utf-8") as file:
            file.write(json.dumps(text))

    def reload_ui(self) -> None:
        # load_url is not working, so we read the index.html file and replace the content.
        if self.__ui is not None:
            html = open("src/index.html", "r", encoding="utf-8")
            try:
                self.__ui.evualate_js(f"document.location.reload(true);")
            except KeyError:
                # The UI is already closed.
                pass

    def delete_wallpaper(self, wallpaper: str) -> None:
        if f"wallpapers/{wallpaper}/index.html" == self.__current_wallpaper:
            self.__show_error("Error", "You can't delete a wallpaper that is currently being displayed.")
            return
        try:
            shutil.rmtree(f"wallpapers/{wallpaper}")
        except Exception:
            root = tkinter.Tk()
            root.withdraw()
            tkinter.messagebox.showwarning("Warning", "Could not delete wallpaper directory.")
            root.destroy()
        # Remove the wallpaper from the index.html
        html = open("src/index.html", "r", encoding="utf-8")
        soup = Bs(html, 'html.parser')

        try:
            target_div = soup.find("div", {"id": "wallpaperContainer"})
            target_div.find("div", {"id": wallpaper}).decompose()
        except Exception:
            # If we get here, the user editet the html manually (or something went wrong).
            pass

        try:
            context_menu = soup.find("div", {"id": wallpaper + "ContextMenu"})
            context_menu.decompose()
        except Exception:
            pass

        try:
            edit_modal_container = soup.find("div", {"id": "editPapers"})
            edit_modal_container.find("div", {"id": "editWallpaper" + wallpaper}).decompose()
        except Exception:
            pass

        html.close()

        with open("src/index.html", "wb") as f:
            f.write(soup.prettify(encoding="utf-8"))

        try:
            if self.__ui is not None:
                self.__ui.evaluate_js(f"""
                    document.getElementById('{wallpaper}').remove();
                    document.getElementById('{wallpaper}ContextMenu').remove();
                """)
        except KeyError:
            # The UI is already closed.
            pass

    def __callb(self, hwnd, ctx) -> None:
        tmp_tg = win32gui.FindWindowEx(hwnd, None, "SHELLDLL_DefView", None)
        if tmp_tg != 0 and tmp_tg is not None:
            self.all_workers[0] = win32gui.FindWindowEx(None, hwnd, "WorkerW", None)

    def __send_behind(self, hwnd: int) -> None:
        prog_man = win32gui.FindWindow("Progman", "Program Manager")

        win32gui.SendMessageTimeout(prog_man, 0x52C,
                                    0, 0, win32con.SMTO_NORMAL, 1000)

        win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)

        win32gui.SetParent(hwnd, prog_man)

        self.all_workers = [0]
        win32gui.EnumWindows(self.__callb, None)

        win32gui.ShowWindow(self.all_workers[0], win32con.SW_HIDE)

        win32gui.SetParent(hwnd, prog_man)

        win32gui.ShowWindow(self.worker, win32con.SW_SHOW)

    def __enum(self, hwnd, ctx) -> None:
        shelldll = win32gui.FindWindowEx(0, 0, "SHELLDLL_DefView", None)
        if shelldll != 0:
            # Maybe SysListView32 works too? I don't know. I've read some comments about it.
            ctx[0] = win32gui.FindWindowEx(0, ctx[0], "WorkerW", None)

    def __create_wallpaper_html(self, name: str, dominant_color_data: dict) -> None:
        file_extension: str = self.__video_path.split(".")[-1]
        if file_extension != "gif":
            html: str = f"""
            <!DOCTYPE html>
            <html lang="en" dir="ltr">
              <head>
                <meta charset="utf-8">
                <title>{name}</title>
                <style>
                    body {{
                        overflow: hidden;
                        background: {dominant_color_data["rgb_str"]};
                    }}
                    
                    video {{
                        position: absolute;
                        top: 0;
                        left: 0;
                        bottom: 0;
                        right: 0;
                        width: 100%;
                        height: 100%;
                        z-index: -10;
                        object-fit: cover;
                    }}
                </style>
              </head>
              <body>
              <script>
    let video = 0;
    window.onload = function (event) {{
        video = document.getElementById("video");
    }};
</script>
                  <video src="video.{self.__video_path.split(".")[-1]}" autoplay muted loop></video>
              </body>
            </html>
            """
            with open(f"wallpapers/{name}/index.html", "w", encoding="utf-8") as file:
                file.write(html)
        else:
            html: str = f"""
            <!DOCTYPE html>
            <html lang="en" dir="ltr">
              <head>
                <meta charset="utf-8">
                <title>{name}</title>
                <style>
                    body {{
                        overflow: hidden;
                    }}
                    
                    img {{
                        position: absolute;
                        top: 0;
                        left: 0;
                        bottom: 0;
                        right: 0;
                        width: 100%;
                        height: 100%;
                        z-index: -10;
                        object-fit: cover;
                    }}
                </style>
              </head>
              <body>
              
                  <img src="video.gif" />
              </body>
            </html>
            """
            with open(f"wallpapers/{name}/index.html", "w", encoding="utf-8") as file:
                file.write(html)

    def __create_wallpaper_thumbnail(self, name: str) -> None:
        video_path: str = f"wallpapers/{name}/video." + self.__video_path.split(".")[-1]
        video: cv2.VideoCapture = cv2.VideoCapture(video_path)
        success: bool = video.isOpened()
        if not success:
            self.__show_error("Error", "The video file couldn't be opened.")
            return
        success, frame = video.read()
        if not success:
            self.__show_error("Error", "The video file couldn't be read.")
            return
        cv2.imwrite(f"wallpapers/{name}/thumbnail.png", frame)

    def set_wallpaper(self, wallpaper: str) -> None:
        if not os.path.isfile(f"wallpapers/{wallpaper}/index.html"):
            self.__show_error("Error", "The wallpaper doesn't exist.")
            return

        if not os.path.isfile(f"wallpapers/{wallpaper}/video_config.json"):
            with open(f"wallpapers/{wallpaper}/video_config.json", "w", encoding="utf-8") as file:
                settings: dict = {
                    "min-width": "100%",
                    "min-height": "100%",
                    "top": "0",
                    "left": "0",
                    "border-radius": "0%",
                    "opacity": "100%",
                    "blur": "0px",
                    "brightness": "100%",
                    "contrast": "100%",
                    "grayscale": "0%",
                    "hue-rotate": "0deg",
                    "invert": "0%",
                    "sepia": "0%",
                    "zoom": "100%",
                    "saturate": "100%",
                    "rotation": "0deg"
                }
                file.write(json.dumps(settings))

        self.load_url(f"wallpapers/{wallpaper}/index.html", f"wallpapers/{wallpaper}/video_config.json")
        if not self.__start_booster:
            self.__start_booster = True
            self.__booster_thread = threading.Thread(target=self.booster)
            self.__booster_thread.start()

    def load_url(self, url: str, css_config_path: str) -> None:
        json_css: dict = json.loads(open(css_config_path, "r", encoding="utf-8").read())
        # Okay. In the json we have all CSS Values we want to set. This Software is Open Source, that means that
        # everyone can modify it for their own needs. So we do it with for loops.
        wallpaper_data: dict = json.loads(
            open(url.replace("index.html", "wallpaper.json"), "r", encoding="utf-8").read())
        self.__current_wallpaper = url
        for window in self.__screen_windows.values():
            window['window'].load_url(url)
            self.__send_behind(window['handle'])
            window['window'].show()
            for key, value in json_css.items():
                setting = key
                if setting not in self.__filter_types and setting != "rotation" and setting != "zoom":
                    key_setting = setting.title().replace("-", "")
                    key_setting = key_setting[0].lower() + key_setting[1:]
                    if "gif" in wallpaper_data["extension"]:
                        window['window'].evaluate_js(f"let video = document.getElementsByTagName('img')[0];"
                                                     f"video.style.{key_setting} = '{value}';")
                    else:
                        window['window'].evaluate_js(f"let video = document.getElementsByTagName('video')[0];"
                                                     f"video.style.{key_setting} = '{value}';")
                elif setting in self.__filter_types:
                    if "gif" in wallpaper_data["extension"]:
                        window['window'].evaluate_js(f"let video = document.getElementsByTagName('img')[0];"
                                                     f"video.style.filter = '{self.build_filter()}';")
                    else:
                        window['window'].evaluate_js(f"let video = document.getElementsByTagName('video')[0];"
                                                     f"video.style.filter = '{self.build_filter()}';")
                elif setting == "rotation":
                    if "gif" in wallpaper_data["extension"]:
                        window['window'].evaluate_js(f"let video = document.getElementsByTagName('img')[0];"
                                                     f"video.style.transform = 'rotate({value})';")
                    else:
                        window['window'].evaluate_js(f"let video = document.getElementsByTagName('video')[0];"
                                                     f"video.style.transform = 'rotate({value}) "
                                                     f"scale({json_css['zoom']})';")
                elif setting == "zoom":
                    if "gif" in wallpaper_data["extension"]:
                        window["window"].evaluate_js(f"let video = document.getElementsByTagName('img')[0];"
                                                     f"video.style.transform = 'rotate({json_css['rotation']}) "
                                                     f"scale({value})';")
                    else:
                        window["window"].evaluate_js(f"let video = document.getElementsByTagName('video')[0];"
                                                     f"video.style.transform = 'rotate({json_css['rotation']}) "
                                                     f"scale({value})';")

    def __set(self) -> None:
        self.__webview_booted = True

    def booster(self) -> None:
        # How does the booster work? Well, it's a simple algorithm. We take all visible windows and look if they are
        # maximized or in fullscreen. If they are, we pause the Video at the screen where the background window is.
        def window_callback(hwnd: int, extra: list):
            if win32gui.IsWindowVisible(hwnd):
                title: str = win32gui.GetWindowText(hwnd)
                if title not in self.blacklist and "overlay" not in title.lower():
                    extra.append(hwnd)
            return True

        windows: list = []
        pause_state: dict = {}
        # Insert screens into the dict
        for screen in self.__screens:
            pause_state[screen.name] = False
        while True:
            if not self.__start_booster:
                return
            win32gui.EnumWindows(window_callback, windows)
            for window in windows:
                # Okay, the following is a bit of a hack. But it works. :)
                screen_monitor = self.__screens[
                    int(win32api.GetMonitorInfo(win32api.MonitorFromWindow(window))["Device"]
                        .replace("\\", "") \
                        .replace(".", "") \
                        .replace("DISPLAY", ""))
                    - 1]

                rect = win32gui.GetWindowRect(window)
                width = rect[2] - rect[0]
                height = rect[3] - rect[1]
                tup = win32gui.GetWindowPlacement(window)
                if tup[1] == win32con.SW_SHOWMAXIMIZED:
                    pause_state[screen_monitor.name] = True
                elif width == screen_monitor.width and height == screen_monitor.height:
                    pause_state[screen_monitor.name] = True
            windows.clear()
            for screen in pause_state:
                if pause_state[screen]:
                    self.__pause_video(screen)
                else:
                    self.__resume_video(screen)

            for screen in self.__screens:
                pause_state[screen.name] = False
            time.sleep(0.65)

    def __pause_video(self, screen):
        screen = screen.replace("\\", "").replace(".", "")
        if screen not in self.__paused_screens:
            self.__paused_screens.append(screen)
            window = self.__screen_windows[screen]
            window["window"].evaluate_js("let video = document.getElementsByTagName('video')[0];"
                                         "video.pause();")

    def __resume_video(self, screen):
        screen = screen.replace("\\", "").replace(".", "")
        if screen in self.__paused_screens:
            max_time: int = 0
            for w in self.__screen_windows.values():
                tmp_time: str = w["window"].evaluate_js("document.getElementsByTagName('video')[0].currentTime;")
                if int(tmp_time) > max_time:
                    max_time = int(tmp_time)
            self.__paused_screens.remove(screen)
            window = self.__screen_windows[screen]
            window["window"].evaluate_js("let video = document.getElementsByTagName('video')[0]; "
                                         "video.play(); video.currentTime = {max_time};")
