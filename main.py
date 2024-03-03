from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.metrics import dp

from kivy.config import Config


class ConfirmAddFoodScreen(Screen):
    pass

class MainScreen(Screen):
    pass

class AddFoodScreen(Screen):
    pass

class MainScreenLower(RelativeLayout):
    def update_confirm_button_position(self):
        confirm_button = self.ids.confirm_add_food_button
        toggle_button = self.ids.toggle_food_button
        if toggle_button.state == 'down':
            confirm_button.pos_hint["right"] = 0
            confirm_button.x = 0
        else:
            confirm_button.pos_hint["right"] = 0.95
            confirm_button.x = 300
        print(confirm_button.x)


class FoodCardsList(BoxLayout):
    def __init__(self, **kwargs):
        super(FoodCardsList, self).__init__(**kwargs)

        # Create labels dynamically
        for i in range(1, 14):  # Create 13 buttons as an example
            label_text = f'Food {i}'
            label = Button(text=label_text, size_hint=(1, None), height=dp(100))
            self.add_widget(label)
        
        # Create a blank label for space
        blankSpace = Label(text=" ", size_hint=(1, None), height=dp(100))
        self.add_widget(blankSpace)


class GroceryPalApp(App):
    def build(self):
        # Create the screen manager
        sm = ScreenManager()
        sm.add_widget(MainScreen(name='main_screen'))

        return sm
    pass

if __name__ == '__main__':
    Config.set('graphics', 'width', '400')
    Config.set('graphics', 'height', '600')
    GroceryPalApp().run()