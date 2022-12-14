import traceback
import sys
import os
import re
from io import BytesIO
import json

abs_path = os.path.dirname(os.path.abspath(__file__))
os.chdir(abs_path)
try:
    from PyQt5 import QtGui, QtWidgets, QtCore
    import PIL.Image, PIL.ImageTk
    from yapf.yapflib.yapf_api import FormatCode
    import musicpy
    from visualization.packages.change_settings import config_window
    sys.path.append('visualization/packages')
    from visualization.packages import visualize
except ImportError:
    import traceback
    print(traceback.format_exc())
    app = QtWidgets.QApplication(sys.argv)
    current_messagebox = QtWidgets.QMessageBox()
    current_messagebox.setIcon(QtWidgets.QMessageBox.Warning)
    current_messagebox.setText(
        'Not all required python packages are installed.\nPlease run\npip install musicpy pillow pyglet==1.5.11 yapf pyqt5\nin the terminal to install the required packages for this editor.'
    )
    current_messagebox.setWindowTitle('Warning')
    current_messagebox.exec_()
    sys.exit(app.exec_())
    sys.exit(0)

musicpy_vars = dir(musicpy)
from musicpy import *

config_path = 'config.json'
piano_config_path = 'visualization/packages/piano_config.json'
with open(config_path, encoding='utf-8') as f:
    config_dict = json.load(f)
current_language = config_dict['language']
current_language_file = f'languages/{current_language}.json'
if not os.path.exists(current_language_file):
    Tk().withdraw()
    messagebox.showerror(
        message=f'Cannot find language file for {current_language}')
with open(current_language_file, encoding='utf-8') as f:
    current_language_dict = json.load(f)

print2 = print


def print(obj):
    current_editor.outputs.insertPlainText(str(obj))
    current_editor.outputs.insertPlainText('\n')


def direct_play(filename):
    if type(filename) == str:
        pygame.mixer.music.load(filename)
        pygame.mixer.music.play()
    else:
        try:
            result = BytesIO()
            filename.save(file=result)
            result.seek(0)
            pygame.mixer.music.load(result)
            result.close()
            pygame.mixer.music.play()
        except:
            pass


def set_font(font, dpi):
    if dpi != 96.0:
        font.setPointSize(font.pointSize() * (96.0 / dpi))
    return font


class Dialog(QtWidgets.QMainWindow):

    def __init__(self, caption, directory, filter, mode=0):
        super().__init__()
        if mode == 0:
            self.filename = QtWidgets.QFileDialog.getOpenFileName(
                self, caption=caption, directory=directory, filter=filter)
        elif mode == 1:
            self.directory = QtWidgets.QFileDialog.getExistingDirectory(
                self, caption=caption, directory=directory)
        elif mode == 2:
            self.filename = QtWidgets.QFileDialog.getSaveFileName(
                self, caption=caption, directory=directory, filter=filter)


class CompletionTextEdit(QtWidgets.QPlainTextEdit):

    def __init__(self, parent=None, pairing_symbols=[]):
        super().__init__(parent)
        self._completer = None
        self.pairing_symbols = pairing_symbols
        self.pairing_symbols_left = [each[0] for each in self.pairing_symbols]
        self.completion_prefix = ''
        self.default_completer_keys = [
            QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return, QtCore.Qt.Key_Escape,
            QtCore.Qt.Key_Tab, QtCore.Qt.Key_Backtab
        ]
        self.special_words = "~!@#$%^&*()+{}|:\"<>?,./;'[]\\-="
        self.current_completion_words = function_names

    def setCompleter(self, c):

        self._completer = c
        c.setWidget(self)
        c.setCompletionMode(QtWidgets.QCompleter.PopupCompletion)
        c.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        c.activated.connect(self.insertCompletion)

    def insertCompletion(self, completion):
        if self._completer.widget() is not self:
            return

        tc = self.textCursor()
        extra = len(completion) - len(self._completer.completionPrefix())
        tc.movePosition(QtGui.QTextCursor.Left)
        tc.movePosition(QtGui.QTextCursor.EndOfWord)

        if self.completion_prefix.lower() != completion[-extra:].lower():
            tc.insertText(completion[-extra:])
            self.setTextCursor(tc)
        if self.current_completion_words != function_names:
            self._completer.setModel(
                QtCore.QStringListModel(function_names, self._completer))
            self.current_completion_words = function_names

    def textUnderCursor(self):
        tc = self.textCursor()
        tc.select(QtGui.QTextCursor.WordUnderCursor)
        return tc.selectedText()

    def focusInEvent(self, e):
        if self._completer is not None:
            self._completer.setWidget(self)
        super().focusInEvent(e)

    def keyPressEvent(self, e):

        isShortcut = False
        current_text = e.text()

        if current_text and current_text[-1] in self.pairing_symbols_left:
            self._completer.popup().hide()
            ind = self.pairing_symbols_left.index(current_text[-1])
            current_pairing_symbol = self.pairing_symbols[ind][1]
            super().keyPressEvent(e)
            self.insertPlainText(current_pairing_symbol)
            self.moveCursor(QtGui.QTextCursor.PreviousCharacter)
            return

        if self._completer is not None and self._completer.popup().isVisible():
            if e.key() in self.default_completer_keys:
                e.ignore()
                return

        if e.key() == QtCore.Qt.Key_Period:
            current_whole_text = self.toPlainText()
            current_row = current_whole_text.split('\n')[-1].replace(' ', '')
            current_word = current_row.split(',')[-1]
            try:
                words = dir(eval(current_word))
                super().keyPressEvent(e)
                self._completer.setModel(
                    QtCore.QStringListModel(words, self._completer))
                self.current_completion_words = words
                isShortcut = True
            except:
                pass

        if self._completer is None or not isShortcut:
            super().keyPressEvent(e)

        ctrlOrShift = e.modifiers() & (QtCore.Qt.ControlModifier
                                       | QtCore.Qt.ShiftModifier)
        if self._completer is None or (ctrlOrShift and not current_text):
            return
        hasModifier = (e.modifiers() !=
                       QtCore.Qt.NoModifier) and not ctrlOrShift
        completionPrefix = self.textUnderCursor()
        self.completion_prefix = completionPrefix
        if not isShortcut and (hasModifier or len(current_text) == 0
                               or len(completionPrefix) < 1
                               or current_text[-1] in self.special_words):
            self._completer.popup().hide()
            return

        if completionPrefix != self._completer.completionPrefix():
            self._completer.setCompletionPrefix(completionPrefix)
            self._completer.popup().setCurrentIndex(
                self._completer.completionModel().index(0, 0))

        cr = self.cursorRect()
        cr.setWidth(
            self._completer.popup().sizeHintForColumn(0) +
            self._completer.popup().verticalScrollBar().sizeHint().width())
        self._completer.complete(cr)


class Editor(QtWidgets.QMainWindow):

    def __init__(self, dpi=None):
        super().__init__()
        self.setMinimumSize(1200, 750)
        self.setWindowTitle(f'Musicpy {current_language_dict["Editor"]}')
        self.background_color = config_dict['background_color']
        self.foreground_color = config_dict['foreground_color']
        self.active_background_color = config_dict['active_background_color']
        self.day_color, self.night_color = config_dict['day_and_night_colors']
        self.search_highlight_color = config_dict['search_highlight_color']
        self.button_background_color = config_dict['button_background_color']
        self.active_foreground_color = config_dict['active_foreground_color']
        self.disabled_foreground_color = config_dict[
            'disabled_foreground_color']
        self.dpi = dpi
        self.get_config_dict = copy(config_dict)
        self.get_config_dict = {
            i: str(j)
            for i, j in self.get_config_dict.items()
        }
        self.font_type = config_dict['font_type']
        self.font_size = config_dict['font_size']
        self.current_font = set_font(
            QtGui.QFont(self.font_type, self.font_size), self.dpi)
        self.inputs_text = self.get_label(
            text=current_language_dict['Input musicpy codes here'])
        self.inputs = CompletionTextEdit(
            self, pairing_symbols=config_dict['pairing_symbols'])
        self.inputs.setFixedSize(700, 200)
        self.inputs.setFont(self.current_font)
        self.inputs_text.move(0, 80)
        self.inputs.move(0, 110)
        self.outputs_text = self.get_label(
            text=current_language_dict['Output'])
        self.outputs = QtWidgets.QPlainTextEdit(self)
        self.outputs.setFont(self.current_font)
        self.outputs_text.move(0, 350)
        self.outputs.setFixedSize(700, 300)
        self.outputs.move(0, 380)
        self.realtime_box = self.get_checkbutton(
            text=current_language_dict['Real Time'],
            command=self.check_realtime)
        self.realtime_box.setChecked(True)
        self.realtime_box.move(current_language_dict['realtime_box_place'], 0)
        self.is_realtime = 1
        self.quit = False
        self.print_box = self.get_checkbutton(
            text=current_language_dict["Don't use print"],
            command=self.check_print)
        self.print_box.setChecked(True)
        self.is_syntax = True
        self.syntax_box = self.get_checkbutton(
            text=current_language_dict['Syntax Highlight'],
            command=self.check_syntax)
        self.syntax_box.setChecked(True)
        self.eachline_character = config_dict['eachline_character']
        self.pairing_symbols = config_dict['pairing_symbols']
        self.print_box.move(550, 0)
        self.syntax_box.move(710, 0)
        self.is_print = True
        self.pre_input = ''
        self.changed = False
        self.input_completer = QtWidgets.QCompleter(function_names)
        self.inputs.setCompleter(self.input_completer)
        self.menu_bar = self.menuBar()
        self.file_menu = self.menu_bar.addMenu(current_language_dict['File'])
        self.file_menu.addAction(
            self.get_action(text=current_language_dict['Open'],
                            command=self.openfile,
                            shortcut='Ctrl+W'))
        self.file_menu.addAction(
            self.get_action(text=current_language_dict['Save'],
                            command=self.save_current_file,
                            shortcut='Ctrl+S'))
        self.file_menu.addAction(
            self.get_action(text=current_language_dict['Save As'],
                            command=self.save))
        self.file_menu.addAction(
            self.get_action(text=current_language_dict['Import MIDI File'],
                            command=self.read_midi_file,
                            shortcut='Ctrl+D'))
        self.file_menu.addAction(
            self.get_action(text=current_language_dict['Settings'],
                            command=self.editor_config))
        self.file_menu.addAction(
            self.get_action(text=current_language_dict['Visualize Settings'],
                            command=self.visualize_config))
        self.menu_bar.addAction(
            self.get_action(text=current_language_dict['Save'],
                            command=self.save_current_file))
        self.menu_bar.addAction(
            self.get_action(text=current_language_dict['Run'],
                            command=lambda: self.runs(mode=1),
                            shortcut='Ctrl+R'))
        self.last_save = self.inputs.toPlainText()
        '''
        syntax_highlight = config_dict['syntax_highlight']
        for each in syntax_highlight:
            syntax_highlight[each].sort(key=lambda s: len(s), reverse=True)
        self.syntax_highlight = syntax_highlight
        for each in self.syntax_highlight:
            self.inputs.tag_configure(each, foreground=each)
        '''
        self.current_filename_path = None
        self.inputs.textChanged.connect(self.input_changed)
        QtWidgets.QShortcut('Ctrl+E',
                            self).activated.connect(self.stop_play_midi)
        '''
        self.bg_mode = config_dict['background_mode']
        self.turn_bg_mode = ttk.Button(
            self,
            text=current_language_dict['Light On']
            if self.bg_mode == 'black' else current_language_dict['Light Off'],
            command=self.change_background_color_mode)
        self.turn_bg_mode.move(x=240, y=0)
        self.change_background_color_mode(turn=False)
        '''
        '''
        self.bind('<Control-a>', lambda e: self.choose_all())
        self.bind('<Control-f>', lambda e: self.search_words())
        self.bind('<Control-e>', lambda e: self.stop_play_midi())
        self.bind('<Control-d>', lambda e: self.read_midi_file())
        self.bind('<Control-w>', lambda e: self.openfile())
        self.bind('<Control-s>', lambda e: self.save_current_file())
        self.bind('<Control-q>', lambda e: self.close_window())
        self.bind('<Control-r>', lambda e: self.runs())
        self.bind('<Control-g>',
                  lambda e: self.change_background_color_mode(True))
        self.bind('<Control-b>', lambda e: self.config_options())
        self.bind('<Control-n>', lambda e: self.visualize_config())
        self.inputs.bind('<Control-MouseWheel>',
                         lambda e: self.change_font_size(e))
        self.inputs.bind('<Alt-z>', lambda e: self.play_select_text())
        self.inputs.bind('<Alt-x>',
                         lambda e: self.visualize_play_select_text())
        self.protocol("WM_DELETE_WINDOW", self.close_window)
        '''

        self.search_box_open = False
        self.current_line_number = 1
        self.current_column_number = 1
        self.line_column = self.get_label(
            text=
            f'Line {self.current_line_number} Col {self.current_column_number}'
        )
        self.line_column.move(750, 500)
        self.current_config_window = None
        self.current_visual_config_window = None
        self.show()

    def get_button(self, command=None, **kwargs):
        current_button = QtWidgets.QPushButton(self, **kwargs)
        if command is not None:
            current_button.clicked.connect(command)
        current_button.setFont(self.current_font)
        current_button.adjustSize()
        return current_button

    def get_checkbutton(self, command=None, **kwargs):
        current_button = QtWidgets.QCheckBox(self, **kwargs)
        if command is not None:
            current_button.clicked.connect(command)
        current_button.setFont(self.current_font)
        current_button.adjustSize()
        return current_button

    def get_label(self, **kwargs):
        current_label = QtWidgets.QLabel(self, **kwargs)
        current_label.setFont(self.current_font)
        current_label.adjustSize()
        return current_label

    def get_action(self, text='', command=None, icon=None, shortcut=None):
        current_action = QtWidgets.QAction(
            QtGui.QIcon() if icon is None else QtGui.QIcon(icon), text, self)
        if command is not None:
            current_action.triggered.connect(command)
        if shortcut is not None:
            current_action.setShortcut(shortcut)
        return current_action

    def close_window(self):
        current_text = self.inputs.toPlainText()
        if current_text != self.last_save:
            self.ask_save_window = Toplevel(
                self,
                bg=self.background_color,
                highlightthickness=config_dict['highlight_thickness'],
                highlightbackground=config_dict['highlight_background'],
                highlightcolor=config_dict['highlight_color'])
            self.ask_save_window.wm_overrideredirect(True)
            self.ask_save_window.setMinimumSize(400, 150)
            ask_save_window_x = self.winfo_x()
            ask_save_window_y = self.winfo_y()
            self.ask_save_window.geometry(
                f"+{ask_save_window_x + 300}+{ask_save_window_y + 200}")
            self.ask_save_window.ask_save_label = QtWidgets.QLabel(
                self.ask_save_window,
                text=current_language_dict[
                    'The file has changed, do you want to save the changes?'])
            self.ask_save_window.ask_save_label.move(x=0, y=30)
            self.ask_save_window.save_button = ttk.Button(
                self.ask_save_window,
                text=current_language_dict['Save'],
                command=self.save_and_quit,
                style='New.TButton')
            self.ask_save_window.not_save_button = ttk.Button(
                self.ask_save_window,
                text=current_language_dict['Discard'],
                command=self.destroy_and_quit,
                style='New.TButton')
            self.ask_save_window.cancel_button = ttk.Button(
                self.ask_save_window,
                text=current_language_dict['Cancel'],
                command=self.ask_save_window.destroy,
                style='New.TButton')
            self.ask_save_window.save_button.move(x=0, y=100)
            self.ask_save_window.not_save_button.move(x=90, y=100)
            self.ask_save_window.cancel_button.move(x=200, y=100)
        else:
            self.destroy()
            self.save_config(True, False)

    def save_and_quit(self):
        self.save_current_file()
        if self.current_filename_path:
            self.destroy()
            self.save_config(True, False)

    def destroy_and_quit(self):
        self.destroy()
        self.save_config(True, False)

    def editor_config(self):
        if self.current_config_window is not None and self.current_config_window.isVisible(
        ):
            return
        self.current_config_window = config_window(dpi=self.dpi,
                                                   config_path=config_path,
                                                   parent=self)
        self.current_config_window.show()

    def visualize_config(self):
        if self.current_visual_config_window is not None and self.current_visual_config_window.isVisible(
        ):
            return
        self.current_visual_config_window = config_window(
            dpi=self.dpi, config_path=piano_config_path)
        self.current_visual_config_window.show()

    def get_current_line_column(self):
        self.current_line_number = self.inputs.textCursor().blockNumber() + 1
        self.current_column_number = self.inputs.textCursor().columnNumber(
        ) + 1
        self.line_column.setText(
            f'Line {self.current_line_number} Col {self.current_column_number}'
        )

    def change_font_size(self, e):
        num = e.delta // 120
        self.font_size += num
        if self.font_size < 1:
            self.font_size = 1
        config_dict['font_size'] = self.font_size
        self.get_config_dict['font_size'] = str(self.font_size)
        self.inputs.configure(font=(self.font_type, self.font_size))
        self.outputs.configure(font=(self.font_type, self.font_size))

    def change_background_color_mode(self, turn=True):
        if turn:
            self.bg_mode = 'white' if self.bg_mode == 'black' else 'black'
        if self.bg_mode == 'white':
            self.inputs.configure(bg=self.day_color,
                                  fg='black',
                                  insertbackground='black')
            self.outputs.configure(bg=self.day_color,
                                   fg='black',
                                   insertbackground='black')
            self.bg_mode = 'white'
            self.turn_bg_mode.configure(
                text=current_language_dict['Light Off'])
        elif self.bg_mode == 'black':
            self.inputs.configure(background=self.night_color,
                                  foreground='white',
                                  insertbackground='white')
            self.outputs.configure(background=self.night_color,
                                   foreground='white',
                                   insertbackground='white')
            self.bg_mode = 'black'
            self.turn_bg_mode.configure(text=current_language_dict['Light On'])
        if turn:
            config_dict['background_mode'] = self.bg_mode

    def openfile(self):
        filename = Dialog(
            caption=current_language_dict['Choose Files'],
            directory='',
            filter=f'{current_language_dict["All files"]} (*)').filename[0]
        if filename:
            self.current_filename_path = filename
            try:
                with open(filename, encoding='utf-8', errors='ignore') as f:
                    self.inputs.clear()
                    self.inputs.insertPlainText(f.read())
                    self.last_save = self.inputs.toPlainText()
            except:
                pass

    def reload_config(self):
        global config_dict
        with open(config_path, encoding='utf-8') as f:
            config_dict = json.load(f)
        current_stylesheet = get_stylesheet()
        app.setStyleSheet(current_stylesheet)
        self.eachline_character = config_dict['eachline_character']
        self.pairing_symbols = config_dict['pairing_symbols']
        self.syntax_highlight = config_dict['syntax_highlight']
        #for each in self.syntax_highlight:
        #self.inputs.tag_configure(each, foreground=each)

        try:
            self.font_size = eval(self.get_config_dict['font_size'])
            self.inputs.configure(font=(self.font_type, self.font_size))
            self.outputs.configure(font=(self.font_type, self.font_size))
        except:
            pass

    def save_current_file(self):
        current_text = self.inputs.toPlainText()
        if current_text != self.last_save:
            if self.current_filename_path:
                self.last_save = self.inputs.toPlainText()
                with open(self.current_filename_path, 'w',
                          encoding='utf-8') as f:
                    f.write(self.last_save)
            else:
                self.save()
            self.setWindowTitle(f'Musicpy {current_language_dict["Editor"]}')

    def save(self):
        filename = Dialog(caption=current_language_dict["Save Input Text"],
                          directory='',
                          filter=f'{current_language_dict["All files"]} (*)',
                          mode=2).filename[0]
        if filename:
            current_filename, file_extension = os.path.splitext(filename)
            if not file_extension:
                filename = f'{current_filename}.txt'
            self.current_filename_path = filename
            current_text = self.inputs.toPlainText()
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(current_text)
            self.last_save = current_text

    def runs(self, mode=0):
        if not self.is_realtime:
            text = self.inputs.toPlainText()
        else:
            text = self.pre_input
        lines = text.split('\n')
        for i in range(len(lines)):
            each = lines[i]
            if each:
                if each[0] == '/':
                    lines[i] = f'play({each[1:]})'
                elif each[0] == '?':
                    lines[i] = f'alg.detect({each[1:]})'
        text = '\n'.join(lines)
        try:
            current_outputs = self.outputs.toPlainText()
            self.outputs.clear()
            exec(text, globals())
        except:
            self.outputs.insertPlainText(current_outputs)
            if mode == 1:
                self.outputs.clear()
                self.outputs.insertPlainText(traceback.format_exc())
            return
        if self.is_print:
            for each in lines:
                try:
                    if 'play(' not in each:
                        print(eval(each))
                except:
                    pass

    def syntax_highlight_func(self):
        end_index = self.inputs.index(END)
        start_x = self.inputs.index(INSERT).split('.')[0]
        for color, texts in self.syntax_highlight.items():
            self.inputs.tag_remove(color, f'{start_x}.0', END)
            for i in texts:
                start_index = '1.0'
                current_last_index = '1.0'
                while self.inputs.compare(start_index, '<', end_index):
                    current_text_index = self.inputs.search(i,
                                                            start_index,
                                                            stopindex=END)
                    if current_text_index:
                        word_length = len(i)
                        x, y = current_text_index.split('.')
                        current_last_index = f"{x}.{int(y)+word_length}"
                        next_index_end = f"{x}.{int(y)+2*word_length}"
                        last_index_start = f"{x}.{int(y)-word_length}"
                        if self.inputs.get(
                                current_last_index,
                                next_index_end) != i and self.inputs.get(
                                    last_index_start, current_text_index) != i:
                            self.inputs.tag_add(color, current_text_index,
                                                current_last_index)
                        start_index = current_last_index
                    else:
                        x, y = start_index.split('.')
                        if self.inputs.get(start_index) == '\n':
                            x = int(x) + 1
                        y = int(y) + 1
                        start_index = f'{x}.{y}'

    def input_changed(self):
        self.get_current_line_column()
        current_text = self.inputs.toPlainText()
        if current_text != self.last_save:
            self.setWindowTitle(f'Musicpy {current_language_dict["Editor"]} *')
        else:
            self.setWindowTitle(f'Musicpy {current_language_dict["Editor"]}')
        if self.quit or (not self.is_realtime):
            self.quit = False
            return
        global function_names
        function_names = list(set(musicpy_vars + list(locals().keys())))
        if self.is_syntax:
            #self.syntax_highlight_func()
            pass
        self.pre_input = self.inputs.toPlainText()
        self.runs()

    def check_realtime(self):
        value = self.realtime_box.isChecked()
        if value:
            self.is_realtime = 1
        else:
            self.is_realtime = 0
            self.quit = True

    def check_print(self):
        self.is_print = self.print_box.isChecked()

    def check_syntax(self):
        self.is_syntax = self.syntax_box.isChecked()

    def play_select_text(self):
        try:
            selected_text = self.inputs.selection_get()
            exec(f"play({selected_text})")
        except:
            self.outputs.delete('1.0', END)
            self.outputs.insert(
                END,
                current_language_dict['The codes selected cannot be played'])

    def visualize_play_select_text(self):
        try:
            selected_text = self.inputs.selection_get()
            exec(f"write({selected_text}, name='temp.mid')")
        except:
            self.outputs.delete('1.0', END)
            self.outputs.insert(
                END,
                current_language_dict['The codes selected cannot be played'])
            return
        visualize.start()

    def read_midi_file(self):
        filename = Dialog(
            caption=current_language_dict["Choose MIDI File"],
            directory='',
            filter=
            f'{current_language_dict["MIDI File"]} (*.mid);{current_language_dict["All files"]} (*)'
        ).filename[0]
        if filename:
            self.inputs.insertPlainText(
                f"new_midi_file = read(\"{filename}\")\n")

    def stop_play_midi(self):
        pygame.mixer.music.stop()

    def close_search_box(self):
        for each in self.search_inds_list:
            ind1, ind2 = each
            self.inputs.tag_remove('highlight', ind1, ind2)
            self.inputs.tag_remove('highlight_select', ind1, ind2)
        self.search_box.destroy()
        self.search_box_open = False

    def search_words(self):
        if not self.search_box_open:
            self.search_box_open = True
        else:
            self.search_box.focus_set()
            self.search_entry.focus_set()
            return
        self.search_box = Toplevel(self, bg=self.background_color)
        self.search_box.protocol("WM_DELETE_WINDOW", self.close_search_box)
        self.search_box.title(current_language_dict['Search'])
        self.search_box.setMinimumSize(300, 200)
        self.search_box.geometry('250x150+350+300')
        self.search_text = QtWidgets.QLabel(
            self.search_box,
            text=current_language_dict['Please input text you want to search'])
        self.search_text.move(x=0, y=0)
        self.search_contents = StringVar()
        self.search_contents.trace_add('write', self.search)
        self.search_entry = Entry(self.search_box,
                                  textvariable=self.search_contents)
        self.search_entry.move(x=0, y=30)
        self.search_entry.focus_set()
        self.search_inds = 0
        self.search_inds_list = []
        self.inputs.tag_configure('highlight',
                                  background=self.search_highlight_color[0])
        self.inputs.tag_configure('highlight_select',
                                  background=self.search_highlight_color[1])
        self.search_up = ttk.Button(self.search_box,
                                    text=current_language_dict['Previous'],
                                    command=lambda: self.change_search_ind(-1))
        self.search_down = ttk.Button(
            self.search_box,
            text=current_language_dict['Next'],
            command=lambda: self.change_search_ind(1))
        self.search_up.move(x=0, y=60)
        self.search_down.move(x=100, y=60)
        self.case_sensitive = False
        self.check_case_sensitive = IntVar()
        self.check_case_sensitive.set(0)
        self.case_sensitive_box = QtWidgets.QCheckBox(
            self.search_box,
            text=current_language_dict['Case sensitive'],
            variable=self.check_case_sensitive)
        self.case_sensitive_box.move(x=170, y=30)

    def change_search_ind(self, ind):
        length = len(self.search_inds_list)
        if self.search_inds in range(length):
            current_inds = self.search_inds_list[self.search_inds]
            self.inputs.tag_remove('highlight_select', current_inds[0],
                                   current_inds[1])
        self.search_inds += ind
        if self.search_inds < 0:
            self.search_inds = length - 1
        elif self.search_inds >= length:
            self.search_inds = 0
        if self.search_inds in range(length):
            current_inds = self.search_inds_list[self.search_inds]
            self.inputs.tag_add('highlight_select', current_inds[0],
                                current_inds[1])
            self.inputs.see(current_inds[1])

    def search(self, *args):
        all_text = self.inputs.toPlainText()

        for each in self.search_inds_list:
            ind1, ind2 = each
            self.inputs.tag_remove('highlight', ind1, ind2)
            self.inputs.tag_remove('highlight_select', ind1, ind2)
        current = self.search_contents.get()
        self.case_sensitive = self.check_case_sensitive.get()
        if not self.case_sensitive:
            all_text = all_text.lower()
            current = current.lower()
        self.search_inds_list = [[
            m.start(), m.end()
        ] for m in re.finditer(re.escape(current), all_text)]
        for each in self.search_inds_list:
            ind1, ind2 = each
            newline = "\n"
            ind1 = f'{all_text[:ind1].count(newline)+1}.{ind1 - all_text[:ind1].rfind(newline) - 1}'
            ind2 = f'{all_text[:ind2].count(newline)+1}.{ind2 - all_text[:ind2].rfind(newline) - 1}'
            each[0] = ind1
            each[1] = ind2
        self.outputs.delete('1.0', END)
        if self.search_inds_list:
            for each in self.search_inds_list:
                ind1, ind2 = each
                self.inputs.tag_add('highlight', ind1, ind2)


def get_stylesheet():
    if config_dict['background_image']:
        bg_path = config_dict['background_image']
        bg_places = config_dict['background_places']
        current_background_stylesheet = f'background-image: url("{bg_path}"); background-repeat: no-repeat; background-position: right; padding: {bg_places[0]}px {bg_places[1]}px {bg_places[2]}px {bg_places[3]}px; background-origin: content;'
    else:
        current_background_stylesheet = ''
    result = f'''
    QMainWindow {{
    background-color: {config_dict["background_color"]}; {current_background_stylesheet}
    }}
    QPushButton {{
    background-color: transparent;
    color: {config_dict["foreground_color"]};
    }}
    QPushButton:hover {{
    background-color: {config_dict["active_background_color"]};
    color: {config_dict["active_foreground_color"]};
    }}
    QCheckBox {{
    background-color: transparent;
    color: {config_dict["foreground_color"]};
    }}
    QLabel {{
    background-color: transparent;
    }}
'''
    return result


if __name__ == '__main__':
    function_names = list(set(musicpy_vars))
    app = QtWidgets.QApplication(sys.argv)
    current_stylesheet = get_stylesheet()
    app.setStyleSheet(current_stylesheet)
    dpi = (app.screens()[0]).logicalDotsPerInch()
    current_editor = Editor(dpi=dpi)
    app.exec()
