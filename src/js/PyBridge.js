function changed(wallpaper, setting, set_json = true) {
    let range = document.getElementById(wallpaper + setting);
    let value = range.value;
    let label = document.getElementById("span" + wallpaper + setting);
    let type = range.getAttribute("data-value-type");

    // Find span element in label and change its text to the value
    label.getElementsByTagName("span")[0].innerHTML = value + type;

    pywebview.api.set_setting(wallpaper, setting, value, type, set_json);
}

function update_span(range) {
    let value = range.value;
    let label = document.getElementById("span" + range.id);
    let type = range.getAttribute("data-value-type");

    // Find span element in label and change its text to the value
    label.getElementsByTagName("span")[0].innerHTML = value + type;
}

function alert_error(title, msg) {
    // I'm not happy with a "alert(....)" function, so let's use a "modal" instead
    // We generate a div, style it to a fixed element show it for 4 Seconds and then remove it
    let div = document.createElement("div");
    div.className = "alert alert-danger";
    div.innerHTML = "<strong>" + title + ": </strong> " + msg + "<br><br><span class='timer'>4</span>";
    div.style.position = "fixed";
    div.style.top = "0";
    div.style.left = "0";
    div.style.width = "100%";
    div.style.height = "100%";
    div.style.zIndex = "9999";
    div.style.backgroundColor = "rgba(0,0,0,0.5)";
    div.style.color = "white";
    div.style.textAlign = "center";
    div.style.verticalAlign = "middle";
    div.style.paddingTop = "20%";
    div.style.fontSize = "1.5em";
    div.style.fontWeight = "bold";
    div.style.fontFamily = "sans-serif";
    div.style.fontVariant = "small-caps";
    div.style.transition = "opacity 0.5s";
    div.style.opacity = "1";
    document.body.appendChild(div);
    // Okay, let's start the timer (And show progress in timer span element)
    let timer = document.getElementsByClassName("timer")[0];
    let i = 4;
    let interval = setInterval(function () {
        timer.innerHTML = i;
        i--;
        if (i < 0) {
            clearInterval(interval);
            div.style.opacity = "0";
            setTimeout(function () {
                document.body.removeChild(div);
            }, 500);
        }
    }, 1000);
}

function toggle_tab(tab) {
    all_tabs = document.getElementsByClassName("tab");
    for (let i = 0; i < all_tabs.length; i++) {
        if (all_tabs[i].id == tab) {
            let span = document.getElementById("tabspan"+tab);
            var wallpapersSec = document.getElementById('justNavText1');
            span.style.color = 'white';
            all_tabs[i].style.display = "block";
        } else {
            let span = document.getElementById("tabspan"+all_tabs[i].id);
            span.style.color = "grey";
            all_tabs[i].style.display = "none";
        }
    }
}