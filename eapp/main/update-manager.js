const NotificationList = require("./notification-list");

const PRED_GOOD = "good";
const PRED_POOR = "poor";
const PRED_GRIM = "grim";
const PRED_NONE = "none";
const POSTURE_MAP = Object.freeze({ [PRED_GOOD]: 0, [PRED_POOR]: 1, [PRED_GRIM]: 2, [PRED_NONE]: 3 });


class UpdateManager {
    _takeBreak = { predictions: [], time: Date.now() };
    _badPosture = { predictions: [], time: Date.now() };
    _calibration = { isGood: true, time: Date.now() };
    _prediction = { isBusy: false, time: Date.now() };
    _view;
    _hasDevice = true;

    constructor(win, cfgMan, historyMan, ipcPython) {
        this._win = win;
        this._ipcPython = ipcPython;
        this._cfgMan = cfgMan;
        this._historyMan = historyMan

        ipcPython.on("ipc_mdl_resp", this._onResponseModel.bind(this));

        setInterval(this._update.bind(this), 1000);
    }

    setView(view) { this._view = view; }
    setHasDevice(dev) { this._hasDevice = dev; }

    _updateTakeBreak(label) { this._takeBreak.predictions.push(label !== PRED_NONE); }
    _updateBadPosture(label) { this._badPosture.predictions.push(label === PRED_POOR || label === PRED_GRIM); }

    _updateCalibration(label, face) {
        if (this._view === "calibrate") {
            if (label !== PRED_GOOD || !face) return;

            this._cfgMan.setCalibration(face);
            this._win.sendMessage("calibrationUpdate", this._cfgMan.calibration);

            return;
        }

        let isCalibrated = false;
        if (face) {
            const { x, y } = face;
            const [x1, y1, x2, y2] = this._cfgMan.calibration;

            isCalibrated = x2 > x1 && y2 > y1 && x1 <= x && x2 >= x && y1 <= y && y2 >= y;
        }

        if (!this._calibration.isGood && isCalibrated) this._calibration.isGood = true;
        else if (this._calibration.isGood && !isCalibrated) {
            this._calibration.isGood = false;
            this._calibration.time = Date.now();
        }
    }

    _onResponseModel({ label, true_label, last_frames, face, pose }) {
        this._prediction.isBusy = false;

        const { bucketSize, bucketCount } = this._cfgMan.settings.history;
        const { hourly, totals } = this._historyMan;
        const lastBucket = hourly[bucketCount - 1];
        const lastSum = lastBucket.reduce((sum, v) => sum + v);

        if (lastSum >= bucketSize) {
            const f = hourly.shift();
            hourly.push(f);
            f.fill(0);
            f[POSTURE_MAP[label]] = 1;
        } else lastBucket[POSTURE_MAP[label]]++;

        totals[POSTURE_MAP[label]] += 1;
        this._prediction.time = Date.now();

        this._updateTakeBreak(label);
        this._updateBadPosture(label);
        this._updateCalibration(label, face);

        this._historyMan.save();
        this._win.sendMessage("historyUpdate", { hourly, totals });

        if (this._view === "calibrate") {
            if (pose) this._win.sendMessage("updatePose", pose);
            this._win.sendMessage("updateListener", {
                type: "truePosture",
                value: {
                    trueLabel: true_label,
                    lastFrames: last_frames,
                    posture: label
                }
            });
        }
    }

    _update() {
        if (!this._hasDevice) return;

        const settings = this._cfgMan.settings;
        const predictionTime = this._view === "calibrate"
            ? (settings.calibrationSpeed ? 100 : settings.measureEvery)
            : settings.measureEvery;


        if (!this._prediction.isBusy && this._prediction.time + predictionTime < Date.now()) {
            this._prediction.isBusy = true;
            this._ipcPython.emit("ipc_mdl", {
                prediction_frames: settings.model.predictionFrames
            });
        }

        if (this._takeBreak.time + settings.takeBreak.time < Date.now()) {
            const predictionCount = this._takeBreak.predictions.reduce((sum, notAway) => sum += (notAway ? 1 : 0), 0);
            const ratio = predictionCount / this._takeBreak.predictions.length;

            this._takeBreak.time = Date.now();
            this._takeBreak.predictions.length = 0;

            if (ratio > 0.6) NotificationList.takeBreak.send(settings.takeBreak.toast, settings.takeBreak.sound);
        }

        if (this._badPosture.time + settings.badPosture.time < Date.now()) {
            const predictionCount = this._badPosture.predictions.reduce((sum, isPoor) => sum += (isPoor ? 1 : 0), 0);
            const ratio = predictionCount / this._badPosture.predictions.length;

            this._badPosture.time = Date.now();
            this._badPosture.predictions.length = 0;

            if (ratio > 0.6) NotificationList.poorPosture.send(settings.badPosture.toast, settings.badPosture.sound);
        }

        if (this._calibration.isGood && this._calibration.time + settings.calibration.time < Date.now()) {
            this._calibration.time = Date.now();
            NotificationList.calibrate.send(settings.calibration.toast, settings.calibration.sound);
        }
    }
}

function initUpdateManager(win, cfgMan, historyMan, ipc) {
    return new UpdateManager(win, cfgMan, historyMan, ipc);
}

module.exports = initUpdateManager;