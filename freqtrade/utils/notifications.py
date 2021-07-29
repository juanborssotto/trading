import os


def notify_critical(msg: str):
    os.system(
        f"notify-send \"{msg}\" --urgency critical -i /usr/share/icons/gnome/48x48/actions/stock_about.png")


def notify(msg: str, duration_secs: int):
    t = duration_secs * 1000
    os.system(
        f"notify-send \"{msg}\" -t {t} critical -i /usr/share/icons/gnome/48x48/actions/stock_about.png")
