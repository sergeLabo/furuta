from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen




class MainScreen(Screen):
    def __init__(self, **kwargs):

        super().__init__(**kwargs)
        self.app = App.get_running_app()



class LogsScreen(Screen):
    pass



SCREENS = { 0: (MainScreen, 'Main'),
            1: (LogsScreen, 'Logs')}


class FurutaApp(App):

    def build(self):
        """Construction des écrans"""

        self.screen_manager = ScreenManager()
        for i in range(len(SCREENS)):
            self.screen_manager.add_widget(SCREENS[i][0](name=SCREENS[i][1]))


        return self.screen_manager



if __name__ == '__main__':
    FurutaApp().run()
