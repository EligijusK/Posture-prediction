const os = require("os");
const sendMail = require("./mailer");
const { PATH_LOG_CONSOLE } = require("./constants");

async function sendCrashLog() {
    const contents = `
    <html>
        <body>
            <table>
                <tr>
                    <td><b>OS type:</b></td>
                    <td>${os.type()}</td>
                </tr>
                <tr>
                    <td><b>Platform:</b></td>
                    <td>${os.platform()}</td>
                </tr>
                <tr>
                    <td><b>Arch:</b></td>
                    <td>${os.arch()}</td>
                </tr>
                <tr>
                    <td><b>Release:</b></td>
                    <td>${os.release()}</td>
                </tr>
                <tr>
                    <td><b>Cwd:</b></td>
                    <td>${process.cwd()}</td>
                </tr>
                <tr>
                    <td><b>Launch Args:</b></td>
                    <td>${process.argv.join(" ")}</td>
                <tr>
            </table>
        </body>
    </html>
    `;
    await sendMail("Crash log", contents, [{ filename: "console.log", path: PATH_LOG_CONSOLE }])
}

module.exports = sendCrashLog;