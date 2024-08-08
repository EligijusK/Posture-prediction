const { ipcRenderer, remote } = require("electron");
const { jwtDecode } = require("jwt-decode");
const { showToastError, showToast} = require("../show-toast");
const TOAST_LIST = require("../toast-list");
const dns = require('dns').promises;
class HistorySync {

    constructor(appSettings) {
        this._appSettings = appSettings;
    }

    updateValues(receivedData) {

        console.log("trying ...")

        let tempToken = this._appSettings.settings.token;
        let tokenError = false;
        if(tempToken.trim().length === 0) {
           showToastError(TOAST_LIST.ADD_TOKEN);
           tokenError = true;
        }
        else
        {
            try {
                let tokenTest = jwtDecode(this._appSettings.settings.token);
            } catch (error) {
                showToastError(TOAST_LIST.WRONG_TOKEN);
                tokenError = true;
            }
        }

        if(!tokenError) {

            let isDeviceOnline = navigator.onLine;
            if (isDeviceOnline) {

                let noErrors = true;
                let tokenData = jwtDecode(this._appSettings.settings.token);
                console.log(tokenData['id']);
                let timeSettings = (this._appSettings.settings.measureEvery / 1000);
                let getRequest = fetch('https://sityea-back-app-f9omq.ondigitalocean.app/user/get-user-by-id/' + tokenData['id'], {
                    method: 'GET',
                    headers: {
                        "Authorization": "Bearer " + this._appSettings.settings.token,
                        'Connection': 'keep-alive',
                        'Host': 'sityea-back-app-f9omq.ondigitalocean.app'
                    }
                }).then(response => response.json())
                    .then(data => {
                        console.log(data);
                        let length = data.results.length;
                        // console.log(data.results[length-1].day);
                        let lastSyncDate = Date.parse(receivedData[4]);
                        let lastDate = Date.parse(data.results[length - 1].day);
                        if (lastSyncDate < lastDate) {
                            let i = length - 1;
                            let total = [0, 0, 0, 0];
                            for (i; i > 0; i--) {
                                var array1 = [];
                                array1.push(data.results[i].correct);
                                array1.push(data.results[i].hunched);
                                array1.push(data.results[i].incorrect);
                                array1.push(data.results[i].away);

                                total = total.map(function (num, idx) {
                                    return num + (array1[idx] / timeSettings);
                                });

                                if (Date.parse(data.results[i].day) === lastSyncDate) {
                                    break;
                                }
                            }
                            ipcRenderer.send("syncTotal", total);
                        }
                    })
                    .catch(error => {
                        if (error === "401") {
                            showToastError(TOAST_LIST.WRONG_TOKEN)
                        } else {
                            console.error("Error:", error);
                        }
                        noErrors = false;
                    });

                var now = new Date();
                const data = JSON.stringify({
                    day: now.toISOString(),
                    correct: receivedData[0],
                    hunched: receivedData[1],
                    incorrect: receivedData[2],
                    away: receivedData[3]
                });

                let request = fetch('https://sityea-back-app-f9omq.ondigitalocean.app/result/create', {
                    method: 'POST',
                    body: data,
                    headers: {
                        "Authorization": "Bearer " + this._appSettings.settings.token,
                        'accept': 'application/json',
                        'Content-Type': 'application/json',
                        'Content-Length': data.length,
                        'Connection': 'keep-alive',
                        'Host': 'sityea-back-app-f9omq.ondigitalocean.app'
                        // fyi, NO need for content length
                    }
                }).then(response => response.status)
                    .then(data => {
                        if (data === 201) {
                            console.log(data);
                            ipcRenderer.send("syncHistory", now.toISOString());
                        }
                    })
                    .catch(error => {
                        if (error === "401") {
                            showToastError(TOAST_LIST.WRONG_TOKEN)
                        } else {
                            console.error("Error:", error);
                        }
                        noErrors = false;
                    });
                console.log(receivedData)
                if (noErrors)
                    showToast(TOAST_LIST.DATA_SYNCHRONIZED);
                console.log("done....")
            }
            else
            {
                showToastError(TOAST_LIST.NO_INTERNET);
            }
        }

    }

}



module.exports = HistorySync;