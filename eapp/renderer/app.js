const { ipcRenderer, webFrame, remote } = require("electron");
const HistoryHourly = require("./history/history-hourly");
const HistoryTotals = require("./history/history-totals");
const initAppSettings = require("./app-settings");
const showToast = require("./show-toast");
const TOAST_LIST = require("./toast-list");

webFrame.setZoomFactor(1);

/**
 * @type {HistoryHourly}
 */
let historyHourly = null;

/**
 * @type {HistoryTotal}
 */
let historyTotals = null;

let isSimpleModel = false;
let isDebugMode = false;

/**
 * @type {CanvasRenderingContext2D}
 */
let context2d;

const canvasSize = { width: 0, height: 0 };
const camCalibration = new Float32Array([Number.MAX_SAFE_INTEGER, Number.MAX_SAFE_INTEGER, -Number.MAX_SAFE_INTEGER, -Number.MAX_SAFE_INTEGER]);
let appSettings = null;
let calibrateData = null;
const pose = new Array(17).fill(1).map(() => new Float32Array(2));

const joints = {
    CHEST: 0,
    HIP_BASE: 1,

    HEAD_BASE: 2,
    HEAD_LEFT: 3,
    HEAD_RIGHT: 4,

    SHOULDER_LEFT: 5,
    ELBOW_LEFT: 6,
    WRIST_LEFT: 7,

    SHOULDER_RIGHT: 8,
    ELBOW_RIGHT: 9,
    WRIST_RIGHT: 10,

    HIP_LEFT: 11,
    KNEE_LEFT: 12,
    FOOT_LEFT: 13,

    HIP_RIGHT: 14,
    KNEE_RIGHT: 15,
    FOOT_RIGHT: 16
};

const connections = [
    [joints.CHEST, joints.HIP_BASE],

    [joints.HIP_BASE, joints.HIP_LEFT],

    [joints.HIP_BASE, joints.HIP_RIGHT],

    [joints.CHEST, joints.SHOULDER_LEFT],
    [joints.SHOULDER_LEFT, joints.ELBOW_LEFT],
    [joints.ELBOW_LEFT, joints.WRIST_LEFT],

    [joints.CHEST, joints.SHOULDER_RIGHT],
    [joints.SHOULDER_RIGHT, joints.ELBOW_RIGHT],
    [joints.ELBOW_RIGHT, joints.WRIST_RIGHT],

    // [joints.CHEST, joints.HEAD_BASE],
    [joints.CHEST, joints.HEAD_LEFT],
    [joints.HEAD_LEFT, joints.HEAD_RIGHT],
    [joints.HEAD_RIGHT, joints.CHEST]
];

function updateCanvas(_, message) {
    calibrateData.data.set(message);
    context2d.putImageData(calibrateData, 0, 0);

    if (isSimpleModel && isDebugMode) {
        connections.forEach(([a, b]) => {
            const [x0, y0] = pose[a], [x1, y1] = pose[b];

            context2d.beginPath();
            context2d.moveTo(x0, y0);
            context2d.lineTo(x1, y1);
            context2d.strokeStyle = "cyan";
            context2d.lineWidth = 2;
            context2d.stroke();
        });
    }

    const [x1, y1, x2, y2] = camCalibration;
    if (x2 > x1 && y2 > y1) {
        const { width, height } = canvasSize;
        const w = x2 - x1, h = y2 - y1;

        context2d.beginPath();
        context2d.rect(x1 * width, y1 * height, w * width, h * height);
        context2d.strokeStyle = "red";
        context2d.lineWidth = 3;
        context2d.stroke();
    }
}

function createForm(element) {
    const type = element.getAttribute("data-form");

    const submitEmail = (function () {
        let timeout = 0;
        const textArea = element.querySelector("[name=\"mail-contents\"]");

        return function submitEmail() {
            if (timeout > Date.now()) {
                showToast(TOAST_LIST.DO_NOT_SPAM);
                return;
            };

            const form = new FormData(element);
            const contents = form.get("mail-contents");

            showToast(TOAST_LIST.MESSAGE_SENT);
            ipcRenderer.send("sysMail", contents);
            textArea.value = "";
            timeout = Date.now() + (60 * 1000);
        }
    })();

    function onSubmit() {
        switch (type) {
            case "send-mail": submitEmail(); break;
            default: console.warn("Unknown form type:", type); break;
        }

        event.preventDefault();
    }

    element.addEventListener("submit", onSubmit);
}

function changeView(view) {
    const prevView = document.body.getAttribute("view");
    if (prevView === view) return;

    document.body.setAttribute("view", view);

    if (view === "calibrate") ipcRenderer.on("comsData", updateCanvas);
    else if (prevView === "calibrate") ipcRenderer.removeListener("comsData", updateCanvas);

    ipcRenderer.send("uiView", view);

    doIframe(prevView, view, "exercises");
    doIframe(prevView, view, "workspace");
}

function doIframe(prevView, view, type) {
    if (view === type) {
        const el = document.querySelector(`[view-in="${type}"] [iframe]`);
        const iframe = document.createElement("webview");

        iframe.src = el.getAttribute("iframe");

        el.appendChild(iframe);
    } else if (prevView === type) {
        const el = document.querySelector(`[view-in="${type}"] [iframe]`);
        el.innerHTML = "";
    }
}

function createAction(element) {
    const command = element.getAttribute("data-action");
    const regexp = /([\w\d-\.]+)\:([\w\d-\.]+)/;
    const [_, action, value] = command.match(regexp);

    function onChangeValue(value, val) {
        const el = document.querySelector(`[config-key="${value}"]`);
        const multi = parseInt(el.getAttribute("config-multiplier"));
        const curValue = parseInt(el.value) * multi;
        const newValue = curValue + val * multi;
        const valMin = el.hasAttribute("min") ? parseInt(el.getAttribute("min")) * multi : -Infinity;
        const valMax = el.hasAttribute("max") ? parseInt(el.getAttribute("max")) * multi : +Infinity;

        appSettings[value] = Math.max(valMin, Math.min(valMax, newValue));
    }

    function onResetEvent(value) {
        switch (value) {
            case "history": ipcRenderer.send("historyReset"); break;
            default: console.warn(`Unknown action '${action}': '${value}'`); break;
        }
    }

    function onCameraEvent(value) {
        switch (value) {
            case "select": {
                const camValue = parseInt(element.value);
                if (camValue >= 0) ipcRenderer.send("setCamera", camValue);
            } break;
            case "calibrated":
                document.body.removeAttribute("is-calibrating");
                changeView("dashboard");
                break;
            case "type": break;
            case "reset": ipcRenderer.send("resetDevice");
            default: console.warn(`Unknown action '${action}': '${value}'`); break;
        }
    }

    function onNavigateEvent(value) {
        switch (value) {
            case "order_rs": ipcRenderer.send("openExternal", "https://sityea.io/3d"); break;
            case "sityea": ipcRenderer.send("openExternal", "https://sityea.io"); break;
            case "privacy": ipcRenderer.send("openExternal", "https://www.sityea.io/privacy-policy/"); break;
            case "terms": ipcRenderer.send("openExternal", "https://www.sityea.io/terms-and-conditions"); break;
            default: console.warn(`Unknown action '${action}': '${value}'`); break;
        }
    }

    function onWindowEvent(value) {
        switch (value) {
            case "minimize":
                ipcRenderer.send("winMinimize");
                event.preventDefault();
                break;
            default: console.warn(`Unknown action '${action}': '${value}'`); break;
        }
    }

    function onOpenFile(value) {
        ipcRenderer.once("openFile-reply", (_, { err } = {}) => {
            if (!err) return;

            alert(`File not found: '${value}'`);
        });

        ipcRenderer.send("openFile", value);
    }

    element.addEventListener("change", function () {
        if (action === "camera" && value === "type")
            ipcRenderer.send("sysRestart");
    });

    element.addEventListener("click", function () {
        switch (action) {
            case "view": changeView(value); break;
            case "add-value": onChangeValue(value, +1); break;
            case "sub-value": onChangeValue(value, -1); break;
            case "reset": onResetEvent(value); break;
            case "camera": onCameraEvent(value); break;
            case "navigate": onNavigateEvent(value); break;
            case "window": onWindowEvent(value); break;
            case "open": onOpenFile(value); break;
            default: console.warn(`Unknown action '${action}': '${value}'`); break;
        }
    });
}

function addInputValidators() {
    function addMinMaxValidator(el, min, max) {
        let prevValue = el.value;
        let newValue = prevValue;
        let validatorFailed = false;

        el.addEventListener("change", function () {
            prevValue = newValue;
            el.value = newValue;

            if (validatorFailed) {
                el.removeAttribute("invalid");
                validatorFailed = false;
            }
        });

        el.addEventListener("input", function () {
            newValue = parseInt(el.value);
            validatorFailed = true;

            if (!isFinite(newValue)) newValue = prevValue;
            else if (min !== null && newValue < min) newValue = min;
            else if (max !== null && newValue > max) newValue = max;
            else validatorFailed = false;

            if (validatorFailed) el.setAttribute("invalid", "");
            else el.removeAttribute("invalid");
        });
    }

    function addMaxlenValidator(el, validator) {
        el.addEventListener("input", function (event) {
            if (el.value.length > validator) {
                el.value = el.value.slice(0, validator);
                event.preventDefault();
            }
        });
    }

    document
        .querySelectorAll("input[type=\"number\"]")
        .forEach(el => {
            if (el.hasAttribute("maxlength")) addMaxlenValidator(el, el.getAttribute("maxlength"));
            if (el.hasAttribute("min") || el.hasAttribute("max"))
                addMinMaxValidator(el, el.getAttribute("min"), el.getAttribute("max"));
        });
}

function onUpdateHistories(_, { hourly, totals }) {
    historyHourly.updateValues(hourly);
    historyTotals.updateValues(totals);
}

function onUpdateCalibration(_, _calibration) { camCalibration.set(_calibration); }

function onUpdatePose(_, newPose) { pose.forEach((arr, i) => { arr.set(newPose[i]) }); }

function onSysInit(_, { useSimple, settings, calibration, cameraList,
    rsDims, history: { hourly, totals } }) {

    if (useSimple) document.body.setAttribute("simple-model", "");

    isSimpleModel = useSimple;

    const canvas = document.createElement("canvas");
    const container = document.getElementById("canvas-container");
    context2d = canvas.getContext("2d");

    container.appendChild(canvas);
    canvasSize.width = canvas.width = rsDims.width;
    canvasSize.height = canvas.height = rsDims.height;
    calibrateData = context2d.createImageData(rsDims.width, rsDims.height);

    appSettings = initAppSettings(settings);
    camCalibration.set(calibration);
    historyHourly = new HistoryHourly(document.getElementById("statistics-hourly"), appSettings, hourly);
    historyTotals = new HistoryTotals(document.getElementById("statistics-totals"), appSettings, totals);

    ipcRenderer.on("historyUpdate", onUpdateHistories);
    ipcRenderer.on("calibrationUpdate", onUpdateCalibration);

    if (isSimpleModel) {
        if (isDebugMode) ipcRenderer.on("updatePose", onUpdatePose);

        const select = document.getElementById("camera-list");
        select.innerHTML = "";

        cameraList.forEach(({ camera_index, camera_name }) => {
            const opt = document.createElement("option");

            opt.value = camera_index;
            opt.text = camera_name;

            if (camera_index === settings.camera) opt.selected = true;

            select.appendChild(opt);
        });
    }

    if (document.body.hasAttribute("is-calibrating")) changeView("calibrate");
}

function createListener(element) {
    const expectedType = element.getAttribute("data-listen");

    ipcRenderer.on("updateListener", function (_, { type, value }) {
        if (type !== expectedType) return;

        function onTruePosture({ trueLabel, lastFrames, posture }) {
            const postureList = document.getElementById("posture-list");
            element.setAttribute("data-posture", posture);
            element.innerText = `${trueLabel.charAt(0).toUpperCase()}${trueLabel.slice(1)}`;

            postureList.innerHTML = lastFrames
                .reverse()
                .map((label, i) => {
                    const labelUppercase = `${label.charAt(0).toUpperCase()}${label.slice(1)}`;
                    let type;

                    switch (label) {
                        case "sitting straight": type = "good"; break;
                        case "hunching":
                        case "extremely hunched":
                        case "lying down": type = "grim"; break;
                        case "lightly hunching":
                        case "partially lying": type = "poor"; break;
                        case "empty":
                        case "unknown":
                        default: type = "none"; break;
                    }

                    return `<div><span>Measurement ${i + 1}: </span><span class="posture ${type}">${labelUppercase}</span></div>`;
                })
                .join("");
        }

        switch (type) {
            case "truePosture": onTruePosture(value); break;
        }
    });

}

function onSysReady() {
    document.querySelectorAll("[data-form]").forEach(createForm);
    document.querySelectorAll("[data-listen]").forEach(createListener);
    document.body.setAttribute("is-loading", false);
    ipcRenderer.once("sysInit-reply", onSysInit);

    ipcRenderer.send("sysInit");
    addInputValidators();
    ipcRenderer.send("uiView", document.body.getAttribute("view"));
}

function onUnzipedFiled(_, progress) {
    const elProgressbar = document.querySelector("[data-proc-state] .progress");

    elProgressbar.style.width = `${progress * 100}%`;
}

function onFirstRun() {
    const elDataProcess = document.querySelector("[data-proc-state]");

    elDataProcess.setAttribute("data-proc-state", "proc_first-run");
}

function onSysProc(_, data) {
    const elProgressbar = document.querySelector("[data-proc-state] .progress");
    const elDataProcess = document.querySelector("[data-proc-state]");
    const elHasDev = document.querySelector("[has-dev]");

    elDataProcess.setAttribute("data-proc-state", data.process);
    if ("device" in data) elHasDev.setAttribute("has-dev", data.device);

    elProgressbar.style.width = null;
}

function onSysCamSelect(_, data) {
    document.body.setAttribute("view", "mode");

    /**
     * @type {HTMLFormElement}
     */
    const formCamera = document.querySelector("form[data-form='select-camera']");
    const cams = formCamera.querySelectorAll("[view-in='mode'] .camera");

    formCamera.addEventListener("submit", function () {
        const form = new FormData(formCamera);
        const camType = parseInt(form.get("cam-type"));
        event.preventDefault();

        document.body.setAttribute("view", "dashboard");
        document.body.setAttribute("is-calibrating", "");
        ipcRenderer.send("confCamSelected", camType);
    });

    cams.forEach(elCurrCam => {
        /**
         * @type {HTMLInputElement}
         */
        const elCamChange = elCurrCam.querySelector("input.cam-input");

        elCamChange.addEventListener("change", function (e) {
            cams.forEach(el => el.classList.remove("selected"));
            elCurrCam.classList.add("selected");
        });
    });
}

function onWinInit(_, { windowSize, debugMode, staticVariables }) {
    document.body.style.setProperty("--true-width", `${windowSize.width}px`);
    document.body.style.setProperty("--true-height", `${windowSize.height}px`);

    if (debugMode) document.body.setAttribute("debug", "");
    isDebugMode = debugMode;

    document.querySelectorAll("[data-static]").forEach(elem => {
        const attr = elem.getAttribute("data-static");

        if (attr in staticVariables) elem.innerText = staticVariables[attr];
    });
}

function onResize(_, { width, height }) {
    // if (global.outerWidth * 2 < global.innerWidth && global.outerHeight * 2 < global.innerHeight) return;

    // ipcRenderer.send("winFrame", {
    //     frame: {
    //         width: global.outerWidth - global.innerWidth,
    //         height: global.outerHeight - global.innerHeight
    //     }
    // });

    // document.body.style.setProperty("--true-width", `${width}px`);
    // document.body.style.setProperty("--true-height", `${height}px`);

    // historyHourly?.onResize();
    // historyTotals?.onResize();
}

window.addEventListener("DOMContentLoaded", function () {
    ipcRenderer.on("sysUnzip", onUnzipedFiled);
    ipcRenderer.once("sysFirstRun", onFirstRun);
    ipcRenderer.once("winInit-reply", onWinInit);
    ipcRenderer.once("sysFetchProc-reply", onSysProc);
    ipcRenderer.on("sysProc", onSysProc);
    ipcRenderer.on("sysCamSelect", onSysCamSelect);
    ipcRenderer.once("sysReady-reply", onSysReady);
    ipcRenderer.on("winResized", onResize);

    ipcRenderer.send("winInit");
    ipcRenderer.send("sysFetchProc");
    ipcRenderer.send("sysReady");

    document.querySelectorAll("[data-action]").forEach(createAction);
});

ipcRenderer.send("winFrame", {
    frame: {
        width: global.outerWidth - global.innerWidth,
        height: global.outerHeight - global.innerHeight
    }
});