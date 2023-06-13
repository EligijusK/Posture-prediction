const Notification = require("./notification");

const NotificationList = new class NotificationList {
    /**
     * @type {Notification}
     */
    takeBreak = null;
    /**
     * @type {Notification}
     */
    poorPosture = null;
    /**
     * @type {Notification}
     */
    calibrate = null;
    /**
     * @type {Notification}
     */
    dev_none = null;
    /**
     * @type {Notification}
     */
    dev_usb = null;
    /**
     * @type {Notification}
     */
    dev_inuse = null;

    async init() {
        const icon = "./images/ico.ico";

        await Notification.loadNote();

        this.takeBreak = new Notification(icon, "Take a break", "You've been sitting too long, consider taking a break.");
        this.poorPosture = new Notification(icon, "Sit straight", "Your posture has been poor for a while - try sitting straight!");
        this.calibrate = new Notification(icon, "Check calibration", "Calibration seems to be off.");
        this.dev_none = new Notification(icon, "Device not found", "No Realsense devices connected.");
        this.dev_usb = new Notification(icon, "Missing USB 3.0 support", "Device must be connected to at least USB 3.0 port with a compatible cable.");
        this.dev_inuse = new Notification(icon, "Device in use", "Intel Realsense device is already in use.");

        Object.freeze(this);
    }
};

module.exports = NotificationList;