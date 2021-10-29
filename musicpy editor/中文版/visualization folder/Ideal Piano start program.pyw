import pygame
import pygame.midi
import keyboard
import time
import pyglet
import mido
import midiutil
from tkinter import *
from tkinter import ttk
from tkinter import filedialog

abs_path = os.path.dirname(os.path.abspath(__file__))

if 'visualization folder' not in abs_path:
    abs_path += '/visualization folder'

if 'visualization folder' not in abs_path:
    abs_path += '/visualization folder'

with open('config.py', encoding='utf-8-sig') as f:
    exec(f.read(), globals(), globals())

with open('browse.py', encoding='utf-8-sig') as f:
    exec(f.read(), globals(), globals())

with open('Ideal Piano.pyw', encoding='utf-8-sig') as f:
    exec(f.read(), globals(), globals())
