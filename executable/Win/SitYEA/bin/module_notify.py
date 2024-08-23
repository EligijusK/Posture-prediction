from platform import system
from argparse import ArgumentParser

argparser = ArgumentParser(prog="Notification manager")
argparser.add_argument("--appid", type=str, required=True)
argparser.add_argument("--icon", type=str, required=True)
argparser.add_argument("--title", type=str, required=True)
argparser.add_argument("--message", type=str, required=True)

args = argparser.parse_args()

if system() == "Windows":
    from app.win_notify import Notify
else:
    from notifypy import Notify

Notify(
    args.title,
    args.message,
    args.appid,
    args.icon
).send()