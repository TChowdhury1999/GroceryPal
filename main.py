import polars as pl
import os
import shutil
import requests
from datetime import datetime
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.config import Config
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.graphics import Color, Rectangle, RoundedRectangle, Line, Ellipse
from kivy.uix.progressbar import ProgressBar
from kivy.clock import Clock
from kivy.uix.popup import Popup

"""
To-do

- input ur own api key & cse id
- colors?
- icons for card buttons
- overwriting is how we edit

"""


class ControlBar(GridLayout):
    def __init__(self, food_name, is_paused, **kwargs):
        super(ControlBar, self).__init__(**kwargs)

        self.cols = 5
        self.size_hint = (0.9, 0.25)
        self.pos_hint = {"x":0.05, "y":0.08}
        self.food_name = food_name

        self.action_list = []

        initial_state = 'down' if is_paused else 'normal'
        initial_text = "||" if is_paused else "|>"
        pause_button = ToggleButton(text=initial_text, state=initial_state)
        self.ids.pause_button = pause_button
        pause_button.bind(on_release = self.on_pause)
        self.add_widget(pause_button)

        increase_button = Button(text="+1")
        increase_button.bind(on_release = self.on_increase)
        self.add_widget(increase_button)

        decrease_button = Button(text="-1")
        decrease_button.bind(on_release = self.on_decrease)
        self.add_widget(decrease_button)

        refill_button = Button(text="refill")
        refill_button.bind(on_release = self.on_refill)
        self.add_widget(refill_button)

        undo_button = Button(text="<-")
        undo_button.bind(on_release = self.on_undo)
        self.add_widget(undo_button)

    def on_increase(self, *args):
        self.action_list.append(1)
        self.change_portions(1)

    def on_decrease(self, *args):
        self.action_list.append(-1)
        self.change_portions(-1)

    def on_refill(self, *args):
        delta = self.parent.total_weight / self.parent.serving_weight
        delta = int(delta)
        self.action_list.append(delta)
        self.change_portions(delta)

    def change_portions(self, delta):
        app_instance = App.get_running_app()
        food_df = app_instance.load_food_data()
        food_df = food_df.with_columns(
            pl.when(pl.col("name") == self.food_name)
            .then(pl.col("servings") + delta)
            .otherwise(pl.col("servings"))
            .alias("servings")
        )
        food_df = food_df.with_columns(
            pl.when(pl.col("servings") < 0)
            .then(pl.lit(0))
            .otherwise(pl.col("servings"))
            .alias("servings")
        )
        food_df.write_csv("data/food_data.csv")
        self.parent.update_portions()

    def on_pause(self, *args):
        pause_button = self.ids.pause_button
        app_instance = App.get_running_app()
        food_df = app_instance.load_food_data()
        if pause_button.state == "down":
            pause_button.text = "||"
            state = True
        else:
            pause_button.text = "|>"
            state = False
        food_df = food_df.with_columns(
            pl.when(pl.col("name") == self.food_name)
            .then(pl.lit(state))
            .otherwise(pl.col("paused"))
            .alias("paused")
        )
        food_df.write_csv("data/food_data.csv")
        self.action_list.append("pause")

    def on_undo(self, *args):
        if len(self.action_list)==0:
            return
        last_action = self.action_list[-1]
        if last_action == "pause":
            pause_button = self.ids.pause_button
            if pause_button.state  == 'normal':
                pause_button.state = "down"
            else:
                pause_button.state = "normal"
            self.on_pause()
            self.action_list.pop()
        elif last_action == 1:
            self.on_decrease()
            self.action_list.pop()
        elif last_action == -1:
            self.on_increase()
            self.action_list.pop()
        else:
            # the last action is delta for refills
            [self.on_decrease() for _ in range(last_action)]
            [self.action_list.pop() for _ in range(last_action)]
        self.action_list.pop()

class Card(RelativeLayout):
    def __init__(self, row, parent_padding, **kwargs):
        super(Card, self).__init__(**kwargs)
        self.parent_padding = parent_padding
        self.size_hint = (None, None) 
        self.rect_outer = RoundedRectangle()
        self.rect_inner = RoundedRectangle()
        self.food_name = row["name"]
        self.serving_weight = row["serving_weight"]
        self.total_weight = row["total_weight"]
        self.is_paused = row["paused"]

        Window.bind(on_resize=self.on_size)
        Clock.schedule_once(self.update_size)

        # actual card
        card = Button(text = "", size_hint = (1, 1), font_size = dp(16), disabled_color = "black",
                background_normal = "", background_color = (0.9, 0.9, 0.9, 0), disabled = True)
        with card.canvas.before:
            Color(0.7, 0.7, 0.7, 1)
            self.rect_outer = RoundedRectangle(radius=[10, 10, 10, 10])
            Color(0.8, 0.8, 0.8, 1)
            self.rect_inner = RoundedRectangle(radius=[10, 10, 10, 10])
        self.add_widget(card)

        # image circle
        with self.canvas:
            Color(1, 1, 1, 1)
            self.image_circle = Ellipse()
            valid_extensions = ['jpg', 'jpeg', 'png', 'gif']  # Add more extensions if needed
            for ext in valid_extensions:
                image_path = f"data/images/{self.food_name}.{ext}"
                if os.path.exists(image_path):
                    self.image_circle.source = image_path
                    break

        # card main title
        main_title = Label(text=self.food_name.title(), size_hint = (None, None), text_size = self.size, font_size = dp(24),
                           color="black")
        self.ids.main_title = main_title
        self.add_widget(main_title)

        # portion remaining labels
        servings = row["servings"]
        servings_per_day = row["servings_per_day"]
        days = servings / servings_per_day
        days_str = str(int(round(days * 2) / 2) if round(days * 2) % 2 == 0 else round(days * 2) / 2)
        portion_label = Label(text = str(int(servings)) + " Servings | " + days_str + " Days", text_size = self.size, font_size = dp(20), color="black")
        self.ids.portion_label = portion_label
        self.add_widget(portion_label)

        # days bar
        total_weight, serving_weight = row["total_weight"], row["serving_weight"]
        max_days = (total_weight / serving_weight) / servings_per_day
        day_bar = ProgressBar(max = max_days, value = days, size_hint=(0.9, 0.05), pos_hint={"x":0.05, "y":0.35})
        self.ids.day_bar = day_bar
        self.add_widget(day_bar)

        # control bar
        control_bar = ControlBar(row["name"], self.is_paused)
        self.add_widget(control_bar)


        expand_options_button = ToggleButton(text="•••",  size_hint=(0.05, 0.15), font_size = dp(18), pos_hint={"x":0.9, "y":0.77}, color="black",
                                       background_normal = "", background_color = (0.9, 0.9, 0.9, 0))
        self.ids["expand_options"] = expand_options_button
        expand_options_button.bind(on_release=self.update_confirm_remove_position)
        self.add_widget(expand_options_button)

        confirm_remove_button = Button(text="Delete Food?", size_hint=(0.25, 0.05), font_size = dp(12), pos_hint={"x":2, "y":0.82}, color="red",
                                       background_normal = "", background_color = (0.9, 0.9, 0.9, 0.97))
        confirm_remove_button.bind(on_release = self.remove_card)
        self.ids["confirm_remove"] = confirm_remove_button
        self.add_widget(confirm_remove_button)
    
    def on_size(self, *args, **kwargs):
        self.update_size()

    def update_size(self, *args, **kwargs):
        window_width, window_height = Window.size
        self.size_hint = (None, None) 
        self.size = (dp(window_width - (self.parent_padding * 2)), dp(window_height / 5))

        # set card rectangle
        self.rect_outer.pos = (0, 0) 
        self.rect_outer.size = self.size
        self.rect_inner.pos = ((1-0.95)/2*self.width, (1-0.93)/2*self.height)
        self.rect_inner.size = (0.95*self.width, 0.93*self.height)

        # set image circle 
        self.image_circle.pos = (0.05 * self.width, 0.45 * self.height)
        self.image_circle.size = (0.2 * self.width, 0.2 * (9/4) * self.height)

        # set card main title
        self.ids.main_title.text_size = (self.width, self.height)
        self.ids.main_title.size = self.ids.main_title.text_size
        self.ids.main_title.pos = (self.image_circle.pos[0] + self.image_circle.size[0] + 0.025*self.width, 0.7*self.height)

        # set portion remaining label
        self.ids.portion_label.text_size = (self.width, self.height)
        self.ids.portion_label.size = self.ids.portion_label.text_size
        self.ids.portion_label.pos = (self.image_circle.pos[0] + self.image_circle.size[0] + 0.025*self.width, 0.55*self.height)

    def update_portions(self):
        app_instance = App.get_running_app()
        food_df = app_instance.load_food_data()
        filtered_df = food_df.filter(pl.col("name")==self.food_name)
        servings = filtered_df["servings"][0]
        servings_per_day = filtered_df["servings_per_day"][0]

        # update servings
        days = servings / servings_per_day
        days_str = str(int(round(days * 2) / 2) if round(days * 2) % 2 == 0 else round(days * 2) / 2)
        self.ids.portion_label.text = str(int(servings)) + " Servings | " + days_str + " Days"
        self.ids.day_bar.value = days

    def update_confirm_remove_position(self, instance):
        confirm_button = self.ids.confirm_remove
        expand_options_button = self.ids.expand_options
        window_width, _ = Window.size
        if expand_options_button.state == "down":
            confirm_button.pos_hint["x"] = 0.625
            confirm_button.x = window_width * 0.625
            expand_options_button.color = (0, 0, 0, 0.3)
        else:
            confirm_button.pos_hint["x"] = 2
            confirm_button.x = window_width*2
            expand_options_button.color = (0, 0, 0, 1)

    def remove_card(self, *args, **kwargs):
        food_data = App.get_running_app().load_food_data()
        updated_food_data = food_data.filter(pl.col("name") != self.food_name)
        updated_food_data.write_csv("data/food_data.csv")
        self.parent.__init__()
        removed_food_popup = Popup(title = "Food Deleted!",
                            content=Label(text=f"Removed {self.food_name}"),
                            size_hint=(0.8, 0.3))
        removed_food_popup.open()

class FoodCardsList(GridLayout):
    def __init__(self, **kwargs):
        super(FoodCardsList, self).__init__(**kwargs)
        # load in food data
        app_instance = App.get_running_app()
        food_df = app_instance.load_food_data()

        # reset children
        self.children = []

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
        self.font_size = self.width/8
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
        label = Label(text = card_label, color = "black", halign="left", valign="top", text_size=self.size,
                      font_size=self.width/20, padding=(0, dp(20)), pos_hint={"x":0.05, "y":0})
        self.add_widget(label)
        text_input = CleanTextInput(input_type, pos_hint={"x":0.025, "y":0.25}, size_hint=(0.95, 0.32))
        self.add_widget(text_input)

class AddFoodScreenForm(GridLayout):
    def __init__(self, **kwargs):
        super(AddFoodScreenForm, self).__init__(**kwargs)
        self.rows = 5
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

class AddImageSearchBar(BoxLayout):
    def __init__(self, **kwargs):
        super(AddImageSearchBar, self).__init__(**kwargs)   
        self.size_hint_x = 0.9
        self.size_hint_y = 0.15 
        self.pos_hint = {"center_x" : 0.5}
        self.orientation = "horizontal"

        # search text bar
        search_bar = TextInput(size_hint_x = 0.7, cursor_color="black")
        self.ids.search_bar = search_bar
        self.add_widget(search_bar)

        # blank space
        blank_space = Label(text="", color =  (0.9, 0.9, 0.9, 1), size_hint_x = 0.02)
        self.add_widget(blank_space)

        # search button
        search_button = Button(text="Search", size_hint_x = 0.26, pos_hint = {"center_x": 0.85}, color="black", background_color="D2DFF3", 
                               background_normal="false")
        search_button.bind(on_release = self.search_images)
        self.add_widget(search_button)

        # blank space
        blank_space = Label(text="", color =  (0.9, 0.9, 0.9, 1), size_hint_x = 0.02)
        self.add_widget(blank_space)
    
    def search_images(self, *args, **kwargs):
        # get the text from the search box
        search_query = self.ids.search_bar.text
        print(search_query)
        app = App.get_running_app()

        # get links to images of this food
        image_urls = app.get_image_urls(search_query)

        # download the first 3
        for count, image_url in enumerate(image_urls):
            app.download_image(image_url, f"data/images/image_cache/cache_image_{count}.png")
        
        # show these images
        image_grid = self.parent.ids.image_grid
        image_grid.images_loaded = True
        for i in range(3):
            toggle_button = image_grid.ids[f"image_option_{i}"]
            toggle_button.set_image(f"data/images/image_cache/cache_image_{i}.png")

class ImageToggleButton(ToggleButton):
    def __init__(self, **kwargs):
        super(ImageToggleButton, self).__init__(**kwargs)

    def set_image(self, image_path):
        self.image_widget = Image(source = image_path, size = (self.width*.9, self.height * .9), 
                                  pos = (self.pos[0] + self.width*.05, self.pos[1]+ self.height*.05))
        self.add_widget(self.image_widget)

class ImageGrid(BoxLayout):
    def __init__(self, **kwargs):
        super(ImageGrid, self).__init__(**kwargs)   
        self.orientation = "horizontal"    
        self.size_hint_y = 0.65
        self.size_hint_x = 0.9
        self.pos_hint = {"center_x" : 0.5}
        group = "image_options"
        self.images_loaded = False

        for i in range(3):
            image_option = ImageToggleButton(size_hint_y = 0.8, pos_hint = {"center_y": 0.5}, group=group)
            self.ids[f"image_option_{i}"] = image_option
            self.add_widget(image_option)
    
    def get_selected_image(self):
        for i in range(3):
            image_option = self.ids[f"image_option_{i}"]
            if image_option.state == 'down':
                return i
        return None
        
class ImageDiv(BoxLayout):
    def __init__(self, **kwargs):
        super(ImageDiv, self).__init__(**kwargs)

        self.orientation="vertical"

        search_label = Label(text= "Select Image for Food", color="black", size_hint_y = 0.2)
        self.add_widget(search_label)

        image_search_bar = AddImageSearchBar()
        self.add_widget(image_search_bar)

        image_grid = ImageGrid()
        self.ids.image_grid = image_grid
        self.add_widget(image_grid)

    def update_rect(self, instance, value):
        # Update the position and size of the rectangle
        self.rect.pos = (self.x+self.rect_padding/2, self.y+self.rect_padding/2)
        self.rect.size = (self.width - self.rect_padding, self.height - self.rect_padding)

class AddFoodScreenSaveBack(BoxLayout):
    def __init__(self, **kwargs):
        super(AddFoodScreenSaveBack, self).__init__(**kwargs)
        back_button = Button(text="Back")
        back_button.bind(on_release = self.go_to_main)
        self.add_widget(back_button)
        save_button = Button(text="Save")
        save_button.bind(on_release = self.save_food)
        self.add_widget(save_button)

    def go_to_main(self, *args, **kwargs):
        App.get_running_app().root.transition = SlideTransition(direction="right")
        App.get_running_app().root.current = "main_screen"
        App.get_running_app().root.transition = SlideTransition(direction="left")
    
    def save_food(self, *args):

        # get data from form
        form = [i for i in self.parent.children if type(i).__name__ == "AddFoodScreenForm"][0]
        text_inputs = [i.children[0] for i in form.children if type(i).__name__ == "AddFoodInputCard"]
        form_dict = {}

        # add in hidden cols
        form_dict["paused"] = False

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
            name_needed_popup = Popup(title = "Could not save new food",
                                      content=Label(text="Your new food needs a name!"),
                                      size_hint=(0.8, 0.3))
            name_needed_popup.open()
            return
        elif form_dict["name"] in food_data["name"]:
            print("Already in list")
            already_in_list_popup = Popup(title = "Could not save new food",
                                          content=Label(text="This food is already in your foods!"),
                                          size_hint=(0.8, 0.3))
            already_in_list_popup.open()
            return
        elif len(str(form_dict["servings_per_day"])) == 0:
            print("Need a servings per day")
            servings_per_day_popup = Popup(title = "Could not save new food",
                                           content=Label(text="Need to know how many you eat a day!"),
                                           size_hint=(0.8, 0.3))
            servings_per_day_popup.open()
            return
        elif len(str(form_dict["serving_weight"]))==0:
            print("Need a serving weight")
            serving_weight_popup = Popup(title = "Could not save new food",
                                         content=Label(text="Need to know how much a serving weighs!"),
                                         size_hint=(0.8, 0.3))
            serving_weight_popup.open()
            return
        elif len(str(form_dict["total_weight"])) == 0:
            print("Need a total weight")
            total_weight_popup = Popup(title = "Could not save new food",
                                       content=Label(text="Need to know how much a new purchase \n of the food weighs!"),
                                       size_hint=(0.8, 0.3))
            total_weight_popup.open()
            return

        # append data
        reversed_column_names = form_data.columns[::-1]
        new_food_data = pl.concat([food_data, form_data.select(reversed_column_names)])
        new_food_data.write_csv("data/food_data.csv")

        # add image
        image_div = [i for i in self.parent.children if type(i).__name__ == "ImageDiv"][0]
        image_grid = [i for i in image_div.children if type(i).__name__ == "ImageGrid"][0]
        # check if image was searched
        if image_grid.images_loaded:
            # get selected image
            selected_image = image_grid.get_selected_image()
            # check if image was selected
            if selected_image != None:
                # save selected image into images with correct filename
                print(selected_image)
                food_name = form_dict["name"]
                shutil.copy(f"data/images/image_cache/cache_image_{selected_image}.png", 
                            f"data/images/{food_name}.png")

        # update the food card list in main page
        main_screen_lower = [i for i in App.get_running_app().root.get_screen("main_screen").children[0].children if type(i).__name__ == "MainScreenLower"][0]
        food_card_list = [i for i in main_screen_lower.children if type(i).__name__ == "MainScreenLowerScroll"][0].children[0]
        food_card_list.__init__()

        # tell the user save is successfull
        save_popup = Popup(title = "New food saved",
                           content=Label(text="Your new food is now included!"),
                           size_hint=(0.8, 0.3))
        save_popup.open()

        # reset add food screen
        self.parent.__init__()

        # go back to main page code below
        self.go_to_main()
        
class AddFoodScreen(Screen):
    pass

class GroceryPalApp(App):
    def build(self):
        # on build, run the auto update logic
        self.auto_food_update()

        # set window size 9:20 ratio
        Window.size = (360, 800)
        # Window.size = (450, 1000)
        # Window.size = (495, 1100)
        # Window.size = (540, 1200)
        # set window color
        Window.clearcolor = (0.95, 0.95, 0.95, 1)
        # Create the screen manager
        sm = ScreenManager()
        sm.add_widget(MainScreen(name='main_screen'))
        sm.add_widget(AddFoodScreen(name="add_food_screen"))
        return sm
    
    def get_image_urls(self, query):
        # Google Custom Search API Endpoint
        search_url = 'https://www.googleapis.com/customsearch/v1'
        # Get API key
        with open("data/api_key.txt") as file:
            api_key = file.read()
        # Get custom search engine id
        with open("data/cse_id.txt") as file:
            cse_id = file.read()
        # Parameters for the API request
        params = {
            'key': api_key,
            'cx': cse_id,
            'q': query,
            'searchType': 'image'
        }
        
        # Making a GET request to the API
        response = requests.get(search_url, params=params)

        # read the data as a json and save the links to the images
        data = response.json()
        link_list = []
        for unique_image_data in data["items"][:3]:
            link_list.append(unique_image_data["link"])
        return(link_list)
    
    def load_food_data(self):
        # load in food data
        try:
            data = pl.read_csv("data/food_data.csv")
            return data
        except Exception as e:
            print(f"Error loading data: {e}")
            return None
    
    def auto_food_update(self):
        # read in date 
        with open("data/last_date.txt") as file:
            written_date = file.read()

        # check if first time initialisation needed
        if len(written_date) == 0:
            self.write_date()
            return()
        
        # calculate time since last opened
        last_updated_date = datetime.strptime(written_date, "%d/%m/%Y").date()
        today_date =  datetime.now().date()
        day_delta = (today_date - last_updated_date).days

        # loop through unpaused foods and remove servings
        food_df = self.load_food_data()
        food_df = food_df.with_columns(
            (pl.col("servings") - pl.col("servings_per_day")*day_delta*(~pl.col("paused")))
            .alias("servings")
        )
        food_df = food_df.with_columns(
            pl.when(pl.col("servings") < 0)
            .then(pl.lit(0))
            .otherwise(pl.col("servings"))
            .alias("servings")
        )
        
        # write new food df
        food_df.write_csv("data/food_data.csv")

        # write new date
        self.write_date()
      
    def write_date(self):
        today_date = datetime.now().date().strftime("%d/%m/%Y")
        with open("data/last_date.txt", 'w') as file:
            file.write(today_date)

    def download_image(self, url, save_path):
        try:
            # Send a GET request to the URL
            response = requests.get(url)
            # Check if the request was successful (status code 200)
            if response.status_code == 200:
                # Open the file in binary write mode and write the content
                with open(save_path, 'wb') as file:
                    file.write(response.content)
            else:
                print("")
        except Exception as e:
            print("")
        
if __name__ == '__main__':
    GroceryPalApp().run()