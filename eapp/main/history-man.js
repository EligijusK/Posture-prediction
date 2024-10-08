const fs = require("fs");
const { promisify } = require("util");
const { ipcMain } = require("electron");
const { PATH_HISTORY } = require("./constants");
const fsExists = promisify(fs.exists);
const fsReadFile = promisify(fs.readFile);
const fsWriteFile = promisify(fs.writeFile);


class HistoryManager {
    constructor(win, hourly, totals, sync) {
        this._win = win;
        this.hourly = hourly;
        this.totals = totals;
        this.sync = sync
        ipcMain.on("historyReset", this.resetHistory.bind(this));
    }

    async resetHistory(event) {
        [this.sync, this.totals, ...this.hourly].forEach(arr => arr.fill(0));
        this.sync.push("date");
        event.reply("historyUpdate", { hourly: this.hourly, totals: this.totals, sync: this.sync });
        await this.save();
    }

    async ResetSyncData()
    {
        this.sync = new Array(4).fill(0);
        this.sync.push("date");
        await this.save();
    }

    toJSON() {
        return {
            hourly: this.hourly,
            totals: this.totals,
            sync: this.sync
        };
    }

    async save() { await fsWriteFile(PATH_HISTORY, JSON.stringify(this, undefined, "    ")); }
}

async function initHistoryManager(win, cfgMan) {
    const createArray = function () { return new Array(4).fill(0); }
    const hourly = new Array(cfgMan.settings.history.bucketCount).fill(1).map(() => createArray());
    const totals = createArray();
    const sync = createArray();
    sync.push("date");
    try {
        if (await fsExists(PATH_HISTORY)) {
            const { hourly: prevHourly, totals: prevTotals, sync: prevSync } = JSON.parse(await fsReadFile(PATH_HISTORY, "UTF-8"));

            for (let i = 0, len = totals.length; i < len; i++)
                totals[i] = prevTotals[i];

            for (let i = 0, len = sync.length; i < len; i++)
                sync[i] = prevSync[i];

            for (let i = 1, len = hourly.length; i < len; i++) {
                const src = prevHourly[i], dst = hourly[i - 1];
                for (let j = 0, len2 = dst.length; j < len2; j++) {
                    dst[j] = src[j];
                }
            }
        }
    } catch (e) { }

    const man = new HistoryManager(win, hourly, totals, sync);

    await man.save();

    return man;
}

module.exports = initHistoryManager;