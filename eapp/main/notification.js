const Speaker = require("speaker");
const Stream = require("stream");
const getAssetPath = require("./get-asset-path");
const { spawn: spawnProcess } = require("child_process");
const { commandNotify } = require("./proc-commands");

class Notification {
    static format = null;
    static note = null;
    static async loadNote() {
        const fs = require("fs");
        const wav = require("wav");
        const { promisify } = require("util");
        const toArray = promisify(require("stream-to-array"));
        const pathNote = getAssetPath("./notification.wav");
        const stream = fs.createReadStream(pathNote);
        const reader = new wav.Reader();

        await new Promise(resolve => {
            reader.on("format", async function (format) {
                Notification.format = format;
                Notification.note = Buffer.concat(await toArray(reader));

                resolve();
            });

            stream.pipe(reader);
        });

    }

    constructor(icon, title, message) {
        this.data = {
            title,
            message,
            icon: getAssetPath(icon),
            appID: "SitYEA"
        };
    }

    send(toast, audio) {
        if (toast) {
            const [command, ...args] = commandNotify;

            args.push(
                "--appid", this.data.appID,
                "--icon", this.data.icon,
                "--title", this.data.title,
                "--message", this.data.message
            );

            spawnProcess(command, args, {
                shell: false,
                cwd: process.cwd(),
                detached: false
            });
        }

        if (audio) {

            const speaker = new Speaker(Notification.format);

            Stream.Readable.from(Notification.note).pipe(speaker);
        }
    }
}

module.exports = Notification;