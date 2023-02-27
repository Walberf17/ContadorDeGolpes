"""
This will help to keep track of the strong and weak moves for players
"""
__version__ = "0.4.7"

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
from kivymd.uix.button import MDIconButton, MDFlatButton, MDRoundFlatButton, MDFillRoundFlatButton, MDRectangleFlatIconButton
from kivymd.uix.relativelayout import MDRelativeLayout
from kivymd.uix.carousel import MDCarousel
from kivy.uix.slider import Slider
from kivy.uix.image import Image
from kivy.uix.modalview import ModalView
from kivymd.uix.stacklayout import MDStackLayout
from kivymd.uix.boxlayout import MDBoxLayout

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
    {'set':[{'won': None, 'moves': [[move, state]]}], 'date' = '23-02-01'},
    ]
}
"""

# Variable
slider_threshold = 20

PRAZO_MAXIMO = datetime.date(2023, 3, 10)

MOVES = [
    'Clear',
    'Drive',
    'Smash',
    'Serve',
    'Defense',
    'Drop',
    'Net Play',
    'kill',
]


### Helpers

def add_move(move, player_name, state, *args):
    add_player(player_name=player_name)
    counter[player_name][-1]['set'][-1]['moves'].append([move, state])
    save_file(player_name)


def add_player(player_name):
    if player_name not in counter:
        counter[player_name] = []
        add_set(player_name)


def add_set(player_name):
    new_set = {'set': [], 'date': datetime.date.today().isoformat()}
    if player_name not in counter:
        add_player(player_name)
        return
    counter[player_name].append(new_set)
    add_point(player_name)


def add_point(player_name, *args):
    counter[player_name][-1]['set'].append({'won': None, 'moves': []})


def set_point_won(player_name, won=True, *args):
    counter[player_name][-1]['set'][-1]['won'] = won
    add_point(player_name)


def unset_point(player_input, *args):
    player_name = player_input.text.title().strip()
    counter[player_name][-1]['set'].pop()
    if len(counter[player_name][-1]['set']) > 0:
        counter[player_name][-1]['set'][-1]['won'] = None


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
        super().__init__(cols=1, size_hint=[.1, 1], pos_hint={'center': [.5, .5]}, md_bg_color=[.9, .9, .9, 1], *args,
                         **kwargs)
        self.window = window
        self.move = move

        self.slider = MDSlider(min=-50, max=50, value=0, orientation='vertical', background_width=30, size_hint_y=.8,
                               show_off=False, hint=False)

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
        add_move(move=self.move, player_name=self.window.player_name.text.title().strip(), state=state)

        # add the history
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
        w = max(Window.size)
        width = w * .23
        super().__init__(md_bg_color=[1, 1, 1, 1], size_hint_x=None, width=width, *args, **kwargs)
        self.val = val
        self.max_val = max_val
        size_hint_y = (val / max_val) * .8
        self.move = move
        self.bar = MDGridLayout(cols=1, md_bg_color=bar_color, size_hint=[.8, size_hint_y], pos_hint={'center_x': .5})
        self.add_widget(self.bar)
        self.add_widget(
            MDLabel(text=self.move, pos_hint={'y': size_hint_y, 'center_x': .5}, halign='center', adaptive_size=True))


class FullBar(MDBoxLayout):
    def __init__(self, elements, name, *args, **kwargs):
        moves_to_show = 3
        w = max(Window.size)
        width = w * .23
        super().__init__(orientation='vertical', md_bg_color=[.98, .98, .98, 1], size_hint_x=None, width=width, *args,
                         **kwargs)
        # return funcionou
        self.elements = elements
        self.add_widget(MDLabel(text=name, size_hint=[1, .1], halign='center'))
        colors = ['red', [0.5, .5, 1, 1], [0, 1, 0, 1], [1, 1, 0, 1], [0, 0, 0, 1], [.5, .7, .5, 1]]

        moves = elements.most_common(moves_to_show)[::-1]
        total = sum([x for x in elements.values()])
        if total > sum(x[-1] for x in moves):
            moves.insert(0, ['outros', total - sum(x[-1] for x in moves)])
        # return not working
        moves_grid = MDGridLayout(cols=1, size_hint=[1, .9], padding=[10, 10, 10, 0])
        # moves_grid = MDGridLayout(cols=1)
        # return não funcionou
        for color, move_qnt in zip(colors, moves):
            move, qnt = move_qnt
            bar = MDGridLayout(size_hint=[1, qnt], md_bg_color=color, cols=1)
            bar.add_widget(MDLabel(text=move, size_hint=[1, 1], pos_hint={'center': [.5, .5]}))
            # moves_grid.add_widget(MDLabel(text=move, size_hint=[1, 1], pos_hint={'center': [.5, .5]}))
            moves_grid.add_widget(bar)
        self.add_widget(moves_grid)


class NameTextField(MDTextField):
    def insert_text(self, substring, from_undo=False):
        super().insert_text(substring.title(), from_undo=False)


# classes for windows
class MainWindow(MDGridLayout):
    def __init__(self, *args, **kwargs):
        super().__init__(cols=1, spacing=20, padding=[20, 20, 20, 20], *args, **kwargs)
        text = 'Player'
        if os.path.exists(last_player):
            with open(last_player, 'r') as file:
                text = json.load(file)
                add_set(text)
        self.player_name = MDTextField(size_hint=[1, .1], text=text, halign='center',
                                       text_color_focus='blue', text_color_normal='black',
                                       required=True)  # , on_text_validate=self.on_validate)
        self.player_name.bind(text=self.on_typing)
        self.player_name.bind(focus=self.on_validate)
        self.score = [0, 0]
        self.score_lbl = MDLabel(size_hint=[.4, 1], pos_hint={'center': [.5, .5]}, text=' 0 x 0 ', halign='center',
                                 font_style='H6')
        self.history_lbl = MDLabel(size_hint=[.4, .05], pos_hint={'center': [.5, .5]}, text='  ', halign='center',
                                   font_style='H6')
        self.history = list()
        self.all_pts = list()
        self.build()

    def build(self):
        # add a Title (Player name)
        self.add_widget(self.player_name)

        points_grid = MDGridLayout(rows=1, size_hint=[1, .1])

        points_grid.add_widget(MDRectangleFlatIconButton(text='back pt', on_release=self.back_point, size_hint=[.3, 1]))
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
        markers_grid = MDGridLayout(rows=2, size_hint=[.9, .8], pos_hint={'center': [.5, .5]},
                                    md_bg_color=[.5, .5, .5, 1], spacing=10, padding=[10] * 4)

        for move in MOVES:
            markers_grid.add_widget(Marker(move, self))
        self.add_widget(markers_grid)

    def on_typing(self, *args):
        self.player_name.text = self.player_name.text.title()

    def on_validate(self, *args):
        self.player_name.text = self.player_name.text.title().strip()

    def set_point(self, player=True, *args):
        self.add_point(player)
        set_point_won(self.player_name.text.title().strip(), player)
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
        self.update_score()


class StatsWindow(MDGridLayout):
    def __init__(self, *args, **kwargs):
        super().__init__(cols=1, padding=[10, 10, 10, 10], spacing=5, *args, **kwargs)
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
        common_grid_stts = MDStackLayout(orientation='lr-tb', spacing=20, padding=[20] * 4, md_bg_color=[.5, .5, .5, 1],
                                         adaptive_height=True)
        stt_scroll = MDScrollView(size_hint=[1, .3], bar_color='red')
        stt_scroll.add_widget(common_grid_stts)
        self.add_widget(stt_scroll)

        # statistic btns
        common_grid_stts.add_widget(MDFillRoundFlatButton(text='Last moves', on_release=self.show_last_move_pts))
        common_grid_stts.add_widget(MDFillRoundFlatButton(text='Qnt moves to pt', on_release=self.moves_qnt_per_point))
        common_grid_stts.add_widget(MDFillRoundFlatButton(text='Common Moves', on_release=self.moves_used_per_point))
        common_grid_stts.add_widget(MDFillRoundFlatButton(text='Moves by day', on_release=self.moves_per_day))

        # specific for moves
        statistics_grid_btns = MDStackLayout(orientation='lr-tb', spacing=20, padding=[20] * 4,
                                             md_bg_color=[.5, .5, .5, 1],
                                             adaptive_height=True)
        moves_scroll = MDScrollView(size_hint=[1, .3], bar_color='black')
        moves_scroll.add_widget(statistics_grid_btns)

        for move in MOVES:
            statistics_grid_btns.add_widget(MDFillRoundFlatButton(text=f'{move}s', on_release=partial(
                self.especific_move_proeficience_per_day, move)))
        self.add_widget(moves_scroll)

    def build_moves(self):
        scroll = MDScrollView(size_hint=[.9, .5])
        grid = MDGridLayout(adaptive_height=True, spacing=20, cols=1, md_bg_color=[.5, .5, .5, 1],
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
            for game in this_player_dict:
                for pt in game['set']:
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
            for game in this_player_dict:
                for won, moves in game:
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
            for game in this_player_dict:
                for pt in game['set']:
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
        victories = MDGridLayout(rows=1, spacing=20, adaptive_width=True)
        loses_grid = MDGridLayout(rows=1, spacing=20, adaptive_width=True)

        # scrolls
        scroll_vic = MDScrollView(size_hint=[1, 1])
        scroll_vic.add_widget(victories)

        scrol_los = MDScrollView(size_hint=[1, 1])
        scrol_los.add_widget(loses_grid)

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
        for move, val in zip(x_w, height_w):
            victories.add_widget(BarForGraphic(max_val=max(height_w), move=move, val=val))

        for move, val in zip(x_l, height_l):
            loses_grid.add_widget(BarForGraphic(max_val=max(height_l), move=move, val=val))

        vic_grid = MDGridLayout(cols=1)
        vic_grid.add_widget(
            MDLabel(text='Pts won', font_style='H6', theme_text_color='Custom', text_color='white', halign='center'))
        vic_grid.add_widget(scroll_vic)

        los_grid = MDGridLayout(cols=1)
        los_grid.add_widget(
            MDLabel(text='Pts lost', font_style='H6', theme_text_color='Custom', text_color='white', halign='center'))
        los_grid.add_widget(scrol_los)

        main_grid.add_widget(vic_grid)
        main_grid.add_widget(los_grid)

        popup = Popup(title=f'Pontuação', content=main_grid, size_hint=[1, .8], title_align='center',
                      title_size=MDLabel(font_style="H4").font_size)
        popup.open()
        # self.moves_per_day()

    def moves_qnt_per_point(self, *args):
        name = self.player_name_btn.text
        this_player_dict = counter.get(name)
        moves_to_win = list()
        moves_to_lose = list()
        if this_player_dict is None:
            this_player_dict = {}
            return this_player_dict
        else:
            for game in this_player_dict:
                for pt in game['set']:
                    if pt['won'] is True:
                        moves_to_win.append(len(pt['moves']))
                    if pt['won'] is False:
                        moves_to_lose.append(len(pt['moves']))

        main_grid = MDGridLayout(cols=1, padding=[20, 0, 20, 20], spacing=10, md_bg_color=[1, 1, 1, 1])

        if moves_to_win:
            main_grid.add_widget(MDLabel(text=f'Mean qnt of moves to get pt: {stt.mean(moves_to_win)}'))
        else:
            main_grid.add_widget(MDLabel(text='No statistics.'))

        if moves_to_lose:
            main_grid.add_widget(MDLabel(text=f'Mean qnt of moves to lose pt: {stt.mean(moves_to_lose)}'))
        else:
            main_grid.add_widget(MDLabel(text='No statistics.'))

        popup = Popup(title=f'Pontuação', content=main_grid, size_hint=[1, .8], title_align='center',
                      title_size=MDLabel(font_style="H4").font_size)
        popup.open()

    def moves_used_per_point(self, *args):
        name = self.player_name_btn.text
        this_player_dict = counter.get(name)
        new_dict = {True: Counter(), False: Counter()}
        if this_player_dict is None:
            this_player_dict = {}
            return this_player_dict
        else:
            for moves_set in this_player_dict:
                for pt in moves_set['set']:
                    won = pt['won']
                    if won is not None:
                        moves = list(el[0] for el in pt['moves'])
                        new_dict[won].update(moves)

        main_grid = MDGridLayout(cols=1, padding=[20, 0, 20, 20], spacing=10, md_bg_color=[1, 1, 1, 1])

        main_grid.add_widget(
            MDLabel(text=f'most used moves for won pts: {[x[0] for x in new_dict[True].most_common(3)]}'))
        main_grid.add_widget(
            MDLabel(text=f'most used moves for lost pts: {[x[0] for x in new_dict[False].most_common(3)]}'))

        popup = Popup(title=f'Pontuação', content=main_grid, size_hint=[1, .8], title_align='center',
                      title_size=MDLabel(font_style="H4").font_size)
        popup.open()

    def moves_per_day(self, *args):
        player_dict = counter.get(self.player_name_btn.text)
        new_dict = dict()
        main_grid = MDGridLayout(cols=1, padding=[20, 0, 20, 20], spacing=10)
        if player_dict in [None, {}]:
            main_grid.add_widget(
                MDLabel(text='Sem informação para análises', theme_text_color='Custom', text_color='black'))
        else:
            for moves_set in player_dict:
                if moves_set['date'] not in new_dict:
                    new_dict[moves_set['date']] = Counter()
                # get moves
                new_moves = list()
                for pt in moves_set['set']:
                    for move, grade in pt['moves']:
                        new_moves.append(move)
                new_dict[moves_set['date']].update(new_moves)
            scroll = MDScrollView(size_hint=[1, 1])
            dates_grid = MDGridLayout(rows=1, adaptive_width=True, padding=10, spacing=10)
            date_moves = list(new_dict.items())
            date_moves.sort(key=lambda x: datetime.date.fromisoformat(x[0]), reverse=False)
            for date, moves_counter in date_moves:
                if sum(moves_counter.values()) > 0:
                    name = datetime.date.fromisoformat(date).strftime('%d/%m/%y')
                    dates_grid.add_widget(FullBar(moves_counter, name))

            if len(dates_grid.children) == 0:
                dates_grid.size_hint = [1, 1]
                dates_grid.md_bg_color = [.98, .98, .98, 1]
                dates_grid.add_widget(MDLabel(text='Sem informação para análises', size_hint=[1, 1], halign='center',
                                              theme_text_color='Custom', text_color='black',
                                              pos_hint={'center': [.5, .5]}))

            scroll.add_widget(dates_grid)
            main_grid.add_widget(scroll)

        popup = Popup(title=f'Golpes por dia', content=main_grid, size_hint=[1, .8], title_align='center',
                      title_size=MDLabel(font_style="H4").font_size)
        popup.open()

    def especific_move_proeficience_per_day(self, move_name, *args):
        player_dict = counter.get(self.player_name_btn.text)
        new_dict = dict()
        main_grid = MDGridLayout(cols=1, padding=[20, 0, 20, 20], spacing=10)
        monthly = True
        if player_dict in [None, {}]:
            main_grid.add_widget(MDLabel(text='Sem informação para análises'))
        else:
            if datetime.date.fromisoformat(player_dict[0]['date']) + datetime.timedelta(
                    days=31) > datetime.date.fromisoformat(player_dict[-1]['date']):
                monthly = False

            for moves_set in player_dict:
                this_date = moves_set['date']
                if monthly:
                    this_date = this_date[:7]
                if this_date not in new_dict:
                    new_dict[this_date] = Counter()

                # get moves
                new_moves = list()
                for pt in moves_set['set']:
                    for move, grade in pt['moves']:
                        if move == move_name:
                            new_moves.append(grade.title())
                new_dict[this_date].update(new_moves)
            scroll = MDScrollView(size_hint=[1, 1])
            dates_grid = MDGridLayout(rows=1, adaptive_width=True, padding=10, spacing=10)
            date_moves = list(new_dict.items())
            if monthly:
                date_moves.sort(key=lambda x: datetime.datetime.strptime(x[0], '%Y-%m'), reverse=False)
            else:
                date_moves.sort(key=lambda x: datetime.datetime.strptime(x[0], '%Y-%m-%d'), reverse=False)

            for date, moves_counter in date_moves:
                if sum(moves_counter.values()) > 0:
                    if monthly:
                        name = datetime.datetime.strptime(date, '%Y-%m').strftime('%m/%y')
                    else:
                        name = datetime.date.fromisoformat(date).strftime('%d/%m/%y')
                    dates_grid.add_widget(FullBar(moves_counter, name))

            if len(dates_grid.children) == 0:
                dates_grid.size_hint = [1, 1]
                dates_grid.md_bg_color = [.98, .98, .98, 1]
                dates_grid.add_widget(MDLabel(text='Sem informação para análises', size_hint=[1, 1], halign='center',
                                              theme_text_color='Custom', text_color='black',
                                              pos_hint={'center': [.5, .5]}))

            scroll.add_widget(dates_grid)
            main_grid.add_widget(scroll)

        title = f'{move_name}s by day'
        if monthly:
            title = f'{move_name}s by day'
        popup = Popup(title=title, content=main_grid, size_hint=[1, .8], title_align='center',
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


class EntreEmContato(MDApp):
    def build(self):
        txt = f'''Esse aplicativo foi desativado  por estar desatualizado. Entre em contato com Mutante Apps pelo email:

mutante.apps@gmail.com'''
        lbl = MDLabel(text=txt, font_style='H4', halign='center')
        return lbl


if datetime.date.today() > PRAZO_MAXIMO:
    EntreEmContato().run()
else:
    AssistenteApp().run()
