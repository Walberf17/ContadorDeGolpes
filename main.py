"""
This will help to keep track of the strong and weak moves for players
"""
__version__ = "0.1.3"

import os
import random
from functools import partial
import json
os.environ['KIVY_ORIENTATION'] = 'Portrait'

from kivy.uix.screenmanager import Screen, ScreenManager
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.button import MDIconButton, MDFlatButton, MDRoundFlatButton, MDFillRoundFlatButton
from kivymd.uix.relativelayout import MDRelativeLayout
from kivymd.uix.carousel import MDCarousel
from kivy.uix.modalview import ModalView



# import kivy
from kivymd.app import MDApp
from kivymd.uix.bottomnavigation import MDBottomNavigation, MDBottomNavigationItem
from kivymd.uix.label import MDLabel
# from kivymd.uix.textfield import MDTextField
from kivymd.uix.gridlayout import MDGridLayout

from kivy.core.window import Window
from kivy.uix.popup import Popup
from kivymd.uix.slider import MDSlider

path_to_save_file = os.path.join('.', 'resultados')
moves_file = os.path.join(path_to_save_file, 'players.json')
last_player = os.path.join(path_to_save_file, 'last_player.json')

os.makedirs(os.path.join(path_to_save_file), exist_ok=True)

counter = {}  # dict of dicts, a dict is a Player, each with the name of the move as keys and its good and bad values

### Helpers

def move_count(slider, move, player_input, *args):
    slider.active = False

    val = slider.value

    if -10 < val < 10:
        return

    player_name = player_input.text.title().strip()
    slider.value = 0

    if add_player_move(player_name=player_name, move_name=move):
        if val > 10:
            state = 'good'
        elif val < -10:
            state = 'bad'
        counter[player_name][move][state] += 1


def add_player_move(player_name, move_name):
    if player_name not in counter:
        counter[player_name] = {}

    if move_name is None:
        return False

    if move_name not in counter[player_name]:
        counter[player_name][move_name] = {'good': 0, 'bad': 0}
    return True

def load_file():
    global counter
    file_name = os.path.join(path_to_save_file, 'players.json')
    if os.path.exists(file_name):
        with open(file_name, 'r') as file:
            counter = json.load(file)

def save_file(last_player_name):

    # Save the dict with the moves
    with open(moves_file, 'w') as file:
        json.dump(counter, file, indent=4, ensure_ascii=False)

    # Save the last player
    with open(last_player, 'w') as file:
        json.dump(last_player_name, file, indent=4, ensure_ascii=False)

# Helper Classes
class Marker(MDGridLayout):
    def __init__(self, move, player_name, *args, **kwargs):
        super().__init__(cols=1, size_hint=[.1, 1], pos_hint={'center': [.5, .5]}, *args, **kwargs)
        self.player_name = player_name
        self.slider = MDSlider(min=-50, max=50, value=0, orientation='vertical', sensitivity='all', hint=False,
                               show_off=False, thumb_color_active='black')
        self.slider.on_touch_up = partial(move_count, self.slider, move, self.player_name)
        self.label = MDLabel(text=move, halign='center')
        self.slider.bind(value=self.change_hint)
        self.add_widget(self.slider)
        self.add_widget(self.label)

    def change_hint(self, slider, value):
        r, g, b = [0, 0, 0]
        if value > 10:
            g = (value + 50) / 100
        elif value < -10:
            r = -(value - 50) / 100

        slider.thumb_color_active = [r, g, b, 1]


class Moveline(MDGridLayout):
    def __init__(self,move, good, bad,  *args, **kwargs):
        super().__init__(cols=3, md_bg_color=[1]*4, *args, **kwargs)
        self.add_widget(MDLabel(text=f'{move} ==>', adaptive_width=True, shorten=True, size_hint=[.5,1], halign='center'))
        self.add_widget(MDLabel(text=f'Bons: {good}', adaptive_width=True, shorten=True, size_hint=[.25,1]))
        self.add_widget(MDLabel(text=f'Ruins: {bad}', adaptive_width=True, shorten=True, size_hint=[.25,1]))


class PlayersSelection(ModalView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.build()

    def build(self):
        self.clear_widgets()
        layout = MDGridLayout(cols=1, size_hint=[.8, .8], md_bg_color='white')
        layout.add_widget(
            MDLabel(text=f'Selecione o Jogador', halign='center', pos_hint={'center': [.5, .2]}, size_hint=[.8, .2]))

        scroll = MDScrollView(size_hint=[.7, .9], pos_hint={'center': [.5, .5]})
        grid = MDGridLayout(cols=1, adaptive_height=True, pos_hint={'center': [.5, .5]}, md_bg_color='white',
                            spacing=20, padding=[30, 10, 30, 10])
        for player in counter:
            grid.add_widget(MDFillRoundFlatButton(text=player, pos_hint={'center': [.5, .5]},
                                                  on_release=partial(self.click_up, player)))
        scroll.add_widget(grid)
        layout.add_widget(scroll)
        self.add_widget(layout)


    def click_up(self, name, *args):
        app = MDApp.get_running_app()
        app.stats_window.change_player(name)
        self.dismiss()


# classes for windows
class MainWindow(MDGridLayout):
    def __init__(self, *args, **kwargs):
        super().__init__(cols=1, spacing=20, padding=[20, 20, 20, 20], *args, **kwargs)
        text = 'Player'
        if os.path.exists(last_player):
            with open(last_player, 'r') as file:
                text = json.load(file)
        self.player_name = MDLabel(size_hint=[1, .1], text=text, halign='center')
                                       # text_color_focus='blue', text_color_normal='black')
        self.build()

    def build(self):
        # add a Title (Player name)
        self.add_widget(self.player_name)

        # Add the moves Markers
        markers_grid = MDGridLayout(cols=3, size_hint=[.9, .9], pos_hint={'center': [.5, .5]})
        moves = [
            'Clear',
            'Drive',
            'Smash',
            'Serve',
            'Defense',
            'Drop',
            'Net Play',
        ]
        for move in moves:
            markers_grid.add_widget(Marker(move, self.player_name))
        self.add_widget(markers_grid)


class StatsWindow(MDGridLayout):
    def __init__(self, *args, **kwargs):
        super().__init__(cols=1, *args, **kwargs)
        self.popup = PlayersSelection(size_hint=[.8,.9])
        text = 'Player'
        if os.path.exists(last_player):
            with open(last_player, 'r') as file:
                text = json.load(file)
        self.player_input = MDRoundFlatButton(font_style='H5', size_hint=[.5, .1], text=text, halign='center',
                                              valign='center', text_color='black', on_release=self.popup.open)
        self.build()
        # self.popup.open()

    def build(self):
        self.clear_widgets()
        # self.popup = PlayersSelection(size_hint=[.8,.9])
        self.add_widget(self.player_input)
        this_player_dict = counter.get(self.player_input.text.title().strip(), {})
        self.add_widget(self.build_moves(this_player_dict))

    def build_moves(self, this_player_dict):
        scroll = MDScrollView()
        grid = MDGridLayout(adaptive_height=True, spacing=20, cols=1, md_bg_color=[0,0,0,1])
        for move in this_player_dict:
            good = this_player_dict[move].get('good', 0)
            bad = this_player_dict[move].get('bad', 0)
            grid.add_widget(Moveline(move, good, bad, padding=[20,20,20,20], adaptive_height=True))
        scroll.add_widget(grid)
        return scroll

    def change_player(self, player_name, *args):
        self.player_input.text = player_name
        self.build()

    def update(self):
        self.popup.build()


# Main app class
class AssistenteApp(MDApp):
    def __init__(self, **kwargs):
        load_file()
        super().__init__(**kwargs)
        self.main_window = MainWindow()
        self.stats_window = StatsWindow()
        self.sm = MDBottomNavigation()
        self.sm.add_widget(MDBottomNavigationItem(self.main_window, name=' Main'), text='Main window')
        self.sm.add_widget(MDBottomNavigationItem(self.stats_window, name='Stats', on_tab_press=self.build_stats_window), text='Show the stats')

    def build(self):
        return self.sm

    def on_stop(self):
        save_file(self.main_window.player_name.text)
        super().on_stop()

    def build_stats_window(self, *args):
        self.stats_window.change_player(self.main_window.player_name.text)
        self.stats_window.popup.build()

AssistenteApp().run()
