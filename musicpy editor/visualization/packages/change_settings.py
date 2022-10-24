from tkinter import *
from tkinter import ttk
from tkinter import filedialog
from ast import literal_eval
import os
from copy import deepcopy as copy
import json


def save_json(config, config_path, whole_config=None):
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config if not whole_config else whole_config,
                  f,
                  indent=4,
                  separators=(',', ': '),
                  ensure_ascii=False)


class settings_window(Tk):

    def __init__(self, config_path='', root=None):
        super(settings_window, self).__init__()
        self.config_path = config_path
        self.root = root
        self.whole_config = None
        self.current_config = self.whole_config
        self.current_path = []
        self.sort_mode = 0
        self.search_inds = 0
        self.search_inds_list = []

        self.title("Settings")
        self.minsize(800, 600)
        self.protocol("WM_DELETE_WINDOW", self.close_settings_box)
        self.config_options_bar = Scrollbar(self)
        self.config_options_bar.place(x=235, y=120, height=170, anchor=CENTER)
        self.choose_config_options = Listbox(
            self, yscrollcommand=self.config_options_bar.set)
        self.choose_config_options.bind(
            '<<ListboxSelect>>', lambda e: self.show_current_config_options())
        self.choose_config_options.place(x=0, y=30, width=220)
        self.config_options_bar.config(
            command=self.choose_config_options.yview)
        self.config_name = ttk.Label(self, text='')
        self.config_name.place(x=300, y=20)
        self.config_contents = Text(self,
                                    undo=True,
                                    autoseparators=True,
                                    maxundo=-1)
        self.config_contents.bind('<KeyRelease>',
                                  lambda e: self.config_change())
        self.config_contents.place(x=350, y=50, width=400, height=400)
        self.choose_filename_button = ttk.Button(self,
                                                 text='choose filename',
                                                 command=self.choose_filename)
        self.choose_directory_button = ttk.Button(
            self, text='choose directory', command=self.choose_directory)
        self.choose_filename_button.place(x=0, y=250)
        self.choose_directory_button.place(x=0, y=300)
        self.save = ttk.Button(self, text="save", command=self.save_current)
        self.save.place(x=0, y=400)
        self.saved_text = ttk.Label(self, text='saved')
        self.search_text = ttk.Label(self, text='search for config options')
        self.search_text.place(x=0, y=450)
        self.search_contents = StringVar(self)
        self.search_contents.trace_add('write', self.search)
        self.search_entry = Entry(self, textvariable=self.search_contents)
        self.search_entry.place(x=0, y=480)
        self.up_button = ttk.Button(
            self,
            text='Previous',
            command=lambda: self.change_search_inds(-1),
            width=8)
        self.down_button = ttk.Button(
            self,
            text='Next',
            command=lambda: self.change_search_inds(1),
            width=8)
        self.up_button.place(x=170, y=480)
        self.down_button.place(x=250, y=480)
        self.choose_bool1 = ttk.Button(
            self, text='True', command=lambda: self.insert_bool('True'))
        self.choose_bool2 = ttk.Button(
            self, text='False', command=lambda: self.insert_bool('False'))
        self.choose_bool1.place(x=135, y=250)
        self.choose_bool2.place(x=245, y=250)
        self.change_sort_button = ttk.Button(
            self, text="sort in order of appearance", command=self.change_sort)
        self.change_sort_button.place(x=150, y=400)
        self.reload_button = ttk.Button(self,
                                        text='Reload',
                                        command=self.reload)
        self.reload_button.place(x=350, y=480)

        if self.config_path:
            self.load_current_file()

    def load_current_file(self):
        if os.path.exists(self.config_path):
            with open(self.config_path, encoding='utf-8') as f:
                self.whole_config = json.load(f)
            self.current_config = self.whole_config
            self.current_config_original = copy(self.whole_config)
            self.current_config_keys = list(self.whole_config.keys())
            self.current_config_alpha_keys = list(
                sorted(self.current_config_keys, key=lambda s: s.lower()))
            self.options_num = len(self.whole_config)
            self.config_contents.delete('1.0', END)
            self.set_sort()

    def close_settings_box(self):
        try:
            self.root.open_settings = False
        except:
            pass
        self.destroy()

    def reload(self):
        try:
            self.root.destroy()
        except:
            pass
        self.destroy()
        os.startfile('easy sampler.exe')

    def change_sort(self):
        if self.current_config:
            if self.sort_mode == 0:
                self.sort_mode = 1
                self.change_sort_button.configure(
                    text='sort in order of appearance')
                self.choose_config_options.delete(0, END)
                for k, each in enumerate(self.current_config_keys):
                    self.choose_config_options.insert(k, each)
            else:
                self.sort_mode = 0
                self.change_sort_button.configure(
                    text='sort in alphabetical order')
                self.choose_config_options.delete(0, END)
                for k, each in enumerate(self.current_config_alpha_keys):
                    self.choose_config_options.insert(k, each)
            self.search()

    def set_sort(self):
        if self.current_config:
            if self.sort_mode == 1:
                self.change_sort_button.configure(
                    text='sort in order of appearance')
                self.choose_config_options.delete(0, END)
                for k, each in enumerate(self.current_config_keys):
                    self.choose_config_options.insert(k, each)
            else:
                self.change_sort_button.configure(
                    text='sort in alphabetical order')
                self.config_contents.delete('1.0', END)
                for k, each in enumerate(self.current_config_alpha_keys):
                    self.choose_config_options.insert(k, each)

    def insert_bool(self, content):
        self.config_contents.delete('1.0', END)
        self.config_contents.insert(END, content)
        self.config_change()

    def config_change(self):
        if self.current_config:
            try:
                current = literal_eval(
                    self.config_contents.get('1.0', 'end-1c'))
                current_config = self.choose_config_options.get(ANCHOR)
                self.current_config[current_config] = current
            except:
                pass

    def change_search_inds(self, num):
        self.search_inds += num
        if self.search_inds < 0:
            self.search_inds = 0
        if self.search_inds_list:
            search_num = len(self.search_inds_list)
            if self.search_inds >= search_num:
                self.search_inds = search_num - 1
            first = self.search_inds_list[self.search_inds]
            self.choose_config_options.selection_clear(0, END)
            self.choose_config_options.selection_set(first)
            self.choose_config_options.selection_anchor(first)
            self.choose_config_options.see(first)
            self.show_current_config_options()

    def search(self, *args):
        if self.current_config:
            current = self.search_contents.get()
            if not current:
                self.choose_config_options.selection_clear(0, END)
                return
            current_keys = self.current_config_keys if self.sort_mode == 1 else self.current_config_alpha_keys
            self.search_inds_list = [
                i for i in range(self.options_num)
                if current.lower() in current_keys[i].lower()
            ]
            if self.search_inds_list:
                self.search_inds = 0
                first = self.search_inds_list[self.search_inds]
                self.choose_config_options.selection_clear(0, END)
                self.choose_config_options.selection_set(first)
                self.choose_config_options.selection_anchor(first)
                self.choose_config_options.see(first)
                self.show_current_config_options()
            else:
                self.choose_config_options.selection_clear(0, END)

    def show_current_config_options(self):
        if self.current_config:
            current_config = self.choose_config_options.get(ANCHOR)
            self.config_name.configure(text=current_config)
            current_config_value = self.current_config[current_config]
            if type(current_config_value) == str:
                current_config_value = f"'{current_config_value}'"
            else:
                current_config_value = str(current_config_value)
            self.config_contents.delete('1.0', END)
            self.config_contents.insert(END, current_config_value)

    def choose_filename(self):
        filename = filedialog.askopenfilename(parent=self,
                                              title="choose filename",
                                              filetypes=(("all files", "*"), ))
        self.config_contents.delete('1.0', END)
        self.config_contents.insert(END, f"'{filename}'")
        self.config_change()

    def choose_directory(self):
        directory = filedialog.askdirectory(
            parent=self,
            title="choose directory",
        )
        self.config_contents.delete('1.0', END)
        self.config_contents.insert(END, f"'{directory}'")
        self.config_change()

    def show_saved(self):
        self.saved_text.place(x=140, y=350)
        self.after(1000, self.saved_text.place_forget)

    def save_current(self):
        if self.current_config:
            changed = False
            for each, current_value in self.current_config.items():
                before_value = self.current_config_original[each]
                if current_value != before_value:
                    save_json(self.current_config, self.config_path,
                              self.whole_config)
                    self.current_config_original[each] = current_value
                    changed = True
            if changed:
                self.show_saved()
                if self.current_path:
                    self.reload_current_file()
                    self.load_current_path()
