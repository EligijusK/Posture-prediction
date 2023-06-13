const { ipcRenderer } = require("electron");

let formPassword;

function onSubmitPassword(event) {
    ipcRenderer.send("sysPassword", "#CHECK_ACCESS#");
    event.preventDefault();
}

function onWinInit(_, { windowSize }) {
    document.body.style.setProperty("--true-width", `${windowSize.width}px`);
    document.body.style.setProperty("--true-height", `${windowSize.height}px`);

    formPassword = document.getElementById("password-form");
    formPassword.addEventListener("submit", onSubmitPassword);
}

window.addEventListener("DOMContentLoaded", function () {
    ipcRenderer.once("winInit-reply", onWinInit);
    ipcRenderer.send("winInit");
});

ipcRenderer.send("winFrame", {
    frame: {
        width: global.outerWidth - global.innerWidth,
        height: global.outerHeight - global.innerHeight
    }
});