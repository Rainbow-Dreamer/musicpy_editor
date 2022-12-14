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
        self.run_button = self.get_button(text=current_language_dict['Run'],
                                          command=lambda: self.runs(mode=1))
        self.run_button.move(160, 0)
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
        self.wraplines_number = config_dict['wraplines_number']
        self.wraplines_button = self.get_button(
            text=current_language_dict['Word Wrap'], command=self.wraplines)
        self.print_box.move(550, 0)
        self.syntax_box.move(710, 0)
        self.wraplines_button.move(750, 400)
        self.is_print = True
        self.pre_input = ''
        self.changed = False
        self.input_completer = QtWidgets.QCompleter(function_names)
        self.inputs.setCompleter(self.input_completer)
        self.menu_bar = self.menuBar()
        self.file_menu = self.menu_bar.addMenu(current_language_dict['File'])
        self.file_menu.addAction(self.get_action(text=current_language_dict['Open'], command=self.openfile, shortcut='Ctrl+W'))
        self.menu_bar.addAction(self.get_action(text=current_language_dict['Save'], command=self.save_current_file, shortcut='Ctrl+S'))
        self.last_save = self.inputs.toPlainText()
        '''
        self.file_top = self.get_button(text=current_language_dict['File'],
                                   command=self.file_top_make_menu)
        self.file_menu = Menu(
            self,
            tearoff=0,
            bg=self.background_color,
            activebackground=self.active_background_color,
            activeforeground=self.active_foreground_color,
            disabledforeground=self.disabled_foreground_color)
        self.file_menu.add_command(label=current_language_dict['Open'],
                                   command=self.openfile,
                                   foreground=self.foreground_color)
        self.file_menu.add_command(label=current_language_dict['Save'],
                                   command=self.save_current_file,
                                   foreground=self.foreground_color)
        self.file_menu.add_command(label=current_language_dict['Save As'],
                                   command=self.save,
                                   foreground=self.foreground_color)
        self.file_menu.add_command(label=current_language_dict['Settings'],
                                   command=self.config_options,
                                   foreground=self.foreground_color)
        self.file_menu.add_command(
            label=current_language_dict['Import MIDI File'],
            command=self.read_midi_file,
            foreground=self.foreground_color)
        self.file_menu.add_command(
            label=current_language_dict['Visualize Settings'],
            command=self.visualize_config,
            foreground=self.foreground_color)
        self.file_top.move(x=0, y=0)
        self.config_button = ttk.Button(self,
                                        text=current_language_dict['Settings'],
                                        command=self.config_options)
        self.config_button.move(x=320, y=0)
        syntax_highlight = config_dict['syntax_highlight']
        for each in syntax_highlight:
            syntax_highlight[each].sort(key=lambda s: len(s), reverse=True)
        self.syntax_highlight = syntax_highlight
        for each in self.syntax_highlight:
            self.inputs.tag_configure(each, foreground=each)
        '''
        self.current_filename_path = None
        self.inputs.textChanged.connect(self.input_changed)
        QtWidgets.QShortcut('Ctrl+E', self).activated.connect(self.stop_play_midi)
        QtWidgets.QShortcut('Ctrl+D', self).activated.connect(self.read_midi_file)
        QtWidgets.QShortcut('Ctrl+R', self).activated.connect(self.runs)
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
        '''
        self.search_box_open = False
        self.config_box_open = False
        self.visualize_config_box_open = False
        self.current_line_number = 1
        self.current_column_number = 1
        self.line_column = QtWidgets.QLabel(
            self,
            text=
            f'Line {self.current_line_number} Col {self.current_column_number}'
        )
        self.line_column.move(750, 500)
        self.get_current_line_column()
        '''
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
        current_action = QtWidgets.QAction(QtGui.QIcon() if icon is None else QtGui.QIcon(icon), text, self)
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

    def visualize_config(self):
        if self.visualize_config_box_open:
            return
        self.visualize_config_box_open = True
        app = QtWidgets.QApplication(sys.argv)
        dpi = (app.screens()[0]).logicalDotsPerInch()
        current_config_window = config_window(dpi=dpi,
                                              config_path=piano_config_path)
        app.exec()
        del app
        self.visualize_config_box_open = False

    def get_current_line_column(self):
        ind = self.inputs.index(INSERT)
        line, column = ind.split('.')
        self.current_line_number = int(line)
        self.current_column_number = int(column)
        self.line_column.config(
            text=
            f'Line {self.current_line_number} Col {self.current_column_number}'
        )
        self.after(10, self.get_current_line_column)

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

    def file_top_make_menu(self):
        self.file_menu.tk_popup(x=self.winfo_pointerx(),
                                y=self.winfo_pointery())

    def wraplines(self):
        N = self.eachline_character
        text = self.outputs.get('1.0', END)
        K = len(text)
        text = ('\n' * self.wraplines_number).join(
            [text[i:i + N] for i in range(0, K, N)])
        self.outputs.delete('1.0', END)
        self.outputs.insert(END, text)

    def close_config_box(self):
        self.config_window.destroy()
        self.config_box_open = False

    def close_visualize_config_box(self):
        self.visualize_config_window.destroy()
        self.visualize_config_box_open = False
        os.chdir('../')

    def insert_bool(self, content):
        self.config_contents.delete('1.0', END)
        self.config_contents.insert(END, content)
        self.config_change()

    def config_change(self):
        current = self.config_contents.toPlainText()
        current_config = self.config_window.choose_config_options.get(ANCHOR)
        self.get_config_dict[current_config] = current

    def change_search_inds(self, num):
        self.config_window.search_inds += num
        if self.config_window.search_inds < 0:
            self.config_window.search_inds = 0
        if self.config_window.search_inds_list:
            search_num = len(self.config_window.search_inds_list)
            if self.config_window.search_inds >= search_num:
                self.config_window.search_inds = search_num - 1
            first = self.config_window.search_inds_list[
                self.config_window.search_inds]
            self.config_window.choose_config_options.selection_clear(0, END)
            self.config_window.choose_config_options.selection_set(first)
            self.config_window.choose_config_options.selection_anchor(first)
            self.config_window.choose_config_options.see(first)
            self.show_current_config_options()

    def search_config(self, *args):
        current = self.config_window.search_entry.get()
        self.config_window.search_inds_list = [
            i for i in range(self.config_window.options_num)
            if current in all_config_options[i]
        ]
        if self.config_window.search_inds_list:
            self.config_window.search_inds = 0
            first = self.config_window.search_inds_list[
                self.config_window.search_inds]
            self.config_window.choose_config_options.selection_clear(0, END)
            self.config_window.choose_config_options.selection_set(first)
            self.config_window.choose_config_options.selection_anchor(first)
            self.config_window.choose_config_options.see(first)
            self.show_current_config_options()
        else:
            self.config_window.choose_config_options.selection_clear(0, END)

    def show_current_config_options(self):
        current_config = self.config_window.choose_config_options.get(ANCHOR)
        self.config_window.config_name.configure(text=current_config)
        self.config_contents.delete('1.0', END)
        current_config_value = self.get_config_dict[current_config]
        self.config_contents.insert(END, current_config_value)

    def choose_filename(self):
        filename = filedialog.askopenfilename(
            parent=self.config_window,
            title=current_language_dict['Choose Filename'],
            filetypes=((current_language_dict['All files'], "*"), ))
        self.config_contents.delete('1.0', END)
        self.config_contents.insert(END, filename)
        self.config_change()

    def choose_directory(self):
        directory = filedialog.askdirectory(
            parent=self.config_window,
            title=current_language_dict['Choose Directory'],
        )
        self.config_contents.delete('1.0', END)
        self.config_contents.insert(END, directory)
        self.config_change()

    def config_options(self):
        if self.config_box_open:
            self.config_window.focus_set()
            return
        self.get_config_dict = copy(config_dict)
        self.get_config_dict = {
            i: str(j)
            for i, j in self.get_config_dict.items()
        }
        self.config_box_open = True
        self.config_window = Toplevel(self, bg=self.background_color)
        self.config_window.setMinimumSize(800, 650)
        self.config_window.title(current_language_dict['Settings'])
        self.config_window.protocol("WM_DELETE_WINDOW", self.close_config_box)

        global all_config_options
        all_config_options = list(self.get_config_dict.keys())
        self.options_num = len(all_config_options)
        global all_config_options_ind
        all_config_options_ind = {
            all_config_options[i]: i
            for i in range(self.options_num)
        }
        global config_original
        config_original = all_config_options.copy()
        global alpha_config
        alpha_config = all_config_options.copy()
        alpha_config.sort(key=lambda s: s.lower())
        self.config_window.options_num = len(all_config_options)
        self.config_window.config_options_bar = Scrollbar(self.config_window)
        self.config_window.config_options_bar.move(x=235,
                                                   y=120,
                                                   height=170,
                                                   anchor=CENTER)
        self.config_window.choose_config_options = Listbox(
            self.config_window,
            yscrollcommand=self.config_window.config_options_bar.set)
        for k in config_dict:
            self.config_window.choose_config_options.insert(END, k)
        self.config_window.choose_config_options.move(x=0, y=30, width=220)
        self.config_window.config_options_bar.config(
            command=self.config_window.choose_config_options.yview)
        self.config_window.config_name = QtWidgets.QLabel(self.config_window,
                                                          text='')
        self.config_window.config_name.move(x=300, y=20)
        self.config_window.choose_config_options.bind(
            '<<ListboxSelect>>', lambda e: self.show_current_config_options())
        self.config_contents = Text(self.config_window,
                                    undo=True,
                                    autoseparators=True,
                                    maxundo=-1)
        self.config_contents.bind('<KeyRelease>',
                                  lambda e: self.config_change())
        self.config_contents.move(x=350, y=50, width=400, height=200)
        self.config_window.choose_filename_button = ttk.Button(
            self.config_window,
            text=current_language_dict['Choose Filename'],
            command=self.choose_filename,
            width=20)
        self.config_window.choose_directory_button = ttk.Button(
            self.config_window,
            text=current_language_dict['Choose Directory'],
            command=self.choose_directory,
            width=20)
        self.config_window.choose_filename_button.move(x=0, y=250)
        self.config_window.choose_directory_button.move(x=0, y=290)
        self.config_window.search_text = QtWidgets.QLabel(
            self.config_window,
            text=current_language_dict['Search config options'])
        self.config_window.search_text.move(x=30, y=370)
        self.config_search_contents = StringVar()
        self.config_search_contents.trace_add('write', self.search_config)
        self.config_window.search_entry = Entry(
            self.config_window, textvariable=self.config_search_contents)
        self.config_window.search_entry.move(x=170, y=370)
        self.config_window.search_inds = 0
        self.config_window.up_button = ttk.Button(
            self.config_window,
            text=current_language_dict['Previous'],
            command=lambda: self.change_search_inds(-1),
            width=8)
        self.config_window.down_button = ttk.Button(
            self.config_window,
            text=current_language_dict['Next'],
            command=lambda: self.change_search_inds(1),
            width=8)
        self.config_window.up_button.move(x=170, y=400)
        self.config_window.down_button.move(x=250, y=400)
        self.config_window.search_inds_list = []
        self.config_window.value_dict = config_dict
        self.config_window.choose_bool1 = ttk.Button(
            self.config_window,
            text='True',
            command=lambda: self.insert_bool('True'))
        self.config_window.choose_bool2 = ttk.Button(
            self.config_window,
            text='False',
            command=lambda: self.insert_bool('False'))
        self.config_window.choose_bool1.move(x=150, y=270)
        self.config_window.choose_bool2.move(x=250, y=270)
        save_button = ttk.Button(self.config_window,
                                 text=current_language_dict['Save'],
                                 command=self.save_config)
        save_button.move(x=30, y=330)
        self.saved_label = QtWidgets.QLabel(
            self.config_window,
            text=current_language_dict['Successfully saved'])
        self.choose_font = ttk.Button(
            self.config_window,
            text=current_language_dict['Choose Font'],
            command=self.get_font)
        self.choose_font.move(x=230, y=460)
        self.whole_fonts = list(font.families())
        self.whole_fonts.sort(
            key=lambda x: x if not x.startswith('@') else x[1:])
        self.font_list_bar = ttk.Scrollbar(self.config_window)
        self.font_list_bar.move(x=190, y=520, height=170, anchor=CENTER)
        self.font_list = Listbox(self.config_window,
                                 yscrollcommand=self.font_list_bar.set,
                                 width=25)
        for k in self.whole_fonts:
            self.font_list.insert(END, k)
        self.font_list.move(x=0, y=430)
        self.font_list_bar.config(command=self.font_list.yview)
        current_font_ind = self.whole_fonts.index(self.font_type)
        self.font_list.selection_set(current_font_ind)
        self.font_list.see(current_font_ind)
        self.change_sort_button = ttk.Button(
            self.config_window,
            text="sort in order of appearance",
            command=self.change_sort)
        self.sort_mode = 1
        self.change_sort_button.move(x=150, y=330, width=180)

        self.reload_button = ttk.Button(self.config_window,
                                        text=current_language_dict['Reload'],
                                        command=self.reload)
        self.reload_button.move(x=230, y=510)

    def reload(self):
        self.destroy()
        self.save_config(True, False)
        try:
            os.startfile(__file__)
        except:
            os.startfile(sys.executable)

    def change_sort(self):
        global all_config_options
        if self.sort_mode == 0:
            self.sort_mode = 1
            self.change_sort_button.config(text='sort in order of appearance')
            all_config_options = config_original.copy()
            self.config_window.choose_config_options.delete(0, END)
            for k in all_config_options:
                self.config_window.choose_config_options.insert(END, k)
        else:
            self.sort_mode = 0
            self.change_sort_button.config(text='sort in alphabetical order')
            all_config_options = alpha_config.copy()
            self.config_window.choose_config_options.delete(0, END)
            for k in all_config_options:
                self.config_window.choose_config_options.insert(END, k)
        self.search_config()

    def get_font(self):
        self.font_type = self.font_list.get(ACTIVE)
        self.font_size = eval(self.get_config_dict['font_size'])
        self.inputs.configure(font=(self.font_type, self.font_size))
        self.outputs.configure(font=(self.font_type, self.font_size))
        self.get_config_dict['font_type'] = str(self.font_type)
        config_dict['font_type'] = self.font_type
        config_dict['font_size'] = self.font_size

    def save_config(self, outer=False, reload=True):
        if not outer:
            for each in config_dict:
                original = config_dict[each]
                changed = self.get_config_dict[each]
                if str(original) != changed:
                    if not isinstance(original, str):
                        config_dict[each] = eval(changed)
                    else:
                        config_dict[each] = changed
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_dict,
                      f,
                      indent=4,
                      separators=(',', ': '),
                      ensure_ascii=False)
        if not outer:
            self.saved_label.move(x=360, y=400)
            self.after(600, self.saved_label.place_forget)
        if reload:
            self.reload_config()

    def search_path(self, obj):
        filename = filedialog.askopenfilename(
            parent=self.config_window,
            title=current_language_dict['Choose Files'],
            filetypes=((current_language_dict['All files'], "*"), ))
        if filename:
            obj.delete(0, END)
            obj.insert(END, filename)

    def reload_config(self):
        try:
            bg_path = config_dict['background_image']
            if not bg_path:
                self.bg_label.configure(image='')
            else:
                self.bg = PIL.Image.open(bg_path)
                ratio = 600 / self.bg.height
                self.bg = self.bg.resize(
                    (int(self.bg.width * ratio), int(self.bg.height * ratio)),
                    PIL.Image.ANTIALIAS)
                self.bg = PIL.ImageTk.PhotoImage(self.bg)
                self.bg_label.configure(image=self.bg)
                bg_places = config_dict['background_places']
                self.bg_label.move(x=bg_places[0], y=bg_places[1])

        except:
            bg_path = config_dict['background_image']
            if not bg_path:
                self.bg = ''
            else:
                self.bg = PIL.Image.open(bg_path)
                ratio = 600 / self.bg.height
                self.bg = self.bg.resize(
                    (int(self.bg.width * ratio), int(self.bg.height * ratio)),
                    PIL.Image.ANTIALIAS)
                self.bg = PIL.ImageTk.PhotoImage(self.bg)
                self.bg_label = QtWidgets.QLabel(self, image=self.bg)
                bg_places = config_dict['background_places']
                self.bg_label.move(x=bg_places[0], y=bg_places[1])
        self.eachline_character = config_dict['eachline_character']
        self.pairing_symbols = config_dict['pairing_symbols']
        self.wraplines_number = config_dict['wraplines_number']
        self.syntax_highlight = config_dict['syntax_highlight']
        for each in self.syntax_highlight:
            self.inputs.tag_configure(each, foreground=each)

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
        print2(111, flush=True)
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

    def cut(self):
        self.inputs.event_generate("<<Cut>>")

    def copy(self):
        self.inputs.event_generate("<<Copy>>")

    def paste(self):
        self.inputs.event_generate('<<Paste>>')

    def choose_all(self):
        self.inputs.tag_add(SEL, '1.0', END)
        self.inputs.mark_set(INSERT, END)
        self.inputs.see(INSERT)

    def inputs_undo(self):
        try:
            self.inputs.edit_undo()
        except:
            pass

    def inputs_redo(self):
        try:
            self.inputs.edit_redo()
        except:
            pass

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
            filter=f'{current_language_dict["MIDI File"]} (*.mid);{current_language_dict["All files"]} (*)').filename[0]        
        if filename:
            self.inputs.insertPlainText(f"new_midi_file = read(\"{filename}\")\n")

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
        current_background_stylesheet = f'background-image: url("{bg_path}"); background-repeat: no-repeat; background-position: right; padding: {bg_places[0]}px {bg_places[1]}px {bg_places[2]}px {bg_places[3]}px; background-origin: content;}}'
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
