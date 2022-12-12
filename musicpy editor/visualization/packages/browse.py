import musicpy as mp
from change_settings import json_module

piano_config_path = 'visualization/packages/piano_config.json'
piano_config = json_module(piano_config_path)


class setup:

    def __init__(self, browse_dict, file_name=None):
        global piano_config
        piano_config = json_module(piano_config_path)
        self.file_path = 'temp.mid'
        self.action = 0
        self.track_ind_get = None
        self.read_result = None
        self.sheetlen = None
        self.set_bpm = None
        self.show_mode = 0
        self.if_merge = True
        state = []
        result = []
        self.read_midi_file(state, result)
        self.read_result = result[0]

    def read_midi_file(self, state, result):
        try:
            all_tracks = mp.read(self.file_path, get_off_drums=False)
            current_piece = mp.copy(all_tracks)
            all_tracks.normalize_tempo()
            all_tracks.get_off_not_notes()
            current_bpm = all_tracks.bpm
            actual_start_time = min(all_tracks.start_times)
            drum_tracks = []
            if piano_config.get_off_drums:
                drum_tracks = [
                    all_tracks[i] for i, each in enumerate(all_tracks.channels)
                    if each == 9
                ]
                all_tracks.get_off_drums()
            if not self.if_merge:
                if self.track_ind_get is not None:
                    all_tracks = [
                        (all_tracks.tracks[self.track_ind_get], current_bpm,
                         all_tracks.start_times[self.track_ind_get])
                    ]
                else:
                    all_tracks = [(all_tracks.tracks[0], current_bpm,
                                   all_tracks.start_times[0])]
                all_tracks[0][0].reset_track(0)
            else:
                all_tracks = [(all_tracks.tracks[i], current_bpm,
                               all_tracks.start_times[i])
                              for i in range(len(all_tracks.tracks))]

            pitch_bends = mp.concat(
                [i[0].split(mp.pitch_bend, get_time=True) for i in all_tracks])
            for each in all_tracks:
                each[0].clear_pitch_bend('all')
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
            all_track_notes, tempo, first_track_start_time = first_track
            for i in range(len(all_tracks)):
                current = all_tracks[i]
                current_track = current[0]
                if piano_config.use_track_colors:
                    current_color = colors[i]
                    for each in current_track:
                        each.own_color = current_color
                if i > 0:
                    all_track_notes &= (current_track,
                                        current[2] - first_track_start_time)
            all_track_notes += pitch_bends
            if self.set_bpm is not None:
                if float(self.set_bpm) == round(tempo, 3):
                    self.set_bpm = None
                else:
                    tempo = float(self.set_bpm)
            first_track_start_time += all_track_notes.start_time
            result.append([
                all_track_notes, tempo, first_track_start_time,
                actual_start_time, drum_tracks, current_piece
            ])
            state.append(True)
        except:
            import traceback
            state.append(traceback.format_exc())
