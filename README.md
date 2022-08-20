<p align="center">
  <img height="auto" width="650" src="https://raw.githubusercontent.com/Fidode07/ImageHost/3ff66d345c56363c41aba681c274ca548c58bf87/%C3%9Cberschrift%20hinzuf%C3%BCgen.svg"/>
</p>

# 🖼️ AnyWallpapers 🖼️
I know what you're wondering now. "AnyWallpapers, that sounds like a bad crawler". But don't worry: it's cool. With this app you can use videos and GIFs as backgrounds. Free and open source! Also, the engine has some cool features like YouTube support, editor and more! especially for Python it's a good perfomance. Feel free to read the README, then you will learn more and be amazed.

# 👨‍💻 Requirements 👨‍💻
I could now annoy everyone and say it is only the requirements.txt. But for once I do not xD. Here you have a List with URL's:
1. <strong>.NET6</strong> (<a href="https://dotnet.microsoft.com/en-us/download/dotnet/6.0">Download Page</a>)
2. <strong>Python</strong> (Testet on 3.8, <a href="https://www.python.org/downloads/release/python-388rc1/">Download</a>)
3. <strong>WebView2 Runtime</strong> - Just download the Installer (<a href="https://developer.microsoft.com/de-de/microsoft-edge/webview2/">Download</a>)
4. <strong>Windows 10</strong> - No idea if it works on other Windows versions (Linux currently not supported)

# 📝 Usage 📝
1. <a href="https://dotnet.microsoft.com/en-us/download/dotnet/6.0">Download .NET6</a> (The Python requirements can only be installed after that)
2. <a href="https://www.python.org/downloads/release/python-388rc1/">Download Python</a> <strong>if not installed</strong>
3. Install Requirements Download the requirements with the following commands:
```
  cd location/of/project
  pip install -r requirements.txt
```
4. <a href="https://developer.microsoft.com/de-de/microsoft-edge/webview2/">Download WebView2 Runtime</a> (Installer)
5. Enjoy the Engine by start "AnyWallpapers.exe" or with:
```
  cd location/of/project
  python Engine.py
```
After starting the Engine.py 1 time or the first time start the .exe, a shortcut to the .exe file should appear on the desktop. This means that the command does not have to be executed 1 more time afterwards.
  <br><br>
<strong>Possible Errors:</strong>
1. It is possible that an error occurs at step 3. This is often due to Python and pythonnet. In this case you can simply do:
```
  pip install --pre pythonnet
```
and then repeat step 3.

2. Is AnyWallpapers.exe not working? Please check first if the following is true: The .exe is in the same folder as the Engine.py (The Engine.py should also not be separated from the src and ext folder). If this is not the case, re-download the project so that the structure is correct. If it still doesn't work after that the error is in the settings.json. Usually "python Engine.py" is executed by the .exe, however sometimes it is "python3" or whatever. Go to settings.json and set the value of Python Path to "path/to/your/python/.exe". e.g.:
```
{
  "python_path": "C:/Users/Fidode07/AppData/Local/Programs/Python/Python38/python.exe"
}
```

# 🔥 Features 🔥
1. Tray Icon
2. Multiple Screen Support
3. Video(s) are paused when another window is maximized or fullscreen
4. After 1 video is paused it will be synchronized with the others again
5. YouTube videos are also possible as background video
6. Powerful "editor" (It is rather an editor tab) to edit the video into a new dimension

# ❓ How to use? ❓
There are things that are not so obvious. Here I will explain a few things.
<br>
<h2>1. Where can I find the "Editor"?</h2>  
<p align="center">Well, that is quite simple. Just right-click on the wallpaper you want to edit. Then you should see an option called "Edit". Just click on it.</p>

<h2>2. How can I use a YouTube video as wallpaper?</h2>
<p align="center">In the sidebar you have an option called "YouTube Video Wallpaper". Click on the option and then paste the link of the YouTube video you want to have into the text field. Now just click on "Use Wallpaper" and you're done.</p>

# 🎥 The engine in use 🎥
<p align="center">
<h3>"Editor":</h3>
<a href="https://streamable.com/tnrwzk">Watch on Streamable</a>
<h3>YouTube-Video as Wallpaper:</h3>
<a href="https://streamable.com/swpox1">Watch on Streamable</a>
</p>

# 🛠 Credits 🛠
This app was developed by <a href="https://github.com/Fidode07">Fidode07</a> (Me). It would make me very happy if people fork this repo and develop it further, but still leave my credits.
