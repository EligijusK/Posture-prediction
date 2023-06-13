const http = require("http");
const sio = require("socket.io");

async function startPythonIPC() {
    let port = 5555, portFound = false;
    let ipc;

    do {
        try {
            const server = new http.Server();
            await new Promise((resolve, reject) => {
                server
                    .listen(port, "127.0.0.1")
                    .once("listening", resolve)
                    .on("error", reject);
            });
            ipc = sio(server);
            portFound = true;
        } catch (e) {
            if (e.code === "EADDRINUSE") port++;
            else throw e;
        }
    } while (!portFound);

    return { ipc, port };
}

module.exports = startPythonIPC;