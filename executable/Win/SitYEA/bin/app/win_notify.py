from win10toast import ToastNotifier

toaster = ToastNotifier()


class Notify:
    def __init__(self, title, description, app_name, icon):
        self.title = title
        self.description = description
        self.app_name = app_name
        self.icon = icon

    def send(self):
        toaster.show_toast(
            self.title, self.description, icon_path=self.icon, threaded=True)
