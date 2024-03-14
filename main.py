import polars as pl
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.label import Label
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.config import Config
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.graphics import Color, Rectangle, RoundedRectangle, Line
from kivy.clock import Clock


class Card(RelativeLayout):
    def __init__(self, card_text, parent_padding, **kwargs):
        super(Card, self).__init__(**kwargs)
        self.size_hint = (None, None) 
        windowWidth, windowHeight = Window.size
        self.size = (dp(windowWidth/2-parent_padding*2), dp(windowHeight/6)) 

        card = Button(text = card_text, size_hint = (1, 1), font_size = dp(16), disabled_color = "black",
                background_normal = "", background_color = (0.9, 0.9, 0.9, 0), disabled = True)
        with card.canvas.before:
            Color(0.7, 0.7, 0.7, 1)
            RoundedRectangle(pos=card.pos, size=self.size, radius=[10, 10, 10, 10])
            Color(0.8, 0.8, 0.8, 1)
            RoundedRectangle(pos=(card.pos[0]+5, card.pos[1]+5), size=(self.size[0]-10, self.size[1]-10),  radius=[10, 10, 10, 10])
        self.add_widget(card)

        expand_options_button = ToggleButton(text="•••",  size_hint=(0.05, 0.15), font_size = dp(18), pos_hint={"x":0.93, "y":0.77}, color="black",
                                       background_normal = "", background_color = (0.9, 0.9, 0.9, 0))
        self.ids["expand_options"] = expand_options_button
        expand_options_button.bind(on_release=self.update_confirm_remove_position)
        self.add_widget(expand_options_button)

        confirm_remove_button = Button(text="Confirm Remove?", size_hint=(0.3, 0.05), font_size = dp(12), pos_hint={"x":2, "y":0.8}, color="red",
                                       background_normal = "", background_color = (0.9, 0.9, 0.9, 0.4))
        self.ids["confirm_remove"] = confirm_remove_button
        self.add_widget(confirm_remove_button)
    
    def update_confirm_remove_position(self, instance):
        print(self.ids)
        confirm_button = self.ids.confirm_remove
        expand_options_button = self.ids.expand_options
        window_width, _ = Window.size
        if expand_options_button.state == "down":
            print("down")
            confirm_button.pos_hint["x"] = 0.6
            confirm_button.x = window_width * 0.6
            expand_options_button.color = (0, 0, 0, 0.3)
        else:
            print("up")
            confirm_button.pos_hint["x"] = 2
            confirm_button.x = window_width*2
            expand_options_button.color = (0, 0, 0, 1)



class FoodCardsList(BoxLayout):
    def __init__(self, **kwargs):
        super(FoodCardsList, self).__init__(**kwargs)
        # load in food data
        app_instance = App.get_running_app()
        food_df = app_instance.load_food_data()
        self.spacing=dp(10)
        card_padding=3
        self.padding=dp(card_padding)
        
        # create a card for each stored food item
        for row in food_df.rows(named=True):
            card_text = row["name"]
            card = Card(card_text, card_padding)
            self.ids["card_"+card_text] = card
            self.add_widget(card)
        
        # Create a blank label for space
        blankSpace = Label(text=" ", size_hint=(1, None), height=dp(100))
        self.add_widget(blankSpace)

class MainScreenLowerScroll(ScrollView):
    def __init__(self, **kwargs):
        super(MainScreenLowerScroll, self).__init__(**kwargs)
        foodcards = FoodCardsList()
        self.add_widget(foodcards)

class MainScreenLower(RelativeLayout):
    def update_confirm_button_position(self):
        confirm_button = self.ids.confirm_add_food_button
        toggle_button = self.ids.toggle_food_button
        window_width, _ = Window.size
        if toggle_button.state == 'down':
            confirm_button.pos_hint["right"] = 0.95
            confirm_button.x = window_width * 0.95 - confirm_button.width
            
        else:
            confirm_button.pos_hint["right"] = 0
            confirm_button.x = 0

class MainScreen(Screen):
    pass

class AddFoodInputCard(RelativeLayout):
    def __init__(self, card_label, parent_padding, **kwargs):
        super(AddFoodInputCard, self).__init__(**kwargs)
        windowWidth, windowHeight = Window.size
        self.size = (dp(windowWidth/2-parent_padding*2), dp(windowHeight/6)) 
        label = Label(text = card_label, color = "black", halign="left", valign="top", text_size=self.size, padding=(0, dp(10)))
        self.add_widget(label)
        text_input = TextInput(pos_hint={"x":0.025, "top":0.55}, size_hint=(0.95, 0.5))
        self.add_widget(text_input)

class AddFoodScreenForm(BoxLayout):
    def __init__(self, **kwargs):
        super(AddFoodScreenForm, self).__init__(**kwargs)
        self.orientation = "vertical"
        card_padding = dp(10)
        name_card = AddFoodInputCard("Name:", card_padding)
        self.add_widget(name_card)
        servings_remaining_card = AddFoodInputCard("Servings Remaining:", card_padding)
        self.add_widget(servings_remaining_card)
        servings_per_day_card = AddFoodInputCard("Servings per day:", card_padding)
        self.add_widget(servings_per_day_card)


class AddFoodScreenSaveBack(BoxLayout):
    pass


class AddFoodScreen(Screen):
    pass


class GroceryPalApp(App):
    def build(self):
        # set window size
        Window.size = (400, 600)
        # set window color
        Window.clearcolor = (0.95, 0.95, 0.95, 1)
        # Create the screen manager
        sm = ScreenManager()
        sm.add_widget(MainScreen(name='main_screen'))
        sm.add_widget(AddFoodScreen(name="add_food_screen"))
        return sm
    
    def load_food_data(self):
        # load in food data
        try:
            data = pl.read_csv("data/food_data.csv")
            return data
        except Exception as e:
            print(f"Error loading data: {e}")
            return None
        

    

if __name__ == '__main__':
    GroceryPalApp().run()