"""
This will help to keep track of the strong and weak moves for players
"""
__version__ = "0.4.0"

import os
import random
from functools import partial
import json
import datetime
import statistics as stt
from collections import Counter

# os.environ['KIVY_ORIENTATION'] = 'Portrait'

from kivy.uix.screenmanager import Screen, ScreenManager
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.button import MDIconButton, MDFlatButton, MDRoundFlatButton, MDFillRoundFlatButton, \
    MDRectangleFlatIconButton
from kivymd.uix.relativelayout import MDRelativeLayout
from kivymd.uix.carousel import MDCarousel
from kivy.uix.slider import Slider
from kivy.uix.image import Image
from kivy.uix.modalview import ModalView
from kivymd.uix.stacklayout import MDStackLayout

# import kivy
from kivymd.app import MDApp
from kivymd.uix.bottomnavigation import MDBottomNavigation, MDBottomNavigationItem
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.gridlayout import MDGridLayout

from kivy.core.window import Window
from kivy.uix.popup import Popup
from kivymd.uix.slider import MDSlider

path_to_save_file = os.path.join('.', 'resultados')
moves_file = os.path.join(path_to_save_file, 'players.json')
last_player = os.path.join(path_to_save_file, 'last_player.json')

os.makedirs(os.path.join(path_to_save_file), exist_ok=True)

counter = {}

"""
exemple = {
    'Player': [
    {'set':[{'won': None, 'moves': [[move, state]]}], 'date' = today},
    ]
}
"""

# Variable
slider_threshold = 20


### Helpers

def add_move(move, player_input, state, *args):
    player_name = player_input.text.title().strip()
    add_player(player_input=player_input)
    counter[player_name][-1]['set'][-1]['moves'].append([move, state])


def add_player(player_input):
    player_name = player_input.text.title().strip()
    if player_name not in counter:
        counter[player_name] = []
        add_set(player_input)


def add_set(player_input):
    player_name = player_input.text.title().strip()
    new_set = {'set': [], 'date': datetime.date.today().isoformat()}
    counter[player_name].append(new_set)
    add_point(player_input)


def add_point(player_input, *args):
    player_name = player_input.text.title().strip()
    counter[player_name][-1]['set'].append({'won': None, 'moves': []})


def set_point_won(player_input, won=True, *args):
    player_name = player_input.text.title().strip()
    counter[player_name][-1]['set'][-1]['won'] = won
    add_point(player_input)


def unset_point(player_input, *args):
    player_name = player_input.text.title().strip()
    counter[player_name][-1].pop()
    counter[player_name][-1][-1][0] = None


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
    def __init__(self, move, window, *args, **kwargs):
        super().__init__(cols=1, size_hint=[.1, 1], pos_hint={'center': [.5, .5]}, md_bg_color=[.7, .7, .7, 1], *args,
                         **kwargs)
        self.window = window
        self.move = move
        # self.slider = Slider(min=-50, max=50, value=0, orientation='vertical', background_width=30, size_hint_y=.8, sensitivity='handle', value_track=True, value_track_color=[0,0,0,1])
        self.slider = MDSlider(min=-50, max=50, value=0, orientation='vertical', background_width=30, size_hint_y=.8,
                               show_off=False)
        self.slider.on_touch_up = self.add_move
        self.label = MDLabel(text=move, halign='center', size_hint_y=.2)
        self.slider.bind(value=self.change_hint)
        self.add_widget(self.slider)
        self.add_widget(self.label)

    def change_hint(self, slider, value):
        r, g, b = [0, 0, 0]
        if value > slider_threshold:
            g = (value + 50) / 100
        elif value < -slider_threshold:
            r = -(value - 50) / 100
        slider.thumb_color_active = [r, g, b, 1]

    def add_move(self, *args):
        self.slider.active = False
        val = self.slider.value
        self.slider.value = 0

        if -slider_threshold < val < slider_threshold:
            return

        self.slider.value = 0

        if val > slider_threshold:
            state = 'good'  # good
        elif val < -slider_threshold:
            state = 'bad'  # bad

        # add the move
        add_move(move=self.move, player_input=self.window.player_name, state=state)

        self.window.add_history(self.move, state)


class Moveline(MDGridLayout):
    def __init__(self, move, good, bad, *args, **kwargs):
        super().__init__(cols=3, md_bg_color=[1] * 4, *args, **kwargs)
        self.add_widget(
            MDLabel(text=f'{move} ==>', adaptive_width=True, shorten=True, size_hint=[.5, 1], halign='center'))
        self.add_widget(MDLabel(text=f'Bons: {good}', adaptive_width=True, shorten=True, size_hint=[.25, 1]))
        self.add_widget(MDLabel(text=f'Ruins: {bad}', adaptive_width=True, shorten=True, size_hint=[.25, 1]))


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
        scroll.add_widget(grid)
        for player in counter:
            grid.add_widget(MDFillRoundFlatButton(text=player, pos_hint={'center': [.5, .5]},
                                                  on_release=partial(self.click_up, player)))

        layout.add_widget(scroll)
        self.add_widget(layout)

    def click_up(self, name, *args):
        app = MDApp.get_running_app()
        app.stats_window.change_player(name)
        self.dismiss()


class BarForGraphic(MDRelativeLayout):
    def __init__(self, val, max_val, move, bar_color=[0, .6, .7, 1], *args, **kwargs):
        super().__init__(md_bg_color=[1, 1, 1, 1], *args, **kwargs)
        self.val = val
        self.max_val = max_val
        size_hint_y = (val / max_val) * .8
        self.move = move
        self.bar = MDGridLayout(cols=1, md_bg_color=bar_color, size_hint=[1, size_hint_y])
        self.add_widget(self.bar)
        self.add_widget(
            MDLabel(text=self.move, pos_hint={'y': size_hint_y, 'center_x': .5}, halign='center', adaptive_size=True))


# classes for windows
class MainWindow(MDGridLayout):
    def __init__(self, *args, **kwargs):
        super().__init__(cols=1, spacing=20, padding=[20, 20, 20, 20], *args, **kwargs)
        text = 'Player'
        if os.path.exists(last_player):
            with open(last_player, 'r') as file:
                text = json.load(file)
        self.player_name = MDTextField(size_hint=[1, .1], text=text, halign='center',
                                       text_color_focus='blue', text_color_normal='black')
        self.score = [0, 0]
        self.score_lbl = MDLabel(size_hint=[.4, 1], pos_hint={'center': [.5, .5]}, text=' 0 x 0 ', halign='center',
                                 font_style='H3')
        self.history_lbl = MDLabel(size_hint=[.4, .05], pos_hint={'center': [.5, .5]}, text='  ', halign='center',
                                   font_style='H6')
        self.history = list()
        self.all_pts = list()
        self.build()

    def build(self):
        # add a Title (Player name)
        self.add_widget(self.player_name)

        points_grid = MDGridLayout(rows=1, size_hint=[1, .1])

        points_grid.add_widget(MDRectangleFlatIconButton(text='Voltar', on_release=self.back_point, size_hint=[.3, 1]))
        points_grid.add_widget(self.score_lbl)
        points_grid.add_widget(MDRectangleFlatIconButton(text='Game', on_release=self.new_set, size_hint=[.3, 1]))

        self.add_widget(points_grid)
        self.add_widget(self.history_lbl)

        pts_grid = MDGridLayout(rows=1, spacing=60, padding=20, size_hint=[1, .1])
        pts_grid.add_widget(MDFillRoundFlatButton(text='Pt player', on_release=partial(self.set_point, True),
                                                  size_hint=[1, 1], pos_hint={'center': [.5, .5]}))
        pts_grid.add_widget(MDFillRoundFlatButton(text='Pt Adv', on_release=partial(self.set_point, False),
                                                  size_hint=[1, 1], pos_hint={'center': [.5, .5]}))
        self.add_widget(pts_grid)

        # Add the moves Markers
        markers_grid = MDGridLayout(cols=5, size_hint=[.9, .8], pos_hint={'center': [.5, .5]},
                                    md_bg_color=[.5, .5, .5, 1],
                                    spacing=10)
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
            markers_grid.add_widget(Marker(move, self))
        self.add_widget(markers_grid)

    def set_point(self, player=True, *args):
        self.add_point(player)
        set_point_won(self.player_name, player)
        self.update_score()
        self.history_lbl.text = ''
        self.history.clear()

    def update_score(self):
        player_score = self.all_pts.count(1)
        adversary_score = self.all_pts.count(0)
        self.score_lbl.text = f' {player_score} x {adversary_score} '

    def add_history(self, move, state):
        self.history.append(move)
        text = ', '.join(self.history)
        self.history_lbl.text = text

    def back_point(self, *args):
        if len(self.all_pts) > 0:
            self.all_pts.pop()
            unset_point(self.player_name)
            self.update_score()

    def add_point(self, player=True):
        self.all_pts.append(int(player))

    def new_set(self, *args):
        self.all_pts.clear()
        self.history.clear()
        self.history_lbl.text = ''


class StatsWindow(MDGridLayout):
    def __init__(self, *args, **kwargs):
        super().__init__(cols=1, padding=[10,10,10,10], spacing=5, *args, **kwargs)
        self.popup = PlayersSelection(size_hint=[.8, .9])
        text = 'Player'
        if os.path.exists(last_player):
            with open(last_player, 'r') as file:
                text = json.load(file)
        self.player_name_btn = MDRoundFlatButton(font_style='H5', size_hint=[.5, .1], text=text, halign='center',
                                                 valign='center', text_color='black', on_release=self.popup.open)
        self.build()

        # self.popup.open()

    def build(self):
        self.clear_widgets()
        self.popup.build()
        self.add_widget(self.player_name_btn)
        self.add_widget(self.build_moves())

        # statistics grid
        statistics_grid_btns = MDGridLayout(cols=4, size_hint=[1, .2], spacing=20)

        # statistic btns
        statistics_grid_btns.add_widget(MDFillRoundFlatButton(text='Pontos Finais', on_release=self.show_last_move_pts))
        statistics_grid_btns.add_widget(MDFillRoundFlatButton(text='Pontos para final', on_release=self.moves_qnt_per_point))
        statistics_grid_btns.add_widget(MDFillRoundFlatButton(text='golpes mais usados', on_release=self.moves_used_per_point))


        self.add_widget(statistics_grid_btns)



    def build_moves(self):
        scroll = MDScrollView(1,.8)
        grid = MDGridLayout(adaptive_height=True, spacing=20, cols=1, md_bg_color=[0, 0, 0, 1],
                            padding=[20, 20, 20, 20])

        this_player_dict = self.get_player_dict()

        for move in this_player_dict:
            good = this_player_dict[move].get('good', 0)
            bad = this_player_dict[move].get('bad', 0)
            grid.add_widget(Moveline(move, good, bad, padding=[20, 20, 20, 20], adaptive_height=True))
        scroll.add_widget(grid)
        return scroll

    def change_player(self, player_name, *args):
        self.player_name_btn.text = player_name
        self.build()

    def update(self):
        self.popup.build()

    def get_player_dict(self):
        name = self.player_name_btn.text
        this_player_dict = counter.get(name)
        new_dict = {}
        if this_player_dict is None:
            this_player_dict = {}
            return this_player_dict
        else:
            for set in this_player_dict:
                for pt in set['set']:
                    moves = pt.get('moves')
                    if moves:
                        for move, state in moves:
                            if move not in new_dict:
                                new_dict[move] = {'good': 0, 'bad': 0}
                            new_dict[move][state] += 1
            return new_dict

    def get_player_used_moves(self):
        name = self.player_name_btn.text
        this_player_dict = counter.get(name)
        new_dict = {True: {}, False: {}}
        if this_player_dict is None:
            this_player_dict = {}
            return this_player_dict
        else:
            for set in this_player_dict:
                for won, moves in set:
                    for move, state in moves:
                        if move not in new_dict[won]:
                            new_dict[won][move] = {'good': 0, 'bad': 0}
                        new_dict[won][move][state] += 1
        return new_dict

    def get_player_last_moves(self):
        name = self.player_name_btn.text
        this_player_dict = counter.get(name)
        new_dict = {True: {}, False: {}}
        if this_player_dict is None:
            this_player_dict = {}
            return this_player_dict
        else:
            for set in this_player_dict:
                for pt in set['set']:
                    won = pt.get('won')
                    moves = pt.get('moves')
                    if won is not None and moves:
                        for move, state in moves:
                            if move not in new_dict[won]:
                                new_dict[won][move] = 0
                            new_dict[won][move] += 1
        return new_dict

    def show_last_move_pts(self, *args):
        main_grid = MDGridLayout(cols=1, padding=[20, 0, 20, 20], spacing=10)
        victories = MDGridLayout(rows=1, spacing=20)
        loses_grid = MDGridLayout(rows=1, spacing=20)
        last_moves = self.get_player_last_moves()
        wons = last_moves.get(True, {})
        loses = last_moves.get(False, {})

        x_w = list()
        height_w = list()
        x_l = list()
        height_l = list()

        # wins
        wins_list = list(wons.items())
        wins_list.sort(key=lambda x: x[-1], reverse=True)
        for move, qnt in wins_list:
            x_w.append(move)
            height_w.append(qnt)

        # loses
        lost_list = list(loses.items())
        lost_list.sort(key=lambda x: x[-1], reverse=True)
        for move, qnt in lost_list:
            x_l.append(move)
            height_l.append(qnt)

        # for graphs
        if height_l and height_w:
            max_y = max(height_l + height_w)
        elif height_w:
            max_y = max(height_w)
        elif height_l:
            max_y = max(height_l)

        for move, val in zip(x_w, height_w):
            victories.add_widget(BarForGraphic(max_val=max_y, move=move, val=val))

        for move, val in zip(x_l, height_l):
            loses_grid.add_widget(BarForGraphic(max_val=max_y, move=move, val=val))

        vic_grid = MDGridLayout(cols=1)
        vic_grid.add_widget(
            MDLabel(text='Pts Feitos', font_style='H6', theme_text_color='Custom', text_color='white', halign='center'))
        vic_grid.add_widget(victories)

        los_grid = MDGridLayout(cols=1)
        los_grid.add_widget(
            MDLabel(text='Perdidos', font_style='H6', theme_text_color='Custom', text_color='white', halign='center'))
        los_grid.add_widget(loses_grid)

        main_grid.add_widget(vic_grid)
        main_grid.add_widget(los_grid)

        popup = Popup(title=f'Pontuação', content=main_grid, size_hint=[1, .8], title_align='center',
                      title_size=MDLabel(font_style="H4").font_size)
        popup.open()

    def moves_qnt_per_point(self, *args):
        name = self.player_name_btn.text
        this_player_dict = counter.get(name)
        moves_to_win = list()
        moves_to_lose = list()
        if this_player_dict is None:
            this_player_dict = {}
            return this_player_dict
        else:
            for set in this_player_dict:
                for pt in set['set']:
                    if pt['won'] is True:
                        moves_to_win.append(len(pt['moves']))
                    if pt['won'] is False:
                        moves_to_lose.append(len(pt['moves']))

        main_grid = MDGridLayout(cols=1, padding=[20, 0, 20, 20], spacing=10, md_bg_color=[1,1,1,1])

        main_grid.add_widget(MDLabel(text=f'Média de Pontos para ponto feito: {stt.mean(moves_to_win)}'))
        main_grid.add_widget(MDLabel(text=f'Média de Pontos para ponto perdido: {stt.mean(moves_to_lose)}'))


        popup = Popup(title=f'Pontuação', content=main_grid, size_hint=[1, .8], title_align='center',
                      title_size=MDLabel(font_style="H4").font_size)
        popup.open()

    def moves_used_per_point(self, *args):
        name = self.player_name_btn.text
        this_player_dict = counter.get(name)
        new_dict = {True:Counter(), False:Counter()}
        if this_player_dict is None:
            this_player_dict = {}
            return this_player_dict
        else:
            for set in this_player_dict:
                for pt in set['set']:
                    won = pt['won']
                    if won is not None:
                        moves = list(el[0] for el in pt['moves'])
                        new_dict[won].update(moves)

        main_grid = MDGridLayout(cols=1, padding=[20, 0, 20, 20], spacing=10, md_bg_color=[1,1,1,1])

        main_grid.add_widget(MDLabel(text=f'Move mais usado nos pontos ganhos: {[x[0] for x in new_dict[True].most_common(3)]}'))
        main_grid.add_widget(MDLabel(text=f'Move mais usado nos pontos perdidos: {[x[0] for x in new_dict[False].most_common(3)]}'))

        popup = Popup(title=f'Pontuação', content=main_grid, size_hint=[1, .8], title_align='center',
                      title_size=MDLabel(font_style="H4").font_size)
        popup.open()

    def history_moves_qnt_per_point(self, *args):
        name = self.player_name_btn.text
        this_player_dict = counter.get(name)
        moves_to_win = list()
        moves_to_lose = list()
        if this_player_dict is None:
            this_player_dict = {}
            return this_player_dict
        else:
            for set in this_player_dict:
                for idx, pt in enumerate(set['set']):
                    if pt['won'] is True:
                        moves_to_win[idx].append(len(pt['moves']))
                    if pt['won'] is False:
                        moves_to_lose[idx].append(len(pt['moves']))

        main_grid = MDGridLayout(cols=1, padding=[20, 0, 20, 20], spacing=10, md_bg_color=[1, 1, 1, 1])

        main_grid.add_widget(MDLabel(text=f'Média de golpes para ponto feito: {stt.mean(moves_to_win)}'))
        main_grid.add_widget(MDLabel(text=f'Média de golpes para ponto perdido: {stt.mean(moves_to_lose)}'))

        popup = Popup(title=f'Pontuação', content=main_grid, size_hint=[1, .8], title_align='center',
                      title_size=MDLabel(font_style="H4").font_size)
        popup.open()


# Main app class
class AssistenteApp(MDApp):
    def __init__(self, **kwargs):
        load_file()
        super().__init__(**kwargs)
        self.main_window = MainWindow()
        self.stats_window = StatsWindow()
        self.sm = MDBottomNavigation()
        self.sm.add_widget(MDBottomNavigationItem(self.main_window, name=' Main'), text='Main window')
        self.sm.add_widget(
            MDBottomNavigationItem(self.stats_window, name='Stats', on_tab_press=self.build_stats_window),
            text='Show the stats')

    def build(self):
        return self.sm

    def on_stop(self):
        save_file(self.main_window.player_name.text)
        super().on_stop()

    def build_stats_window(self, *args):
        self.stats_window.change_player(self.main_window.player_name.text)
        self.stats_window.popup.build()


AssistenteApp().run()
