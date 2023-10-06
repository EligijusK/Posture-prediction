const fs = require("fs");
const { promisify } = require("util");
const { PATH_CALIBRATION, PATH_SETTINGS, PATH } = require("./constants");
const app = require('electron');

const fsExists = promisify(fs.exists);
const fsReadFile = promisify(fs.readFile);
const fsWriteFile = promisify(fs.writeFile);

class ConfigManager {
    constructor(settings, calibration) {
        this.settings = settings;
        this.calibration = calibration;
        this.calibrationHistory = [[...calibration]];
    }

    toJSON() { return this.settings; }

    async save() { await fsWriteFile(PATH_SETTINGS, JSON.stringify(this, undefined, "    ")); }
    async saveCalibration() { await fsWriteFile(PATH_CALIBRATION, this.calibration); }

    setSettings(settings) {
        mergeSettings(this.settings, settings);
        this.save();
    }

    async setCalibration(face) {
        const { x, y } = face;
        const { size: hsize, history } = this.settings.calibration;

        const x0 = Math.max(0, Math.min(1, x - hsize));
        const y0 = Math.max(0, Math.min(1, y - hsize));
        const x1 = Math.max(0, Math.min(1, x + hsize));
        const y1 = Math.max(0, Math.min(1, y + hsize));

        this.calibrationHistory.push([x0, y0, x1, y1]);
        this.calibrationHistory = this.calibrationHistory.slice(-history);

        const calib = this.calibrationHistory.reduce((accu, calib) => {

            accu[0] = Math.min(accu[0], calib[0]);
            accu[1] = Math.min(accu[1], calib[1]);
            accu[2] = Math.max(accu[2], calib[2]);
            accu[3] = Math.max(accu[3], calib[3]);

            return accu;
        }, [Infinity, Infinity, -Infinity, -Infinity]);

        this.calibration[0] = calib[0];
        this.calibration[1] = calib[1];
        this.calibration[2] = calib[2];
        this.calibration[3] = calib[3];

        await this.saveCalibration();
    }

    static settingsDefaults() {
        return {
            calibrationSpeed: true,
            measureEvery: 10 * 1000,
            useRealsense: -1,
            minimizeTray: true,
            camera: -1,
            sendLogs: true,
            model: {
                model: "./model",
                predictionFrames: 5,
            },
            calibration: {
                enabled: true,
                time: 5 * 60 * 1000,
                size: 0.14,
                history: 15
            },
            history: {
                bucketSize: 20,
                bucketCount: 20
            },
            takeBreak: {
                sound: true,
                toast: true,
                time: 45 * 60 * 1000
            },
            badPosture: {
                sound: true,
                toast: true,
                time: 5 * 60 * 1000
            }
        };
    }

}

function mergeSettings(source, other) {
    (function traverseSettings(source, other) {
        Object
            .keys(source)
            .forEach(key => {
                if (!(key in source && key in other)) return;
                if (typeof source[key] !== typeof other[key]) return;

                if (typeof source[key] === "object" && !(source[key] instanceof Array))
                    traverseSettings(source[key], other[key]);
                else source[key] = other[key];
            });
    })(source, other);
}

let activeConfigManager = null;

async function initConfigManager() {
    const settings = ConfigManager.settingsDefaults();
    const calibration = new Float32Array([Number.MAX_SAFE_INTEGER, Number.MAX_SAFE_INTEGER, -Number.MAX_SAFE_INTEGER, -Number.MAX_SAFE_INTEGER]);

    try {
        if (await fsExists(PATH_SETTINGS)) {
            const other = JSON.parse(await fsReadFile(PATH_SETTINGS, "UTF-8"));

            mergeSettings(settings, other);
        }
    } catch (e) { console.error(e); }

    if (await fsExists(PATH_CALIBRATION)) {
        const buffer = await fsReadFile(PATH_CALIBRATION);
        calibration.set(new Float32Array(buffer.buffer))
    }

    const man = new ConfigManager(settings, calibration);

    // console.log(PATH)
    // Main problems is path problem to config fle as expected
    await man.save();
    await man.saveCalibration();

    activeConfigManager = man;

    return man;
}

function getConfigManager() { return activeConfigManager; }

module.exports = { initConfigManager, getConfigManager };