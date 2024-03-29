import polars as pl
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
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
from kivy.graphics import Color, Rectangle, RoundedRectangle, Line, Ellipse
from kivy.uix.progressbar import ProgressBar
from kivy.clock import Clock


class Card(RelativeLayout):
    def __init__(self, row, parent_padding, **kwargs):
        super(Card, self).__init__(**kwargs)
        self.parent_padding = parent_padding
        self.size_hint = (None, None) 
        self.rect_outer = RoundedRectangle()
        self.rect_inner = RoundedRectangle()

        Window.bind(on_resize=self.on_size)
        Clock.schedule_once(self.update_size)

        # actual card
        card = Button(text = "", size_hint = (1, 1), font_size = dp(16), disabled_color = "black",
                background_normal = "", background_color = (0.9, 0.9, 0.9, 0), disabled = True)
        with card.canvas.before:
            Color(0.7, 0.7, 0.7, 1)
            self.rect_outer = RoundedRectangle(pos=card.pos, size=self.size, radius=[10, 10, 10, 10])
            Color(0.8, 0.8, 0.8, 1)
            self.rect_inner = RoundedRectangle(pos=(card.pos[0]+5, card.pos[1]+5), size=(self.size[0]-10, self.size[1]-10),  radius=[10, 10, 10, 10])
        self.add_widget(card)

        # image circle
        with self.canvas:
            Color(0, 0, 1, 0.4)
            ellipse_size = self.width * 0.12
            ellipse_pos = (self.width * 0.035, self.height * 0.5)
            Ellipse(pos = ellipse_pos, size = (ellipse_size, ellipse_size))

        # card main title
        main_title_pos = (self.width * 0.18, self.height * 0.67)
        main_title = Label(text=row["name"].title(), size_hint = (1, 1), text_size = self.size, font_size = dp(24),
                           pos=main_title_pos, color="black")
        self.add_widget(main_title)

        # portion remaining labels
        portion_label_pos = (self.width * 0.18, self.height * 0.5)
        servings = row["servings"]
        portion_label = Label(text = str(int(servings)) + " Servings", text_size = self.size, font_size = dp(20),
                              pos = portion_label_pos, color="black")
        self.add_widget(portion_label)

        # days remaining labels
        days_label_pos = (self.width * 0.45, self.height * 0.5)
        servings_per_day = row["servings_per_day"]
        days = servings / servings_per_day
        days_str = str(int(days)) if days % 1 == 0 else "{:.1f}".format(days)
        days_label = Label(text = "| "+days_str + " Days", text_size = self.size, font_size = dp(20),
                              pos = days_label_pos, color="black")
        self.add_widget(days_label)

        # days bar
        total_weight, serving_weight = row["total_weight"], row["serving_weight"]
        max_days = (total_weight / serving_weight) / servings_per_day
        day_bar = ProgressBar(max = max_days, value = days, size_hint=(0.9, 0.05), pos_hint={"x":0.05, "y":0.35})
        self.add_widget(day_bar)

        # control bar
        control_bar = GridLayout(cols=6, size_hint=(0.9, 0.25), pos_hint={"x":0.05, "y":0.08})
        for i in range(6):
            control_bar.add_widget(Button(text=str(i)))
        self.add_widget(control_bar)


        expand_options_button = ToggleButton(text="•••",  size_hint=(0.05, 0.15), font_size = dp(18), pos_hint={"x":0.93, "y":0.77}, color="black",
                                       background_normal = "", background_color = (0.9, 0.9, 0.9, 0))
        self.ids["expand_options"] = expand_options_button
        expand_options_button.bind(on_release=self.update_confirm_remove_position)
        self.add_widget(expand_options_button)

        confirm_remove_button = Button(text="Confirm Remove?", size_hint=(0.3, 0.05), font_size = dp(12), pos_hint={"x":2, "y":0.8}, color="red",
                                       background_normal = "", background_color = (0.9, 0.9, 0.9, 0.4))
        self.ids["confirm_remove"] = confirm_remove_button
        self.add_widget(confirm_remove_button)
    
    def on_size(self, *args, **kwargs):
        self.update_size()

    def update_size(self, *args, **kwargs): 
        window_width, window_height = Window.size
        self.size_hint = (None, None) 
        # check why this doesnt adjust with window size
        self.size = (dp(window_width - self.parent_padding * 2), dp(window_height / 5))
        self.rect_outer.pos = (0, 0) #(self.x, self.y)
        self.rect_outer.size = self.size
        self.rect_inner.pos = (5, 5)
        self.rect_inner.size = (self.width - 10, self.height - 10)

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

class FoodCardsList(GridLayout):
    def __init__(self, reset = False, **kwargs):
        super(FoodCardsList, self).__init__(**kwargs)
        # self.clear_widgets()
        # load in food data
        app_instance = App.get_running_app()
        food_df = app_instance.load_food_data()

        self.cols = 1
        self.rows = len(food_df)+1

        self.spacing=dp(10) 
        card_padding=3
        self.padding=dp(card_padding)
    
        # create a card for each stored food item
        for row in food_df.rows(named=True):
            card = Card(row, card_padding)
            self.ids["card_"+row["name"]] = card
            card.update_size()
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

class AddFoodScreenTitle(GridLayout):
    def __init__(self, **kwargs):
        super(AddFoodScreenTitle, self).__init__(**kwargs)
        self.cols = 2
        self.rows = 1
        back_button = Button(text = "<-", size_hint_x = 0.2, background_normal="", background_color = (0.9, 0.9, 0.9, 1), color="black")
        back_button.bind(on_release = self.go_to_main)
        self.add_widget(back_button)
        title = Label(text="Add Food", halign="left", valign="center", size = self.size, font_size=dp(24), color="black")
        title.bind(size=title.setter('text_size'))
        self.add_widget(title)
        # Set background color using canvas
        with self.canvas.before:
            Color(0.9, 0.9, 0.9, 1)  # Set background color (light gray)
            self.rect = Rectangle(size=self.size, pos=self.pos)

    def on_size(self, *args):
        # Update the size of the rectangle when the layout size changes
        self.rect.size = self.size

    def on_pos(self, *args):
        # Update the position of the rectangle when the layout position changes
        self.rect.pos = self.pos

    def go_to_main(self, instance):
        App.get_running_app().root.transition = SlideTransition(direction="right")
        App.get_running_app().root.current = "main_screen"
        App.get_running_app().root.transition = SlideTransition(direction="left")

class CleanTextInput(TextInput):
    def __init__(self, input_type, **kwargs):
        super(CleanTextInput, self).__init__(**kwargs)

        # set background color
        self.background_normal = ''
        self.background_active = ''
        self.background_color = (0.9, 0.9, 0.9, 0)

        # set cursor color
        self.cursor_color = "black"

        # set text 
        self.multiline = False
        self.font_size = dp(14)
        self.input_type = input_type

        # set initial underline color and color changing funcs
        self.bind(focus=self.update_line_color)     
        self.bind(pos=self.update)

    def update(self, *args):
        self.canvas.after.clear()
        self.update_line_color()

    def update_line_color(self, *args):
        line_points = [self.x, self.y, self.right, self.y]
        if self.focus:
            with self.canvas.after:
                Color(0, 0, 0, 1)  # Black color
                Line(points=line_points, width=1)

        else:
            with self.canvas.after:
                Color(0.7, 0.7, 0.7, 1)  # Grey color
                Line(points=line_points, width=1)


    def insert_text(self, substring, from_undo=False):
        # function which filters based on input type and number type
        if self.input_type == "number" and (substring.isdigit() or (substring == "." and "." not in self.text)):
            super(CleanTextInput, self).insert_text(substring, from_undo=from_undo)
        elif self.input_type == "text":
            super(CleanTextInput, self).insert_text(substring, from_undo=from_undo)
        
class AddFoodInputCard(RelativeLayout):
    def __init__(self, card_label, parent_padding, input_type="text", **kwargs):
        super(AddFoodInputCard, self).__init__(**kwargs)
        windowWidth, windowHeight = Window.size
        self.size = (dp(windowWidth/2-parent_padding*2), dp(windowHeight/6)) 
        label = Label(text = card_label, color = "black", halign="left", valign="top", text_size=self.size, padding=(0, dp(20)))
        self.add_widget(label)
        text_input = CleanTextInput(input_type, pos_hint={"x":0.025, "y":0.3}, size_hint=(0.95, 0.45))
        self.add_widget(text_input)

class AddFoodScreenForm(GridLayout):
    def __init__(self, **kwargs):
        super(AddFoodScreenForm, self).__init__(**kwargs)
        self.rows = 6
        card_padding = dp(10)
        name_card = AddFoodInputCard("Name:", card_padding)
        self.add_widget(name_card)
        servings_remaining_card = AddFoodInputCard("Servings Remaining:", card_padding, input_type="number")
        self.add_widget(servings_remaining_card)
        servings_per_day_card = AddFoodInputCard("Servings per Day:", card_padding, input_type="number")
        self.add_widget(servings_per_day_card)
        serving_weight = AddFoodInputCard("Serving Weight (g):", card_padding, input_type="number")
        self.add_widget(serving_weight)
        total_weight = AddFoodInputCard("Total Weight (g)", card_padding, input_type="number")
        self.add_widget(total_weight)
        add_image_card = Label(text="Add Image Placeholder", color="black")
        self.add_widget(add_image_card)

class AddFoodScreenSaveBack(BoxLayout):
    def __init__(self, **kwargs):
        super(AddFoodScreenSaveBack, self).__init__(**kwargs)
        # self.size_hint_y = 0.1
        back_button = Button(text="Back")
        back_button.bind(on_release = self.go_to_main)
        self.add_widget(back_button)
        save_button = Button(text="Save")
        save_button.bind(on_release = self.save_food)
        self.add_widget(save_button)

    def go_to_main(self, instance):
        App.get_running_app().root.transition = SlideTransition(direction="right")
        App.get_running_app().root.current = "main_screen"
        App.get_running_app().root.transition = SlideTransition(direction="left")
    
    def save_food(self, *args):
        # get data from form
        form = [i for i in self.parent.children if type(i).__name__ == "AddFoodScreenForm"][0]
        text_inputs = [i.children[0] for i in form.children if type(i).__name__ == "AddFoodInputCard"]
        form_dict = {}

        # put form data into a dictionary
        for i, form_input in enumerate(["total_weight", "serving_weight", "servings_per_day", 
                           "servings", "name"]):
            try:
                form_value = float(text_inputs[i].text)
            except ValueError:
                form_value = text_inputs[i].text
            form_dict[form_input] = form_value

        # read in current data and append 
        food_data = pl.read_csv("data/food_data.csv")
        form_data = pl.DataFrame(form_dict)

        # do some input checks
        if len(form_dict["name"]) == 0:
            print("Name needed")
            return
        elif form_dict["name"] in form_data["name"]:
            print("Already in list")
            return
        elif len(form_dict["servings_per_day"]) == 0:
            print("Need a servings per day")
            return
        elif len(form_dict["serving_weight"])==0:
            print("Need a serving weight")
            return
        elif len(form_dict["total_weight"]) == 0:
            print("Need a total weight")
            return
        
        # append data
        reversed_column_names = form_data.columns[::-1]
        new_food_data = pl.concat([food_data, form_data.select(reversed_column_names)])
        new_food_data.write_csv("data/food_data.csv")

        # update the food card list in main page
        main_screen_lower = [i for i in App.get_running_app().root.get_screen("main_screen").children[0].children if type(i).__name__ == "MainScreenLower"][0]
        food_card_list = [i for i in main_screen_lower.children if type(i).__name__ == "MainScreenLowerScroll"][0].children[0]
        food_card_list.__init__(reset = True)

class AddFoodScreen(Screen):
    pass

class GroceryPalApp(App):
    def build(self):
        # set window size 9:20 ratio
        Window.size = (360, 800)
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