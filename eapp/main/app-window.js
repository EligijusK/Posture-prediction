const process = require("process");
const { app, ipcMain, BrowserWindow, Tray, Menu, nativeImage } = require("electron");
const getAssetPath = require("./get-asset-path");
let trayIsOpen = false;

class AppWindow {
    constructor({ width, height }) {
        const icon = getAssetPath("./images/ico.png");
        const trayIcon = getAssetPath('./images/trayIco.png');
        const win = this._win = new BrowserWindow({
            width,
            height,
            minWidth: width,
            minHeight: height,
            maxWidth: width,
            maxHeight: height,
            resizable: false,
            minimizable: true,
            title: "ChainHealth AI",
            icon,
            webPreferences: { nodeIntegration: true, contextIsolation: false, webviewTag: true }
        });

        win.setSize(width, height);

        let frameSize = { width: 0, height: 0 };

        ipcMain.on("winFrame", (_, { frame }) => {
            Object.assign(frameSize, frame);
            win.setSize(width + frame.width, height + frame.height);

            // console.log(`New size @31 ${width + frame.width}x${height + frame.height}, frame: ${frame.width}x${frame.height}`);
        });

        win.setMenu(null);

        win.on("ready-to-show", () => {
            const fnShow = () => {
                win.show();

                const _width = width + frameSize.width, _height = height + frameSize.height

                win.setSize(_width, _height);
                // console.log(`New size @43 ${_width}x${_height}, frame: ${frameSize.width}x${frameSize.height}`);
                this.sendMessage("winResized", { width, height });
                setTimeout(() => {
                    win.setSize(_width, _height);
                    // console.log(`New size @47 ${_width}x${_height}, frame: ${frameSize.width}x${frameSize.height}`);
                    this.sendMessage("winResized", { width, height });
                }, 500);
            }
            const context = Menu.buildFromTemplate([
                { label: "Show App", click: fnShow },
                { label: "Quit", click: function () { win.close(); } }
            ]);


            if(!trayIsOpen) {
                this._tray = new Tray(trayIcon);
                console.log(this.trayIsOpen)
                this._tray.setContextMenu(context);
                this._tray.on("double-click", fnShow);
            }
            trayIsOpen = true;
        });
    }

    get win() { return this._win; }

    toTray() { this._win.hide(); }

    async openFreeEntry() { await this._win.loadFile("./eapp/renderer/free-entry.html"); }
    async openPasswordCheck() { await this._win.loadFile("./eapp/renderer/password.html"); }
    async openPosture() { await this._win.loadFile("./eapp/renderer/posture.html"); }
    openDevTools() { this._win.webContents.openDevTools(); }

    sendMessage(channel, ...args) { this._win.webContents.send(channel, ...args); }
    close() { this._win.close(); }
    restart() {
        app.relaunch({ args: process.argv.slice(1) });
        app.quit();
    }
}

module.exports = AppWindow;