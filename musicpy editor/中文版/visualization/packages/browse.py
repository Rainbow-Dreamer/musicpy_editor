import time
import musicpy as mp
import os
import sys
import piano_config
import importlib


class setup:
    def __init__(self):
        self.file_path = 'temp.mid'
        self.action = 0
        self.track_ind_get = None
        self.interval = None
        self.read_result = None
        self.sheetlen = None
        self.set_bpm = None
        self.off_melody = 0
        self.if_merge = True
        self.load_midi_file()

    def load_midi_file(self):
        try:
            all_tracks = mp.read(self.file_path,
                                 self.track_ind_get,
                                 mode='all',
                                 get_off_drums=piano_config.get_off_drums,
                                 to_piece=True)
        except:
            all_tracks = mp.read(self.file_path,
                                 self.track_ind_get,
                                 mode='all',
                                 get_off_drums=piano_config.get_off_drums,
                                 to_piece=True,
                                 split_channels=True)
        all_tracks.normalize_tempo()
        all_tracks = [(all_tracks.bpm, all_tracks.tracks[i],
                       all_tracks.start_times[i])
                      for i in range(len(all_tracks.tracks))]
        pitch_bends = mp.concat(
            [i[1].split(mp.pitch_bend, get_time=True) for i in all_tracks])
        for each in all_tracks:
            each[1].clear_pitch_bend('all')
        start_time_ls = [j[2] for j in all_tracks]
        first_track_ind = start_time_ls.index(min(start_time_ls))
        all_tracks.insert(0, all_tracks.pop(first_track_ind))
        if piano_config.use_track_colors:
            color_num = len(all_tracks)
            import random
            if not piano_config.use_default_tracks_colors:
                colors = []
                for i in range(color_num):
                    current_color = tuple(
                        [random.randint(0, 255) for j in range(3)])
                    while (colors == (255, 255, 255)) or (current_color
                                                          in colors):
                        current_color = tuple(
                            [random.randint(0, 255) for j in range(3)])
                    colors.append(current_color)
            else:
                colors = piano_config.tracks_colors
                colors_len = len(colors)
                if colors_len < color_num:
                    for k in range(color_num - colors_len):
                        current_color = tuple(
                            [random.randint(0, 255) for j in range(3)])
                        while (colors == (255, 255, 255)) or (current_color
                                                              in colors):
                            current_color = tuple(
                                [random.randint(0, 255) for j in range(3)])
                        colors.append(current_color)
        first_track = all_tracks[0]
        tempo, all_track_notes, first_track_start_time = first_track
        for i in range(len(all_tracks)):
            current = all_tracks[i]
            current_track = current[1]
            if piano_config.use_track_colors:
                current_color = colors[i]
                for each in current_track:
                    each.own_color = current_color
            if i > 0:
                all_track_notes &= (current_track,
                                    current[2] - first_track_start_time)
        all_track_notes += pitch_bends
        if self.set_bpm:
            tempo = float(self.set_bpm)
        self.read_result = tempo, all_track_notes, first_track_start_time
