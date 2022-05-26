import random
import os
import sys
import pygame
import pygame.midi
import time
import pyglet
import tkinter as tk
import browse
import musicpy as mp
from ast import literal_eval
import piano_config
from change_settings import config_window
from copy import deepcopy as copy
import importlib

if sys.platform == 'darwin':
    current_test = tk.Tk()
    current_test.withdraw()
    current_test.destroy()

if piano_config.language == 'English':
    from languages.en import language_patch
elif piano_config.language == 'Chinese':
    from languages.cn import language_patch
    mp.alg.detect = language_patch.detect

key = pyglet.window.key


def get_off_sort(a):
    identifier = language_patch.ideal_piano_language_dict['sort']
    each_chord = a.split('/')
    for i in range(len(each_chord)):
        current = each_chord[i]
        if identifier in current:
            current = current[:current.index(identifier) - 1]
            if current[0] == '[':
                current += ']'
            each_chord[i] = current
    return '/'.join(each_chord)


def load(dic, path, file_format, volume):
    wavedict = {
        i: pygame.mixer.Sound(f'{path}/{dic[i]}.{file_format}')
        for i in dic
    }
    if volume != None:
        [wavedict[x].set_volume(volume) for x in wavedict]
    return wavedict


def get_image(img):
    return pyglet.image.load(img).get_texture()


def update(dt):
    pass


class ideal_piano_button:

    def __init__(self, img, x, y):
        self.img = get_image(img).get_transform()
        self.img.width /= piano_config.button_resize_num
        self.img.height /= piano_config.button_resize_num
        self.x = x
        self.y = y
        self.button = pyglet.sprite.Sprite(self.img, x=self.x, y=self.y)
        self.ranges = [self.x, self.x + self.img.width
                       ], [self.y, self.y + self.img.height]

    def get_range(self):
        height, width = self.img.height, self.img.width
        return [self.x, self.x + width], [self.y, self.y + height]

    def inside(self, mouse_pos):
        range_x, range_y = self.ranges
        return range_x[0] <= mouse_pos[0] <= range_x[1] and range_y[
            0] <= mouse_pos[1] <= range_y[1]

    def draw(self):
        self.button.draw()


class piano_window(pyglet.window.Window):

    def __init__(self):
        self.init_window()
        self.init_parameters()
        self.init_key_map()
        self.init_keys()
        self.init_screen()
        self.init_layers()
        self.init_piano_keys()
        self.init_note_mode()
        self.init_screen_labels()
        self.init_music_analysis()

    def init_window(self):
        super(piano_window, self).__init__(*piano_config.screen_size,
                                           caption='Ideal Piano',
                                           resizable=True)
        self.icon = pyglet.image.load('visualization/resources/piano.ico')
        self.set_icon(self.icon)
        self.keyboard_handler = key.KeyStateHandler()
        self.push_handlers(self.keyboard_handler)

    def init_key_map(self):
        self.map_key_dict = {
            each.lower().lstrip('_'): value
            for each, value in key.__dict__.items() if isinstance(value, int)
        }
        self.map_key_dict_reverse = {
            j: i
            for i, j in self.map_key_dict.items()
        }
        self.map_key_dict_reverse[59] = ';'
        self.map_key_dict_reverse[39] = "'"
        self.map_key_dict_reverse[44] = ","
        self.map_key_dict_reverse[46] = "."
        self.map_key_dict_reverse[47] = '/'
        self.map_key_dict_reverse[91] = '['
        self.map_key_dict_reverse[93] = ']'
        self.map_key_dict_reverse[92] = '\\'
        self.map_key_dict_reverse[96] = '`'
        self.map_key_dict_reverse[45] = '-'
        self.map_key_dict_reverse[61] = '='
        self.map_key_dict_reverse[65288] = 'backspace'
        self.map_key_dict2 = {
            j: i
            for i, j in self.map_key_dict_reverse.items()
        }

    def init_keys(self):
        self.pause_key = self.map_key_dict.setdefault(piano_config.pause_key,
                                                      key.SPACE)
        self.repeat_key = self.map_key_dict.setdefault(piano_config.repeat_key,
                                                       key.LCTRL)
        self.unpause_key = self.map_key_dict.setdefault(
            piano_config.unpause_key, key.ENTER)
        self.config_key = self.map_key_dict.setdefault(piano_config.config_key,
                                                       key.LALT)

    def init_screen(self):
        self.screen_width, self.screen_height = piano_config.screen_size
        self.show_delay_time = int(piano_config.show_delay_time * 1000)
        pygame.mixer.init(piano_config.frequency, piano_config.size,
                          piano_config.channel, piano_config.buffer)
        pygame.mixer.set_num_channels(piano_config.max_num_channels)
        try:
            background = get_image(piano_config.background_image)
        except:
            background = get_image('resources/white.png')
        if not piano_config.background_size:
            if piano_config.width_or_height_first:
                ratio_background = self.screen_width / background.width
                background.width = self.screen_width
                background.height *= ratio_background
            else:
                ratio_background = self.screen_height / background.height
                background.height = self.screen_height
                background.width *= ratio_background
        else:
            background.width, background.height = piano_config.background_size
        self.background = background

    def init_layers(self):
        self.batch = pyglet.graphics.Batch()
        self.bottom_group = pyglet.graphics.OrderedGroup(0)
        self.piano_bg = pyglet.graphics.OrderedGroup(1)
        self.piano_key = pyglet.graphics.OrderedGroup(2)
        self.play_highlight = pyglet.graphics.OrderedGroup(3)

    def init_note_mode(self):
        if not piano_config.draw_piano_keys:
            self.bar_offset_x = 9
            image = get_image(piano_config.piano_image)
            if not piano_config.piano_size:
                ratio = self.screen_width / image.width
                image.width = self.screen_width
                image.height *= ratio
            else:
                image.width, image.height = piano_config.piano_size
            self.image_show = pyglet.sprite.Sprite(image,
                                                   x=0,
                                                   y=0,
                                                   batch=self.batch,
                                                   group=self.piano_bg)

        current_piano_engine.plays = []
        if piano_config.note_mode == 'bars drop':
            current_piano_engine.bars_drop_time = []
            distances = self.screen_height - self.piano_height
            self.bars_drop_interval = piano_config.bars_drop_interval
            self.bar_steps = (distances / self.bars_drop_interval
                              ) / piano_config.adjust_ratio
        else:
            self.bar_steps = piano_config.bar_steps
            self.bars_drop_interval = 0

    def init_screen_labels(self):
        self.label = pyglet.text.Label('',
                                       font_name=piano_config.fonts,
                                       font_size=piano_config.fonts_size,
                                       bold=piano_config.bold,
                                       x=piano_config.label1_place[0],
                                       y=piano_config.label1_place[1],
                                       color=piano_config.message_color,
                                       anchor_x=piano_config.label_anchor_x,
                                       anchor_y=piano_config.label_anchor_y,
                                       multiline=True,
                                       width=1000)
        self.label2 = pyglet.text.Label('',
                                        font_name=piano_config.fonts,
                                        font_size=piano_config.fonts_size,
                                        bold=piano_config.bold,
                                        x=piano_config.label2_place[0],
                                        y=piano_config.label2_place[1],
                                        color=piano_config.message_color,
                                        anchor_x=piano_config.label_anchor_x,
                                        anchor_y=piano_config.label_anchor_y)
        self.label3 = pyglet.text.Label('',
                                        font_name=piano_config.fonts,
                                        font_size=piano_config.fonts_size,
                                        bold=piano_config.bold,
                                        x=piano_config.label3_place[0],
                                        y=piano_config.label3_place[1],
                                        color=piano_config.message_color,
                                        anchor_x=piano_config.label_anchor_x,
                                        anchor_y=piano_config.label_anchor_y)

        self.label_midi_device = pyglet.text.Label(
            '',
            font_name=piano_config.fonts,
            font_size=15,
            bold=piano_config.bold,
            x=250,
            y=400,
            color=piano_config.message_color,
            anchor_x=piano_config.label_anchor_x,
            anchor_y=piano_config.label_anchor_y,
            multiline=True,
            width=1000)

    def init_music_analysis(self):
        if piano_config.show_music_analysis:
            self.music_analysis_label = pyglet.text.Label(
                '',
                font_name=piano_config.fonts,
                font_size=piano_config.music_analysis_fonts_size,
                bold=piano_config.bold,
                x=piano_config.music_analysis_place[0],
                y=piano_config.music_analysis_place[1],
                color=piano_config.message_color,
                anchor_x=piano_config.label_anchor_x,
                anchor_y=piano_config.label_anchor_y,
                multiline=True,
                width=piano_config.music_analysis_width)
            if piano_config.music_analysis_file:
                with open(piano_config.music_analysis_file,
                          encoding='utf-8') as f:
                    data = f.read()
                    lines = [i for i in data.split('\n\n') if i]
                    self.music_analysis_list = []
                    self.current_key = None
                    bar_counter = 0
                    for each in lines:
                        if each:
                            if each[:3] != 'key':
                                current = each.split('\n')
                                current_bar = current[0]
                                if current_bar[0] == '+':
                                    bar_counter += eval(current_bar[1:])
                                else:
                                    bar_counter = eval(current_bar) - 1
                                current_chords = '\n'.join(current[1:])
                                if self.current_key:
                                    current_chords = f'{piano_config.key_header}{self.current_key}\n' + current_chords
                                self.music_analysis_list.append(
                                    [bar_counter, current_chords])
                            else:
                                self.current_key = each.split('key: ')[1]

    def init_piano_keys(self):
        self.piano_height = piano_config.white_key_y + piano_config.white_key_height
        self.piano_keys = []
        self.initial_colors = []
        if piano_config.draw_piano_keys:
            piano_background = get_image(piano_config.piano_background_image)
            if not piano_config.piano_size:
                ratio = self.screen_width / piano_background.width
                piano_background.width = self.screen_width
                piano_background.height *= ratio
            else:
                piano_background.width, piano_background.height = piano_config.piano_size
            self.piano_background_show = pyglet.sprite.Sprite(
                piano_background,
                x=0,
                y=0,
                batch=self.batch,
                group=self.piano_bg)
            for i in range(piano_config.white_keys_number):
                current_piano_key = pyglet.shapes.BorderedRectangle(
                    x=piano_config.white_key_start_x +
                    piano_config.white_key_interval * i,
                    y=piano_config.white_key_y,
                    width=piano_config.white_key_width,
                    height=piano_config.white_key_height,
                    color=piano_config.white_key_color,
                    batch=self.batch,
                    group=self.piano_key,
                    border=piano_config.piano_key_border,
                    border_color=piano_config.piano_key_border_color)
                current_piano_key.current_color = None
                self.piano_keys.append(current_piano_key)
                self.initial_colors.append(
                    (current_piano_key.x, piano_config.white_key_color))
            first_black_key = pyglet.shapes.BorderedRectangle(
                x=piano_config.black_key_first_x,
                y=piano_config.black_key_y,
                width=piano_config.black_key_width,
                height=piano_config.black_key_height,
                color=piano_config.black_key_color,
                batch=self.batch,
                group=self.piano_key,
                border=piano_config.piano_key_border,
                border_color=piano_config.piano_key_border_color)
            first_black_key.current_color = None
            self.piano_keys.append(first_black_key)
            self.initial_colors.append(
                (first_black_key.x, piano_config.black_key_color))
            current_start = piano_config.black_key_start_x
            for j in range(piano_config.black_keys_set_num):
                for k in piano_config.black_keys_set:
                    current_start += k
                    current_piano_key = pyglet.shapes.BorderedRectangle(
                        x=current_start,
                        y=piano_config.black_key_y,
                        width=piano_config.black_key_width,
                        height=piano_config.black_key_height,
                        color=piano_config.black_key_color,
                        batch=self.batch,
                        group=self.piano_key,
                        border=piano_config.piano_key_border,
                        border_color=piano_config.piano_key_border_color)
                    current_piano_key.current_color = None
                    self.piano_keys.append(current_piano_key)
                    self.initial_colors.append(
                        (current_start, piano_config.black_key_color))
                current_start += piano_config.black_keys_set_interval
            self.piano_keys.sort(key=lambda s: s.x)
            self.initial_colors.sort(key=lambda s: s[0])
            self.initial_colors = [t[1] for t in self.initial_colors]
            self.note_place = [(each.x, each.y) for each in self.piano_keys]
            self.bar_offset_x = 0

    def init_parameters(self):
        self.mouse_left = 1
        self.mouse_pos = 0, 0
        self.first_time = True
        self.message_label = False
        self.is_click = False
        self.mode_num = None
        self.func = None
        self.click_mode = None
        self.bar_offset_x = piano_config.bar_offset_x

    def init_midi_file(self):
        init_result = current_piano_engine.init_midi_show()
        if init_result == 'back':
            self.mode_num = 4
        else:
            self.func = current_piano_engine.mode_midi_show
            self.not_first()
            pyglet.clock.schedule_interval(self.func, 1 / piano_config.fps)

    def on_mouse_motion(self, x, y, dx, dy):
        self.mouse_pos = x, y

    def on_mouse_press(self, x, y, button, modifiers):
        pass

    def on_draw(self):
        self.clear()
        self.background.blit(0, 0)
        if not piano_config.draw_piano_keys:
            self.image_show.draw()
        if self.batch:
            self.batch.draw()
        self.label_midi_device.draw()
        self._draw_window()

    def _draw_window(self):
        if self.is_click:
            self.is_click = False
            self.not_first()
            self.label.text = ''
            self.label2.text = ''
            self.mode_num = None
        self.label.draw()
        self.label2.draw()
        if self.message_label:
            self.label3.draw()
        if piano_config.show_music_analysis:
            self.music_analysis_label.draw()

    def redraw(self):
        self.clear()
        self.background.blit(0, 0)
        if not piano_config.draw_piano_keys:
            self.image_show.draw()
        if self.batch:
            self.batch.draw()
        self.label_midi_device.draw()
        self.label2.draw()
        if self.message_label:
            self.label3.draw()
        if piano_config.show_music_analysis:
            self.music_analysis_label.draw()

    def reset_click_mode(self):
        self.click_mode = None

    def not_first(self):
        self.first_time = not self.first_time

    def open_settings(self):
        self.keyboard_handler[self.config_key] = False
        self.keyboard_handler[key.S] = False
        os.chdir(abs_path)
        current_config_window = config_window()
        current_config_window.mainloop()
        self.reload_settings()

    def reload_settings(self):
        importlib.reload(piano_config)
        self.init_parameters()
        self.init_keys()
        self.init_screen()
        self.init_layers()
        self.init_piano_keys()
        self.init_note_mode()
        self.init_screen_labels()
        self.init_music_analysis()

    def on_close(self):
        pygame.mixer.music.stop()
        pyglet.clock.unschedule(self.func)
        pyglet.clock.unschedule(current_piano_engine.midi_file_play)
        if not piano_config.use_soundfont and sys.platform == 'linux':
            try:
                os.remove(current_piano_engine.current_convert_name)
            except:
                pass
        self.close()


class piano_engine:

    def __init__(self):
        self.init_parameters()

    def init_parameters(self):
        self.notedic = piano_config.key_settings
        self.currentchord = mp.chord([])
        self.playnotes = []
        self.still_hold_pc = []
        self.still_hold = []
        self.paused = False
        self.pause_start = 0
        self.playls = []
        self.bars_drop_time = []
        self.plays = []
        self.midi_device_load = False
        self.current_midi_device = language_patch.ideal_piano_language_dict[
            'current_midi_device']
        self.device = None
        self.play_midi_file = False
        self.sostenuto_pedal_on = False
        self.soft_pedal_volume_ratio = 1

    def has_load(self, change):
        self.midi_device_load = change

    def configkey(self, current_key):
        return current_piano_window.keyboard_handler[
            current_piano_window.
            config_key] and current_piano_window.keyboard_handler[
                current_piano_window.map_key_dict2[current_key]]

    def configshow(self, content):
        current_piano_window.label.text = str(content)

    def switchs(self, current_key, name):
        if self.configkey(current_key):
            setattr(piano_config, name, not getattr(piano_config, name))
            self.configshow(
                f'{name} {language_patch.ideal_piano_language_dict["changes"]} {getattr(piano_config, name)}'
            )

    def detect_config(self):
        if self.configkey(piano_config.volume_up):
            if piano_config.global_volume + piano_config.volume_change_unit <= 1:
                piano_config.global_volume += piano_config.volume_change_unit
            else:
                piano_config.global_volume = 1
            [
                self.wavdic[j].set_volume(piano_config.global_volume)
                for j in self.wavdic
            ]
            self.configshow(
                f'volume up to {int(piano_config.global_volume*100)}%')
        if self.configkey(piano_config.volume_down):
            if piano_config.global_volume - piano_config.volume_change_unit >= 0:
                piano_config.global_volume -= piano_config.volume_change_unit
            else:
                piano_config.global_volume = 0
            [
                self.wavdic[j].set_volume(piano_config.global_volume)
                for j in self.wavdic
            ]
            self.configshow(
                f'volume down to {int(piano_config.global_volume*100)}%')
        self.switchs(piano_config.change_delay, 'delay')
        self.switchs(piano_config.change_read_current,
                     'delay_only_read_current')
        self.switchs(piano_config.change_pause_key_clear_notes,
                     'pause_key_clear_notes')

    def midi_file_play(self, dt):
        pygame.mixer.music.play()

    def piano_key_reset(self, dt, each):
        current_piano_window.piano_keys[
            each.degree -
            21].color = current_piano_window.initial_colors[each.degree - 21]

    def _detect_chord(self, current_chord):
        return mp.alg.detect(
            current_chord, piano_config.inv_num,
            piano_config.change_from_first, piano_config.original_first,
            piano_config.same_note_special, piano_config.whole_detect,
            piano_config.return_fromchord, piano_config.poly_chord_first,
            piano_config.root_position_return_first,
            piano_config.alter_notes_show_degree)

    def init_midi_show(self):
        current_setup = browse.setup()
        self.path = current_setup.file_path
        self.action = current_setup.action
        read_result = current_setup.read_result
        self.sheetlen = current_setup.sheetlen
        set_bpm = current_setup.set_bpm
        self.off_melody = current_setup.off_melody
        self.if_merge = current_setup.if_merge
        play_interval = current_setup.interval
        if self.action == 1:
            self.action = 0
            return 'back'
        if self.path and read_result:
            if read_result != 'error':
                self.bpm, self.musicsheet, start_time, actual_start_time = read_result
                self.musicsheet, new_start_time = self.musicsheet.pitch_filter(
                    *piano_config.pitch_range)
                start_time += new_start_time
                self.sheetlen = len(self.musicsheet)
                if set_bpm:
                    self.bpm = float(set_bpm)
            else:
                return 'back'
        else:
            return 'back'

        if self.off_melody:
            self.musicsheet = mp.split_chord(
                self.musicsheet, 'hold', piano_config.melody_tol,
                piano_config.chord_tol, piano_config.get_off_overlap_notes,
                piano_config.average_degree_length,
                piano_config.melody_degree_tol)
            self.sheetlen = len(self.musicsheet)
        if play_interval is not None:
            play_start, play_stop = int(
                self.sheetlen * (play_interval[0] / 100)), int(
                    self.sheetlen * (play_interval[1] / 100))
            self.musicsheet = self.musicsheet[play_start:play_stop]
            self.sheetlen = play_stop + 1 - play_start
        if self.sheetlen == 0:
            return 'back'
        pygame.mixer.set_num_channels(self.sheetlen)
        self.wholenotes = self.musicsheet.notes
        self.unit_time = 4 * 60 / self.bpm

        # every object in playls has a situation flag at the index of 3,
        # 0 means has not been played yet, 1 means it has started playing,
        # 2 means it has stopped playing
        self.musicsheet.start_time = start_time
        self.musicsheet.actual_start_time = actual_start_time
        self.playls = self._midi_show_init(self.musicsheet, self.unit_time,
                                           start_time)
        if piano_config.show_music_analysis:
            self.show_music_analysis_list = [[
                mp.add_to_last_index(self.musicsheet.interval, each[0]),
                each[1]
            ] for each in current_piano_window.music_analysis_list]
            self.default_show_music_analysis_list = copy(
                self.show_music_analysis_list)
        self.startplay = time.time()
        self.lastshow = None
        self.finished = False
        self.paused = False

    def _midi_show_init(self,
                        musicsheet,
                        unit_time,
                        start_time,
                        window_mode=0):
        self.play_midi_file = False
        playls = []
        self.start = start_time * unit_time + current_piano_window.bars_drop_interval
        self._midi_show_init_as_midi(musicsheet, unit_time, start_time, playls,
                                     window_mode)
        return playls

    def _midi_show_init_as_midi(self, musicsheet, unit_time, start_time,
                                playls, window_mode):
        self.play_midi_file = True
        if window_mode == 0:
            if not self.if_merge:
                mp.write(musicsheet,
                         60 / (unit_time / 4),
                         start_time=musicsheet.start_time,
                         name='temp.mid')
                self._load_file('temp.mid')
            else:
                with open(self.path, 'rb') as f:
                    if f.read(4) == b'RIFF':
                        is_riff_midi = True
                    else:
                        is_riff_midi = False
                if not is_riff_midi:
                    self._load_file(self.path)
                else:
                    current_path = mp.riff_to_midi(self.path)
                    current_buffer = current_path.getbuffer()
                    with open('temp.mid', 'wb') as f:
                        f.write(current_buffer)
                    self._load_file('temp.mid')
        current_start_time = current_piano_window.bars_drop_interval
        if sys.platform == 'linux' and not piano_config.use_soundfont:
            current_start_time += self.musicsheet.actual_start_time * self.unit_time
        pyglet.clock.schedule_once(self.midi_file_play, current_start_time)
        self._midi_show_init_note_list(musicsheet, unit_time, playls)

    def _load_file(self, path):
        pygame.mixer.music.load(path)

    def _midi_show_init_note_list(self, musicsheet, unit_time, playls, mode=0):
        musicsheet.clear_pitch_bend('all')
        self.musicsheet = musicsheet
        self.wholenotes = self.musicsheet.notes
        self.sheetlen = len(self.musicsheet)
        for i in range(self.sheetlen):
            currentnote = musicsheet.notes[i]
            duration = unit_time * currentnote.duration
            interval = unit_time * musicsheet.interval[i]
            currentstart = self.start
            currentstop = self.start + duration
            if mode == 0:
                currentwav = 0
            else:
                currentwav = pygame.mixer.Sound(
                    f'{piano_config.sound_path}/{currentnote}.{piano_config.sound_format}'
                )
                note_volume = currentnote.volume / 127
                note_volume *= piano_config.global_volume
                currentwav.set_volume(note_volume)
            playls.append(
                [currentwav, currentstart, currentstop, 0, i, currentnote])
            if piano_config.note_mode == 'bars drop':
                self.bars_drop_time.append(
                    (currentstart - current_piano_window.bars_drop_interval,
                     currentnote))
            self.start += interval

    def mode_midi_show(self, dt):
        if not self.paused:
            self._midi_show_playing()
        else:
            self._midi_show_pause()
        if self.finished:
            self._midi_show_finished()

    def _midi_show_playing(self):
        self.currentime = time.time() - self.startplay
        if piano_config.note_mode == 'bars drop':
            self._midi_show_draw_notes_bars_drop_mode()
        for k in range(self.sheetlen):
            nownote = self.playls[k]
            self._midi_show_play_current_note(nownote, k)

        self.playnotes = [
            self.wholenotes[x[4]] for x in self.playls if x[3] == 1
        ]
        if self.playnotes:
            self._midi_show_update_notes()
        self._midi_show_playing_read_pc_keyboard_key()

        if piano_config.note_mode == 'bars':
            self._midi_show_draw_notes_hit_key_bars_mode()
        elif piano_config.note_mode == 'bars drop':
            self._midi_show_draw_notes_hit_key_bars_drop_mode()

    def _midi_show_play_current_note(self, nownote, k):
        current_sound, start_time, stop_time, situation, number, current_note = nownote
        if situation != 2:
            if situation == 0:
                if self.currentime >= start_time:
                    if not self.play_midi_file:
                        current_sound.play()
                    nownote[3] = 1
                    if piano_config.show_music_analysis:
                        if self.show_music_analysis_list:
                            current_music_analysis = self.show_music_analysis_list[
                                0]
                            if k == current_music_analysis[0]:
                                current_piano_window.music_analysis_label.text = current_music_analysis[
                                    1]
                                del self.show_music_analysis_list[0]
                    if piano_config.note_mode == 'bars':
                        self._midi_show_draw_notes_bars_mode(current_note)
                    elif piano_config.note_mode != 'bars drop':
                        self._midi_show_set_piano_key_color(current_note)
            elif situation == 1:
                if self.currentime >= stop_time:
                    if not self.play_midi_file:
                        current_sound.fadeout(
                            current_piano_window.show_delay_time)
                    nownote[3] = 2
                    if k == self.sheetlen - 1:
                        self.finished = True

    def _midi_show_draw_notes_bars_drop_mode(self):
        if self.bars_drop_time:
            j = 0
            while j < len(self.bars_drop_time):
                next_bar_drop = self.bars_drop_time[j]
                if self.currentime >= next_bar_drop[0]:
                    current_note = next_bar_drop[1]
                    places = current_piano_window.note_place[
                        current_note.degree - 21]
                    current_bar = pyglet.shapes.BorderedRectangle(
                        x=places[0] + current_piano_window.bar_offset_x,
                        y=current_piano_window.screen_height,
                        width=piano_config.bar_width,
                        height=piano_config.bar_unit * current_note.duration /
                        (self.bpm / 130),
                        color=current_note.own_color
                        if piano_config.use_track_colors else
                        (piano_config.bar_color
                         if piano_config.color_mode == 'normal' else
                         (random.randint(0, 255), random.randint(0, 255),
                          random.randint(0, 255))),
                        batch=current_piano_window.batch,
                        group=current_piano_window.bottom_group,
                        border=piano_config.bar_border,
                        border_color=piano_config.bar_border_color)
                    current_bar.opacity = 255 * (
                        current_note.volume / 127
                    ) if piano_config.opacity_change_by_velocity else piano_config.bar_opacity
                    current_bar.num = current_note.degree - 21
                    current_bar.hit_key = False
                    self.plays.append(current_bar)
                    del self.bars_drop_time[j]
                    continue
                j += 1

    def _midi_show_draw_notes_bars_mode(self, current_note):
        places = current_piano_window.note_place[current_note.degree - 21]
        current_bar = pyglet.shapes.BorderedRectangle(
            x=places[0] + current_piano_window.bar_offset_x,
            y=piano_config.bar_y,
            width=piano_config.bar_width,
            height=piano_config.bar_unit * current_note.duration /
            (self.bpm / 130),
            color=current_note.own_color if piano_config.use_track_colors else
            (piano_config.bar_color if piano_config.color_mode == 'normal' else
             (random.randint(0, 255), random.randint(0, 255),
              random.randint(0, 255))),
            batch=current_piano_window.batch,
            group=current_piano_window.play_highlight,
            border=piano_config.bar_border,
            border_color=piano_config.bar_border_color)
        current_bar.opacity = 255 * (
            current_note.volume / 127
        ) if piano_config.opacity_change_by_velocity else piano_config.bar_opacity
        self.plays.append(current_bar)
        current_piano_window.piano_keys[current_note.degree -
                                        21].color = current_bar.color

    def _midi_show_update_notes(self):
        self.playnotes.sort(key=lambda x: x.degree)
        if self.playnotes != self.lastshow:
            if piano_config.draw_piano_keys and piano_config.note_mode != 'bars drop':
                if self.lastshow:
                    for each in self.lastshow:
                        if each not in self.playnotes:
                            current_piano_window.piano_keys[
                                each.degree -
                                21].color = current_piano_window.initial_colors[
                                    each.degree - 21]
            self.lastshow = self.playnotes
            if piano_config.show_notes:
                current_piano_window.label.text = str(self.playnotes)
            if piano_config.show_chord and any(
                    type(t) == mp.note for t in self.playnotes):
                chordtype = self._detect_chord(self.playnotes)
                current_piano_window.label2.text = str(
                    chordtype
                ) if not piano_config.sort_invisible else get_off_sort(
                    str(chordtype))

    def _midi_show_set_piano_key_color(self, current_note):
        current_piano_key = current_piano_window.piano_keys[current_note.degree
                                                            - 21]
        if piano_config.use_track_colors:
            current_piano_key.color = current_note.own_color
        else:
            if piano_config.color_mode == 'normal':
                current_piano_key.color = piano_config.bar_color
            else:
                current_piano_key.color = (random.randint(0, 255),
                                           random.randint(0, 255),
                                           random.randint(0, 255))

    def _midi_show_playing_read_pc_keyboard_key(self):
        if current_piano_window.keyboard_handler[
                current_piano_window.pause_key]:
            if self.play_midi_file:
                if pygame.mixer.music.get_busy():
                    pygame.mixer.music.pause()
                    self.paused = True
            else:
                self.paused = True
            if self.paused:
                self.pause_start = time.time()
                current_piano_window.message_label = True
                current_piano_window.label3.text = language_patch.ideal_piano_language_dict[
                    'pause'].format(unpause_key=piano_config.unpause_key)

    def _midi_show_draw_notes_hit_key_bars_mode(self):
        i = 0
        while i < len(self.plays):
            each = self.plays[i]
            each.y += current_piano_window.bar_steps
            if each.y >= current_piano_window.screen_height:
                each.batch = None
                del self.plays[i]
                continue
            i += 1

    def _midi_show_draw_notes_hit_key_bars_drop_mode(self):
        i = 0
        while i < len(self.plays):
            each = self.plays[i]
            each.y -= current_piano_window.bar_steps
            if not each.hit_key and each.y <= piano_config.bars_drop_place:
                each.hit_key = True
                if piano_config.draw_piano_keys:
                    current_piano_window.piano_keys[
                        each.num].color = each.color
            if each.height + each.y <= current_piano_window.piano_height:
                each.batch = None
                if piano_config.draw_piano_keys:
                    current_piano_window.piano_keys[
                        each.num].color = current_piano_window.initial_colors[
                            each.num]
                del self.plays[i]
                continue
            i += 1

    def _midi_show_pause(self):
        if current_piano_window.keyboard_handler[
                current_piano_window.unpause_key]:
            if self.play_midi_file:
                pygame.mixer.music.unpause()
            self.paused = False
            current_piano_window.message_label = False
            pause_stop = time.time()
            pause_time = pause_stop - self.pause_start
            self.startplay += pause_time

    def _midi_show_finished(self):
        if piano_config.draw_piano_keys and piano_config.note_mode != 'bars drop':
            if self.lastshow:
                for t in self.lastshow:
                    current_piano_window.piano_keys[
                        t.degree -
                        21].color = current_piano_window.initial_colors[
                            t.degree - 21]
        current_piano_window.label2.text = ''
        for each in self.plays:
            each.batch = None
        if piano_config.show_music_analysis:
            current_piano_window.music_analysis_label.text = ''
            self.show_music_analysis_list = copy(
                self.default_show_music_analysis_list)
        current_piano_window.label.text = language_patch.ideal_piano_language_dict[
            'repeat'].format(repeat_key=piano_config.repeat_key)
        if current_piano_window.keyboard_handler[
                current_piano_window.repeat_key]:
            if piano_config.note_mode == 'bars' or piano_config.note_mode == 'bars drop':
                self.plays.clear()
                if piano_config.note_mode == 'bars drop':
                    self.bars_drop_time.clear()
            if piano_config.draw_piano_keys:
                for k in range(len(current_piano_window.piano_keys)):
                    current_piano_window.piano_keys[
                        k].color = current_piano_window.initial_colors[k]
            self.playls.clear()
            current_piano_window.label.text = ''
            current_piano_window.redraw()
            self.playls = self._midi_show_init(self.musicsheet,
                                               self.unit_time,
                                               self.musicsheet.start_time,
                                               window_mode=1)
            self.startplay = time.time()
            self.lastshow = None
            self.playnotes.clear()
            self.finished = False


def start():
    global current_piano_engine
    global current_piano_window
    current_piano_engine = piano_engine()
    current_piano_window = piano_window()
    current_piano_window.init_midi_file()
    pyglet.clock.schedule_interval(update, 1 / piano_config.fps)
    pyglet.app.run()
