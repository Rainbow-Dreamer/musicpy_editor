import traceback
import sys
import os
from io import BytesIO
import json
from multiprocessing import Process

abs_path = os.path.dirname(os.path.abspath(__file__))
os.chdir(abs_path)
try:
    from PyQt5 import QtGui, QtWidgets, QtCore, Qt
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
        'Not all required python packages are installed.\nPlease follow the steps in the following link to install the required packages for this editor:\nhttps://github.com/Rainbow-Dreamer/musicpy_editor#installation'
    )
    current_messagebox.setWindowTitle('Warning')
    current_messagebox.show()
    app.exec()
    del current_messagebox
    del app
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
    app = QtWidgets.QApplication(sys.argv)
    current_messagebox = QtWidgets.QMessageBox()
    current_messagebox.setIcon(QtWidgets.QMessageBox.Warning)
    current_messagebox.setText(
        f'Cannot find language file for {current_language}')
    current_messagebox.setWindowTitle('Warning')
    current_messagebox.show()
    app.exec()
    del current_messagebox
    del app
    current_language = 'English'
    current_language_file = f'languages/{current_language}.json'
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
        font.setPointSize(int(font.pointSize() * (96.0 / dpi)))
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


class CustomTextEdit(QtWidgets.QPlainTextEdit):

    def __init__(self,
                 parent=None,
                 pairing_symbols=[],
                 custom_actions=[],
                 size=None,
                 font=None,
                 place=None):
        super().__init__(parent)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.__contextMenu)
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
        self.custom_actions = custom_actions
        if size is not None:
            self.setFixedSize(*size)
        if font is not None:
            self.setFont(font)
        if place is not None:
            self.move(*place)
        self.input_completer = QtWidgets.QCompleter(function_names)
        self.setCompleter(self.input_completer)

    def __contextMenu(self):
        self._normalMenu = self.createStandardContextMenu()
        self._addCustomMenuItems(self._normalMenu)
        self._normalMenu.exec_(QtGui.QCursor.pos())

    def _addCustomMenuItems(self, menu):
        menu.addSeparator()
        menu.addActions(self.custom_actions)

    def setCompleter(self, completer):

        self._completer = completer
        completer.setWidget(self)
        completer.setCompletionMode(QtWidgets.QCompleter.PopupCompletion)
        completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        completer.activated.connect(self.insertCompletion)

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
        hasModifier = (e.modifiers()
                       != QtCore.Qt.NoModifier) and not ctrlOrShift
        completionPrefix = self.textUnderCursor()
        self.completion_prefix = completionPrefix
        if not isShortcut and (hasModifier or len(current_text) == 0
                               or len(completionPrefix) < 1
                               or current_text[-1] in self.special_words):
            self._completer.popup().hide()
            if self.current_completion_words != function_names:
                self._completer.setModel(
                    QtCore.QStringListModel(function_names, self._completer))
                self.current_completion_words = function_names
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

    def zoom(self, delta):
        if delta < 0:
            self.zoomOut(1)
        elif delta > 0:
            self.zoomIn(1)

    def wheelEvent(self, event):
        if (event.modifiers() & QtCore.Qt.ControlModifier):
            self.zoom(event.angleDelta().y())
        else:
            super().wheelEvent(event)


def format_color(color, style=''):
    """
    Return a QtGui.QTextCharFormat with the given attributes.
    """
    _color = QtGui.QColor()
    if type(color) is not str:
        _color.setRgb(color[0], color[1], color[2])
    else:
        _color.setNamedColor(color)

    _format = QtGui.QTextCharFormat()
    _format.setForeground(_color)
    if 'bold' in style:
        _format.setFontWeight(QtGui.QFont.Bold)
    if 'italic' in style:
        _format.setFontItalic(True)

    return _format


styles = {
    'keyword': format_color([150, 85, 140], 'bold'),
    'operator': format_color('red'),
    'brace': format_color('darkGray'),
    'defclass': format_color([220, 220, 255], 'bold'),
    'string': format_color([20, 110, 100]),
    'string2': format_color([30, 120, 110]),
    'comment': format_color([128, 128, 128]),
    'numbers': format_color([100, 150, 190]),
}


class Highlighter(QtGui.QSyntaxHighlighter):

    keywords = [
        'and',
        'assert',
        'break',
        'class',
        'continue',
        'def',
        'del',
        'elif',
        'else',
        'except',
        'exec',
        'finally',
        'for',
        'from',
        'global',
        'if',
        'import',
        'in',
        'is',
        'lambda',
        'not',
        'or',
        'pass',
        'print',
        'raise',
        'return',
        'try',
        'while',
        'yield',
        'None',
        'True',
        'False',
    ]
    operators = config_dict['syntax_highlight']['red']
    braces = []

    def __init__(self, document):
        super().__init__(document)
        self.tri_single = (QtCore.QRegExp("'''"), 1, styles['string2'])
        self.tri_double = (QtCore.QRegExp('"""'), 2, styles['string2'])

        rules = []

        rules += [(r'\b%s\b' % w, 0, styles['keyword'])
                  for w in Highlighter.keywords]
        rules += [(r'%s' % o, 0, styles['operator'])
                  for o in Highlighter.operators]
        rules += [(r'%s' % b, 0, styles['brace']) for b in Highlighter.braces]
        other_rules = [[(r'\b%s\b' % k, 0, format_color(i)) for k in j]
                       for i, j in config_dict['syntax_highlight'].items()
                       if i != 'red']
        for i in other_rules:
            rules += i
        rules += [
            (r'"[^"\\]*(\\.[^"\\]*)*"', 0, styles['string']),
            (r"'[^'\\]*(\\.[^'\\]*)*'", 0, styles['string']),
            (r'\bdef\b\s*(\w+)', 1, styles['defclass']),
            (r'\bclass\b\s*(\w+)', 1, styles['defclass']),
            (r'#[^\n]*', 0, styles['comment']),
            (r'\b[+-]?[0-9]+[lL]?\b', 0, styles['numbers']),
            (r'\b[+-]?0[xX][0-9A-Fa-f]+[lL]?\b', 0, styles['numbers']),
            (r'\b[+-]?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\b', 0,
             styles['numbers']),
        ]
        self.rules = [(QtCore.QRegExp(pat), index, fmt)
                      for (pat, index, fmt) in rules]

    def highlightBlock(self, text):
        for expression, nth, format in self.rules:
            index = expression.indexIn(text, 0)

            while index >= 0:
                index = expression.pos(nth)
                length = len(expression.cap(nth))
                self.setFormat(index, length, format)
                index = expression.indexIn(text, index + length)

        self.setCurrentBlockState(0)
        in_multiline = self.match_multiline(text, *self.tri_single)
        if not in_multiline:
            in_multiline = self.match_multiline(text, *self.tri_double)

    def match_multiline(self, text, delimiter, in_state, style):
        if self.previousBlockState() == in_state:
            start = 0
            add = 0
        else:
            start = delimiter.indexIn(text)
            add = delimiter.matchedLength()
        while start >= 0:
            end = delimiter.indexIn(text, start + add)
            if end >= add:
                length = end - start + add + delimiter.matchedLength()
                self.setCurrentBlockState(0)
            else:
                self.setCurrentBlockState(in_state)
                length = len(text) - start + add
            self.setFormat(start, length, style)
            start = delimiter.indexIn(text, start + length)

        if self.currentBlockState() == in_state:
            return True
        else:
            return False


class ask_save_window(QtWidgets.QMainWindow):

    def __init__(self, dpi=None):
        super().__init__()
        self.setStyleSheet(current_editor.get_stylesheet())
        self.setWindowTitle('Save File')
        self.setMinimumSize(600, 200)
        self.dpi = dpi
        self.font_type = config_dict['font_type']
        self.font_size = config_dict['font_size']
        self.current_font = set_font(
            QtGui.QFont(self.font_type, self.font_size), self.dpi)
        self.ask_save_label = self.get_label(text=current_language_dict[
            'The file has changed, do you want to save the changes?'])
        self.ask_save_label.move(0, 30)
        self.save_button = self.get_button(
            text=current_language_dict['Save'],
            command=current_editor.save_and_quit)
        self.not_save_button = self.get_button(
            text=current_language_dict['Discard'],
            command=current_editor.destroy_and_quit)
        self.cancel_button = self.get_button(
            text=current_language_dict['Cancel'], command=self.close)
        self.save_button.move(0, 100)
        self.not_save_button.move(120, 100)
        self.cancel_button.move(300, 100)
        self.show()

    def get_button(self, command=None, **kwargs):
        current_button = QtWidgets.QPushButton(self, **kwargs)
        if command is not None:
            current_button.clicked.connect(command)
        current_button.setFont(self.current_font)
        current_button.adjustSize()
        current_button.setStyleSheet(
            f'background-color: {config_dict["button_background_color"]}')
        return current_button

    def get_label(self, **kwargs):
        current_label = QtWidgets.QLabel(self, **kwargs)
        current_label.setFont(self.current_font)
        current_label.adjustSize()
        return current_label


class Editor(QtWidgets.QMainWindow):

    def __init__(self, dpi=None):
        super().__init__()
        self.setMinimumSize(1200, 750)
        self.setWindowTitle(f'Musicpy {current_language_dict["Editor"]}')
        self.dpi = dpi
        self.get_config_dict = copy(config_dict)
        self.get_config_dict = {
            i: str(j)
            for i, j in self.get_config_dict.items()
        }
        self.font_type = config_dict['font_type']
        self.font_size = config_dict['font_size']
        self.editor_area_font_size = config_dict['editor_area_font_size']
        self.current_font = set_font(
            QtGui.QFont(self.font_type, self.font_size), self.dpi)
        self.current_editor_area_font = set_font(
            QtGui.QFont(self.font_type, self.editor_area_font_size), self.dpi)
        self.inputs_text = self.get_label(
            text=current_language_dict['Input musicpy codes here'])
        self.inputs_text.move(0, 80)
        self.custom_actions = [
            self.get_action(text=current_language_dict['Play Selected Code'],
                            command=self.play_select_text,
                            shortcut='Ctrl+B'),
            self.get_action(
                text=current_language_dict['Play Selected Code Visually'],
                command=self.visualize_play_select_text,
                shortcut='Ctrl+G'),
            self.get_action(text=current_language_dict['Import MIDI File'],
                            command=self.read_midi_file,
                            shortcut='Ctrl+D'),
            self.get_action(text=current_language_dict['Stop Playing'],
                            command=self.stop_play_midi,
                            shortcut='Ctrl+E'),
            self.get_action(text=current_language_dict['Search'],
                            command=self.search_words,
                            shortcut='Ctrl+F')
        ]
        self.inputs = CustomTextEdit(
            self,
            pairing_symbols=config_dict['pairing_symbols'],
            custom_actions=self.custom_actions,
            size=(700, 200),
            font=self.current_editor_area_font,
            place=(0, 110))
        self.inputs.addActions(self.custom_actions)
        self.outputs_text = self.get_label(
            text=current_language_dict['Output'])
        self.outputs = QtWidgets.QPlainTextEdit(self)
        self.outputs.setFont(self.current_editor_area_font)
        self.outputs_text.move(0, 350)
        self.outputs.setFixedSize(700, 300)
        self.outputs.move(0, 380)
        self.is_realtime = True
        self.quit = False
        self.is_syntax = True
        self.highlight = Highlighter(
            self.inputs.document() if self.is_syntax else None)
        self.pairing_symbols = config_dict['pairing_symbols']
        self.is_print = True
        self.pre_input = ''
        self.changed = False
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
        self.file_menu.addAction(self.custom_actions[2])
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
        self.settings_menu = self.menu_bar.addMenu(
            current_language_dict['Settings'])
        self.syntax_action = self.get_action(
            text=current_language_dict['Syntax Highlight'],
            command=self.check_syntax,
            checkable=True,
            initial_value=True)
        self.settings_menu.addAction(self.syntax_action)
        self.print_action = self.get_action(
            text=current_language_dict["Don't use print"],
            command=self.check_print,
            checkable=True,
            initial_value=True)
        self.settings_menu.addAction(self.print_action)
        self.realtime_action = self.get_action(
            text=current_language_dict["Real Time"],
            command=self.check_realtime,
            checkable=True,
            initial_value=True)
        self.settings_menu.addAction(self.realtime_action)
        self.last_save = self.inputs.toPlainText()
        self.current_filename_path = None
        self.inputs.textChanged.connect(self.input_changed)
        self.bg_mode = config_dict['background_mode']
        self.change_background_color_mode(turn=False)
        self.background_action = self.get_action(
            text=current_language_dict['Light'],
            command=lambda: self.change_background_color_mode(turn=True),
            checkable=True,
            initial_value=True)
        self.settings_menu.addAction(self.background_action)
        self.addAction(
            self.get_action(command=self.close_window, shortcut='Ctrl+Q'))

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
        self.ask_save_window = None
        self.visualize_process = None

        self.setStyleSheet(self.get_stylesheet())

        self.show()

    def get_stylesheet(self):
        font_size = self.current_font.pointSize()
        font_type = self.font_type
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
        font-size: {font_size}pt;
        font-family: {font_type};
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
        font-size: {font_size}pt;
        font-family: {font_type};
        }}
        QMenu {{
        background-color: {config_dict["background_color"]};
        color: {config_dict["foreground_color"]};
        font-size: {font_size}pt;
        font-family: {font_type};
        }}
        QMenu::item:selected {{
        background-color: {config_dict["active_background_color"]};
        color: {config_dict["active_foreground_color"]};
        }}
    '''
        return result

    def closeEvent(self, event):
        current_text = self.inputs.toPlainText()
        if current_text == self.last_save:
            event.accept()
        else:
            event.ignore()
            self.close_window()

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

    def get_action(self,
                   text='',
                   command=None,
                   icon=None,
                   shortcut=None,
                   checkable=False,
                   initial_value=False,
                   **kwargs):
        current_action = QtWidgets.QAction(
            QtGui.QIcon() if icon is None else QtGui.QIcon(icon), text, self,
            **kwargs)
        if command is not None:
            current_action.triggered.connect(command)
        if shortcut is not None:
            current_action.setShortcut(shortcut)
        if checkable:
            current_action.setCheckable(True)
            current_action.setChecked(initial_value)
        return current_action

    def close_window(self):
        if self.ask_save_window is not None and self.ask_save_window.isVisible(
        ):
            return
        self.ask_save_window = ask_save_window(dpi=self.dpi)
        self.ask_save_window.show()

    def save_and_quit(self):
        self.save_current_file()
        if self.current_filename_path:
            self.last_save = self.inputs.toPlainText()
            self.ask_save_window.close()
            self.close()
            os._exit(0)

    def destroy_and_quit(self):
        self.last_save = self.inputs.toPlainText()
        self.ask_save_window.close()
        self.close()
        os._exit(0)

    def editor_config(self):
        if self.current_config_window is not None and self.current_config_window.isVisible(
        ):
            self.current_config_window.activateWindow()
            return
        else:
            self.current_config_window = config_window(dpi=self.dpi,
                                                       config_path=config_path,
                                                       parent=self)
            self.current_config_window.setStyleSheet(self.get_stylesheet())

    def visualize_config(self):
        if self.current_visual_config_window is not None and self.current_visual_config_window.isVisible(
        ):
            self.current_visual_config_window.activateWindow()
            return
        else:
            self.current_visual_config_window = config_window(
                dpi=self.dpi, config_path=piano_config_path)
            self.current_visual_config_window.setStyleSheet(
                self.get_stylesheet())

    def get_current_line_column(self):
        self.current_line_number = self.inputs.textCursor().blockNumber() + 1
        self.current_column_number = self.inputs.textCursor().columnNumber(
        ) + 1
        self.line_column.setText(
            f'Line {self.current_line_number} Col {self.current_column_number}'
        )

    def change_background_color_mode(self, turn=True):
        if turn:
            if self.bg_mode == 'black':
                self.bg_mode = 'white'
            else:
                self.bg_mode = 'black'
        if self.bg_mode == 'white':
            self.inputs.setStyleSheet("background-color: white; color: black")
            self.outputs.setStyleSheet("background-color: white; color: black")
        elif self.bg_mode == 'black':
            self.inputs.setStyleSheet("background-color: black; color: white")
            self.outputs.setStyleSheet("background-color: black; color: white")
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
        current_stylesheet = self.get_stylesheet()
        app.setStyleSheet(current_stylesheet)
        self.pairing_symbols = config_dict['pairing_symbols']
        if self.is_syntax:
            self.highlight = Highlighter(self.inputs.document())

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
        self.pre_input = self.inputs.toPlainText()
        self.runs()

    def check_realtime(self):
        value = self.realtime_action.isChecked()
        if value:
            self.is_realtime = True
        else:
            self.is_realtime = False
            self.quit = True

    def check_print(self):
        self.is_print = self.print_action.isChecked()

    def check_syntax(self):
        self.is_syntax = self.syntax_action.isChecked()
        self.highlight.setDocument(
            self.inputs.document() if self.is_syntax else None)

    def play_select_text(self):
        try:
            selected_text = self.inputs.textCursor().selectedText()
            exec(f"play({selected_text})")
        except:
            self.outputs.clear()
            self.outputs.insertPlainText(
                current_language_dict['The codes selected cannot be played'])

    def visualize_play_select_text(self):
        try:
            selected_text = self.inputs.textCursor().selectedText()
            exec(f"write({selected_text}, name='temp.mid')")
        except:
            self.outputs.clear()
            self.outputs.insertPlainText(
                current_language_dict['The codes selected cannot be played'])
            return
        if self.visualize_process is not None and self.visualize_process.is_alive(
        ):
            self.visualize_process.terminate()
        self.visualize_process = Process(target=visualize.start)
        self.visualize_process.daemon = True
        self.visualize_process.start()

    def read_midi_file(self):
        filename = Dialog(
            caption=current_language_dict["Choose MIDI File"],
            directory='',
            filter=
            f'{current_language_dict["MIDI File"]} (*.mid);;{current_language_dict["All files"]} (*)'
        ).filename[0]
        if filename:
            self.inputs.insertPlainText(
                f"new_midi_file = read(\"{filename}\")\n")

    def stop_play_midi(self):
        pygame.mixer.music.stop()

    def close_search_box(self):
        pass

    def search_words(self):
        pass

    def change_search_ind(self, ind):
        pass

    def search(self, *args):
        pass


if __name__ == '__main__':
    function_names = list(set(musicpy_vars))
    function_names.sort()
    app = QtWidgets.QApplication(sys.argv)
    dpi = (app.screens()[0]).logicalDotsPerInch()
    current_editor = Editor(dpi=dpi)
    app.exec()
