const { ArgumentParser } = require("argparse");
const mmap = require("@raygun-nickj/mmap-io");
const fs = require("fs");
const { promisify } = require("util");
const { initConfigManager } = require("./config-man");
const AppWindow = require("./app-window");
const ProcessManager = require("./proc-manager");
const { ipcMain, shell, screen } = require("electron");
const startPythonIPC = require("./ipc");
const { DEPTH_MAX, PATH_RAM, PATH_RAM_2 } = require("./constants");
const openFile = require("open");
const initUpdateManager = require("./update-manager");
const initHistoryManager = require("./history-man");
const Access = require("./access-man");
const NotificationList = require("./notification-list");
const sendMail = require("./mailer");
const fsExists = promisify(fs.exists);
const { unzipAssets, needsUnzip } = require("./unzip-assets");
const { createWritableDirs, getSettingPathMac, getTrueSettingsPath } = require("./writable-path-utils");
const appVersion = require("./app-version");
const Console = require("console");

const parser = new ArgumentParser({ description: "SitYEA arguments", add_help: true });
parser.add_argument("--width", { default: 1440, type: "int", help: "Window size" });
parser.add_argument("--devtools", { default: 0, type: "int", help: "Open dev tools" });
parser.add_argument("--gpu", { default: 0, type: "int", help: "Allow GPU support" });
parser.add_argument("--debug", { default: 0, type: "int", help: "Debug mode" });
parser.add_argument("--simple", { default: 0, type: "int", help: "Use simple mode" });

const hdpi = screen.getPrimaryDisplay().scaleFactor;
const [args, _] = parser.parse_known_args();
const width = Math.floor(args.width / hdpi);
const fopen = promisify(fs.open);
const windowSize = { width, height: Math.round(width * (850 / 1440))  };
const [WIDTH, HEIGHT, CHANNELS] = [640, 480, 4];
const [UINT8_BYTES, FLOAT_BYTES] = [1, 4];
const BUFFER_OFFSET = WIDTH * HEIGHT * 1 * FLOAT_BYTES;
const BUFFER_SIZE = WIDTH * HEIGHT * CHANNELS * UINT8_BYTES;


async function runApp() {
    await NotificationList.init();
    const hasAccess = true; //await Access.checkAccess();
    const win = new AppWindow(windowSize);

    ipcMain.on("winInit", ev => ev.reply("winInit-reply", {
        windowSize,
        debugMode: args.debug,
        staticVariables: {
            app_ver: appVersion
        }
    }));

    ipcMain.on("openFile", async (ev, filepath) => {
        const fullpath = getTrueSettingsPath(filepath);

        if (await fsExists(fullpath)) {
            openFile(fullpath);
            ev.reply("openFile-reply");
        } else ev.reply("openFile-reply", { err: "FILE_NOT_FOUND" });
    })

    ipcMain.on("openExternal", (_, url) => shell.openExternal(url));
    win.win.on("resize", function () {
        const [width, height] = win.win.getSize();

        win.sendMessage("winResized", { width, height });
    });

    if (!hasAccess) {
        async function onCorrectPassword() { await initPostureEvaluator(win); }

        Access.addPasswordListener(onCorrectPassword);

        await win.openPasswordCheck();
    }
    else {
        if (await needsUnzip()) {
            async function onCorrectPassword() { await initPostureEvaluator(win); }

           Access.addPasswordListener(onCorrectPassword);

            await win.openFreeEntry();
        }
        else await initPostureEvaluator(win);
    }

    if (args.devtools) win.openDevTools();

}

const CAMERA_T = Object.freeze({
    CAM_NONE: -1,
    CAM_WEBCAM: 0,
    CAM_REALSENSE: 1
});

/**
 * 
 * @param {AppWindow} win 
 */
async function initPostureEvaluator(win) {
    await createWritableDirs();

    let isRendererReady = false, isSystemReady = false, isSimple = false;
    let deviceFound = false;
    let updateMan;

    let procReadyState = "proc_init";

    async function initSystem(ev) {
        isRendererReady = true;

        await unzipAssets(win);

        const manCfg = await initConfigManager(windowSize); // this is first problem

        win.win.addListener("minimize", function (event) {
            if (manCfg.settings.minimizeTray) {
                win.toTray();
                event.preventDefault();
            }
        });

        ipcMain.on("sysRestart", async () => {
            await manCfg.save();
            win.restart();
            win.restart();
        });

        manCfg.settings.useRealsense = CAMERA_T.CAM_NONE;

        if (manCfg.settings.useRealsense === CAMERA_T.CAM_NONE) {
            win.sendMessage("sysCamConfig");

            manCfg.settings.useRealsense = CAMERA_T.CAM_WEBCAM;

            manCfg.save();
        }

        isSimple = manCfg.settings.useRealsense === CAMERA_T.CAM_WEBCAM;

        const { ipc: ipcPython, port: portPython } = await startPythonIPC();

        win.sendMessage("sysProc", { process: "proc_ipc" });
        procReadyState = "proc_ipc";

        const manProc = new ProcessManager(win, manCfg);

        const ipcRS = await manProc.starRS({
            ipc: ipcPython,
            port: portPython,
            pathRam: getSettingPathMac(PATH_RAM),
            pathRam2: getSettingPathMac(PATH_RAM_2),
            camera: manCfg.settings.camera,
            useSimple: isSimple
        });

        console.log("RS process initialized.");

        ipcMain.on("resetDevice", async function (_) {
            manCfg.settings.useRealsense = -1;
            manCfg.settings.camera = -1;
            await manCfg.save();
            win.restart();
        });

        ipcMain.on("setCamera", function (_, camIndex) {
            ipcPython.emit("ipc_rs_cam", camIndex);
            manCfg.settings.camera = camIndex;
            manCfg.save();
        });

        ipcRS.on("ipc_rs_err", function ({ ex }) {
            NotificationList[ex].send(true, false);

            deviceFound = false;

            if (updateMan) updateMan.setHasDevice(deviceFound);

            win.sendMessage("sysProc", { process: "proc_cam", device: deviceFound });
        });

        ipcRS.on("ipc_rs_new_camera", function ({ ex }) {
            NotificationList[ex].send(true, false);
            win.sendMessage("sysProc", { process: "proc_cam", camera: "Connected new camera" });
        });

        const { ramPadding, dims: rsDims, depthScale, matrixK, cameraList } = await new Promise(resolve => {

            ipcRS.once("ipc_rs_resp", resolve);
            ipcRS.emit("ipc_rs");

        });

        console.log("Received RS metadata.");

        const fd = fs.openSync(getSettingPathMac(PATH_RAM_2), 'r+');

        console.log("Reading RAM file...");

        procReadyState = "proc_cam";
        deviceFound = true;
        win.sendMessage("sysProc", { process: "proc_cam", device: deviceFound });

        ipcRS.on("ipc_rs_resp", function () {
            deviceFound = true;
            if (updateMan) updateMan.setHasDevice(deviceFound);
            win.sendMessage("sysProc", { process: "proc_cam", device: deviceFound });
        });

        // /**
        //  * map( size, protection, privacy, fd [, offset = 0 [, advise = 0]] ) -> Buffer
        //  * @type {Uint8Array}
        //  */
        const ram = mmap.map(BUFFER_SIZE, mmap.PROT_READ, mmap.MAP_SHARED, fd); // offset doesn't work idk why thats why using two files is solution

        console.log("RAM file is ready.");

        const ipcMDL = await manProc.startMDL({
            ipc: ipcPython,
            port: portPython,
            maxFrames: manCfg.settings.model.predictionFrames,
            pathModel: getSettingPathMac(manCfg.settings.model.model),
            pathRam: getSettingPathMac(PATH_RAM),
            pathRam2: getSettingPathMac(PATH_RAM_2),
            width: rsDims.width,
            height: rsDims.height,
            depthScale,
            depthMax: DEPTH_MAX,
            allowGPU: args.gpu,
            useSimple: isSimple,
            ramPadding,
            matrixK
        });

        console.log("Model initialized.");

        win.sendMessage("sysProc", { process: "proc_net", device: deviceFound });
        procReadyState = "proc_net";

        console.log("Initialized history.");

        const historyMan = await initHistoryManager(win, manCfg);

        console.log("Initialized update manager.");

        updateMan = initUpdateManager(win, manCfg, historyMan, ipcMDL);

        ipcMain.on("sysMail", (_, contents) => sendMail("User review", contents));

        let activeTab;
        ipcMain.on("sysInit", ev => {
            activeTab = "dashboard";
            updateMan.setView(activeTab);
            console.log("Renderer is ready starting.");
            ev.reply("sysInit-reply", {
                rsDims,
                cameraList,
                settings: manCfg.settings,
                calibration: manCfg.calibration,
                useSimple: isSimple,
                history: {
                    hourly: historyMan.hourly,
                    totals: historyMan.totals,
                    sync: historyMan.sync
                }
            });
        });

        ipcMain.on("confSave", (_, settings) => manCfg.setSettings(settings));

        ipcMain.on("uiView", function (_, tab) {
            activeTab = tab;
            updateMan.setView(activeTab);
        });

        setInterval(function () {
            if (activeTab === "calibrate") {
                win.sendMessage("comsData", ram);
            }
        }, 1000 / 60);

        ev.reply("sysReady-reply");

        isSystemReady = true;
    }

    ipcMain.on("sysFetchProc", function (ev) {
        const payload = {
            processess: procReadyState === "proc_cam"
                ? { process: procReadyState, device: deviceFound }
                : { process: procReadyState },
            useSimple: isSimple
        };

        ev.reply("sysFetchProc-reply", payload);
    });

    ipcMain.on("sysReady", async function (ev) {
        if (!isSystemReady && !isRendererReady) await initSystem(ev);
        else if (isSystemReady) ev.reply("sysReady-reply");
    });

    await win.openPosture();
}

module.exports = runApp;