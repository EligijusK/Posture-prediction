const { ipcRenderer } = require("electron");
const {showToast} = require("./show-toast");
const TOAST_LIST = require("./toast-list");

class AppSettings {
    constructor(settings) {
        this.settings = settings;

        this._bindInputFields();
        this._bindInputToggle();
        this._bindSelections();
    }

    _save() { ipcRenderer.send("confSave", this.settings); }

    _bindSelections() {
        document
            .querySelectorAll("select[config-key]")
            .forEach(el => {
                const configKey = el.getAttribute("config-key");
                const confProps = configKey.split(".");

                Object.defineProperty(this, configKey, {
                    get: () => {
                        const { object, key } = this._getProp(confProps);
                        return object[key];
                    },
                    set: val => {
                        const { object, key } = this._getProp(confProps);
                        object[key] = val;
                        el.value = val;
                        showToast(TOAST_LIST.CHANGES_SAVED);
                        this._save();
                    }
                });

                el.addEventListener("change", () => this[configKey] = parseInt(el.value));

                el.value = this[configKey];
            });
    }

    _bindInputToggle() {
        document
            .querySelectorAll("input[config-toggle]")
            .forEach(el => {
                const configKey = el.getAttribute("config-toggle");
                const confProps = configKey.split(".");

                Object.defineProperty(this, configKey, {
                    get: () => {
                        const { object, key } = this._getProp(confProps);
                        return object[key];
                    },
                    set: val => {
                        const { object, key } = this._getProp(confProps);
                        el.checked = object[key] = val;
                        showToast(TOAST_LIST.CHANGES_SAVED);
                        this._save();
                    }
                });

                el.addEventListener("change", () => this[configKey] = el.checked);

                el.checked = this[configKey];
            });
    }

    _bindInputFields() {
        document
            .querySelectorAll("input[config-key]")
            .forEach(el => {
                const configKey = el.getAttribute("config-key");
                 const confProps = configKey.split(".");
                if(el.getAttribute("type") === "number") {
                    const confMulti = parseInt(el.getAttribute("config-multiplier"));

                    Object.defineProperty(this, configKey, {
                        get: () => {
                            const {object, key} = this._getProp(confProps);
                            return object[key];
                        },
                        set: val => {
                            const {object, key} = this._getProp(confProps);
                            object[key] = val;
                            el.value = val / confMulti;
                            showToast(TOAST_LIST.CHANGES_SAVED);
                            this._save();
                        }
                    });

                    el.addEventListener("change", () => this[configKey] = parseInt(el.value) * confMulti);

                    el.value = this[configKey] / confMulti;
                }
                else if(el.getAttribute("type") === "text")
                {
                    Object.defineProperty(this, configKey, {
                        get: () => {
                            const { object, key } = this._getProp(confProps);
                            return object[key];
                        },
                        set: val => {
                            const { object, key } = this._getProp(confProps);
                            el.checked = object[key] = val;
                            showToast(TOAST_LIST.CHANGES_SAVED);
                            this._save();
                        }
                    });

                    el.addEventListener("change", () => this[configKey] = el.value);

                    el.value = this[configKey];
                }
            });

    }

    _getProp(confProps) {
        const len = confProps.length;
        const key = confProps[len - 1];

        let object = this.settings;

        for (let i = 0; i < len - 1; i++)
            object = object[confProps[i]];

        return { object, key };
    }
}

function initAppSettings(settings) {
    return new AppSettings(settings);
}

module.exports = initAppSettings;