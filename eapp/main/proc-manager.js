const subproc = require("child_process");
const { commandRS, commandMDL } = require("./proc-commands");
const sendCrashLog = require("./submit-crash");


class ProcessManager {
    /**
     * @type {ChildProcessWithoutNullStreams}
     */
    _procRS = null;

    /**
     * @type {ChildProcessWithoutNullStreams}
     */
    _procMDL = null;

    constructor(win, manCfg) {
        this._win = win;
        this._manCfg = manCfg;
    }

    startMDL({ ipc, port, pathRam, pathRam2, maxFrames, pathModel, allowGPU, useSimple,
        width, height, depthScale, depthMax, matrixK, ramPadding }) {
        return new Promise(resolve => {
            ipc.on("connection", onConnect.bind(undefined, "mdl", ipc, resolve));

            const [command, ...args] = commandMDL;
            const proc = this._procMDL = subproc.spawn(command, args, {
                shell: false,
                cwd: process.cwd(),
                detached: false
            }).on("exit", async retCode => {
                if (retCode !== 0 && this._manCfg.settings.sendLogs) await sendCrashLog();

                setTimeout(() => this._win.close(), 1000)
            });

            proc.stdout.on("data", chunk => chunk.toString("utf8").split("\n").filter(x => x.length > 0).forEach(l => console.log("MDL =>", l)));
            proc.stderr.on("data", chunk => chunk.toString("utf8").split("\n").filter(x => x.length > 0).forEach(l => console.error("MDL =>", l)));
            // console.log(pathModel)
            proc.stdin.write(Buffer.from(new Uint32Array([port, ramPadding, Number(allowGPU), Number(useSimple), width, height, maxFrames]).buffer));
            proc.stdin.write(Buffer.from(new Float32Array([depthScale, depthMax]).buffer));
            proc.stdin.write(Buffer.from(new Float32Array(matrixK).buffer));
            proc.stdin.write(pathRam + "," + pathRam2);
            proc.stdin.write("\x00");
            proc.stdin.write(pathModel);
            proc.stdin.write("\x00");
        });
    }

    starRS({ ipc, port, pathRam, pathRam2, useSimple, camera }) {

        return new Promise(resolve => {
            ipc.on("connection", onConnect.bind(undefined, "rs", ipc, resolve));

            const [command, ...args] = commandRS;
            // const proc = this._procRS = subproc.spawn(command, args, {
            const proc = this._procRS = subproc.spawn(command, args, {
                shell: false,
                cwd: process.cwd(),
                detached: false,
                foreground: true
            }).on("exit", async retCode => {
                if (retCode !== 0 && this._manCfg.settings.sendLogs)
                {
                    console.log(retCode);
                    await sendCrashLog();
                }


                setTimeout(() => this._win.close(), 1000);
            });

            proc.stdout.on("data", chunk => chunk.toString("utf8").split("\n").filter(x => x.length > 0).forEach(l => console.log("RS =>", l)));
            proc.stderr.on("data", chunk => chunk.toString("utf8").split("\n").filter(x => x.length > 0).forEach(l => console.error("RS =>", l)));

            proc.stdin.write(Buffer.from(new Uint32Array([port, Number(useSimple)]).buffer));
            proc.stdin.write(Buffer.from(new Int32Array([camera]).buffer));
            proc.stdin.write(pathRam+","+pathRam2);
            proc.stdin.write("\x00");

        });
    }
}

module.exports = ProcessManager;

function onConnect(connType, ipc, resolve, sock) {
    // console.log("start");
    function onConnIPC({ type }) {
        if (type !== connType) return;

        ipc.removeListener("connection", onConnect);
        sock.removeListener("ipc_conn", onConnIPC);
        resolve(sock);
    }

    sock.on("ipc_conn", onConnIPC);


}