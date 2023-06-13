const nodemailer = require("nodemailer");

async function sendMail(subject, contents, attachments) {
    const mailAddr = "print@sityea.com";
    const mailHost = "jurginas.serveriai.lt";
    const mailPass = "eUEKCJkEyUd35H3g";

    // create reusable transporter object using the default SMTP transport
    const transporter = nodemailer.createTransport({
        host: mailHost,
        port: 465,
        secure: true, // true for 465, false for other ports
        auth: {
            user: mailAddr, // generated ethereal user
            pass: mailPass, // generated ethereal password
        },
    });

    // send mail with defined transport object
    const info = await transporter.sendMail({
        from: mailAddr, // sender address
        to: mailAddr, // list of receivers
        subject, // Subject line
        text: contents, // plain text body
        html: contents, // html body,
        attachments
    });

    console.log("Message sent:", info.messageId);
}

module.exports = sendMail;