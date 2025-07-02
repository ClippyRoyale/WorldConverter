'''
MR World Converter
Version 3.4.6

Copyright © 2022–2025 ClippyRoyale

LICENSE INFO:
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program (see the file license.txt).
    If not, see <https://www.gnu.org/licenses/>.

CHANGELOG: See changelog.txt
'''

import codecs
import json
import os
import sys
import webbrowser
import urllib.error
import urllib.request
from collections import abc
from glob import glob
from time import time
from typing import *
from tkinter import *
import tkinter.font as tkfont
from tkinter import filedialog # not imported with tkinter by default
from tkinter import messagebox # not imported with tkinter by default

#### BEGIN UI SETUP ####

VERSION = '3.4.6'

window = Tk()
window.wm_title('Clippy’s World Converter')
window.geometry('480x360')
window.resizable(False, False)
# Run in fullscreen on Replit only
if os.path.isdir("/home/runner"):
    window.attributes('-fullscreen', True)

app_icon = PhotoImage(file='ui/iconHD.png')
window.iconphoto(False, app_icon)

colors = {
    'red': '#ff0000',
    'green': '#008000',
    'blue': '#0000ff',
    'gray': '#808080',
    'silver': '#c0c0c0',
    # Background color is baby blue to distinguish this app from Skin Converter
    'BG': '#e0f0ff',
}

def relative_font_size(multiple:Union[int,float]):
    '''
    Different platforms use different default font sizes.
    Get this system's default size to use as a base.
    All other font sizes will be a multiple of it.
    '''
    base_font_size = tkfont.Font(font='TkDefaultFont').cget('size')
    return int(multiple * base_font_size)

f_italic = tkfont.Font(slant='italic', size=relative_font_size(1))
f_bold = tkfont.Font(weight='bold', size=relative_font_size(1))
f_large = tkfont.Font(size=relative_font_size(1.5))
f_heading = tkfont.Font(weight='bold', size=relative_font_size(1.5))

footer_frame = LabelFrame(window, width=480, height=40, bg=colors['BG'])
footer = Label(footer_frame,
        text=f'World Converter v{VERSION} — a Clippy production',
        fg=colors['gray'], bg=colors['BG'])
back_btn = Button(footer_frame, text='Back to Menu',
        highlightbackground=colors['BG'])

main_frame = LabelFrame(window, width=480, height=320, bg=colors['BG'])
main_frame.grid_propagate(False)

menu_heading = Label(main_frame, text='Welcome to the MR World Converter',
        font=f_heading, bg=colors['BG'])
menu_subhead = Label(main_frame,
        text='Because those worlds aren’t gonna convert themselves',
        font=f_italic, bg=colors['BG'])

icons = {
    'info': \
        PhotoImage(file='ui/info.png'),
    'question': \
        PhotoImage(file='ui/question.png'),
    'warning': \
        PhotoImage(file='ui/warning.png'),
    'error': \
        PhotoImage(file='ui/denied.png'),
    'done': \
        PhotoImage(file='ui/accepted.png'),
}

# OTHER GLOBAL VARIABLES

warnings = ''

#### BEGIN UI FUNCTIONS ####

def cls():
    '''
    Clear the main content frame -- remove text, buttons, etc.
    '''
    for child in main_frame.winfo_children():
        child.place_forget()

def update_subhead(subhead:Label, current:int, target:int):
    '''
    Update the user on the progress of a large conversion task.
    '''
    rounded_pct = round(current/target*100, 1)

    subhead = Label(main_frame,
        text=f'Now converting file {current+1} of {target} ({rounded_pct}%)',
        justify='left', bg=colors['BG'])
    subhead.place(x=0, y=36)

    return subhead

def button_dialog(title:str, message:Union[str, List[str]],
                  buttons:Tuple[str, ...]=('Cancel', 'Okay'), *,
                  icon:Optional[str]=None):
    '''
    Displays a dialog box with one or more buttons to the user. Holds until the
    user clicks a button. Returns the name of the button clicked.

    icon is one of: info, question, warning, error, done, bomb
    '''

    cls()

    button_clicked = None
    # Nested function that all button event bindings point to
    # Sets the button_clicked variable one layer up so the function knows
    # it can return
    def button_event(index:int):
        nonlocal button_clicked
        button_clicked = buttons[index]

    dialog_icon = None
    if icon in icons:
        dialog_icon = Label(main_frame, image=icons[icon], bg=colors['BG'])
        dialog_icon.place(x=470, y=10, anchor=NE)

    next_y = 0
    if title:
        dialog_title = Label(main_frame, text=str(title), font=f_heading,
                justify='left', bg=colors['BG'])
        dialog_title.place(x=0, y=0)
        # If there’s title text, leave space so msg_text doesn't cover it up
        next_y = 30

    dialog_message = []
    # Failsafe in case message is in an invalid format
    if not isinstance(message, list) and not isinstance(message, str):
        message = str(message)
    # Convert to list if message is only one line / a string
    if isinstance(message, str):
        message = [message]

    for index, item in enumerate(message):
        dialog_message.append(Label(main_frame, text=item, justify='left',
                wraplength=470, bg=colors['BG']))

        # Apply styling as needed
        if item.startswith('<b>'):
            dialog_message[-1].config(font=f_bold,
                                      text=item[3:]) # strip <b> tag
        elif item.startswith('<i>'):
            dialog_message[-1].config(font=f_italic,
                                      text=item[3:]) # strip <i> tag

        # Shorten wrapping if dialog box has icon, so text doesn’t cover it
        if icon and next_y < 100:
            dialog_message[-1].config(wraplength=380)

        dialog_message[index].place(x=0, y=next_y)
        next_y += dialog_message[-1].winfo_reqheight() + 4

    # Reworked dialogs don't support bottom text
    # (it adds unnecessary complexity).

    button_objs = []
    for index, item in enumerate(buttons):
        # Create new button object
        new_btn = Button(main_frame, text=item,
                highlightbackground=colors['BG'],
                command=lambda c=index: button_event(c))
        # Add to button obj list
        button_objs.append(new_btn)

    # Place buttons one by one on the frame, aligned right and starting with
    # the rightmost button
    next_button_x = 470
    for i in reversed(button_objs):
        i.place(x=next_button_x, y=310, anchor=SE)
        next_button_x -= i.winfo_reqwidth()
        next_button_x -= 10 # a little extra space between buttons

    # Wait for user to click a button
    while button_clicked is None:
        window.update()
    # Once we get here, a button has been clicked, so return the button's name
    return button_clicked

def bool_dialog(title:str, message:Union[str, List[str]],
                  button1='Cancel', button2='Okay', *,
                  icon:Optional[str]=None):
    '''
    Simplified version of button_dialog() that only allows 2 buttons and returns
    a boolean value. If the user clicks the right/Okay button, return True.
    Otherwise, if the user clicks the left/Cancel button, return False.
    '''
    button_name = button_dialog(title, message, (button1, button2), icon=icon)
    if button_name == button2:
        return True
    else:
        return False

def yn_dialog(title:str, message:Union[str, List[str]],
                  button1='Yes', button2='No', *, icon:Optional[str]=None):
    '''
    yn_dialog is like bool_dialog but the buttons' return values are reversed.
    The left/Yes button returns True, and the right/No button returns false.
    '''
    button_name = button_dialog(title, message, (button1, button2), icon=icon)
    if button_name == button1:
        return True
    else:
        return False

def simple_dialog(title:str, message:Union[str, List[str]],
                  button='Okay', *, icon:Optional[str]=None):
    '''
    Single-button dialog. Returns None.
    '''
    button_dialog(title, message, (button,), icon=icon)

#### END UI CODE ####

# Compatibility constants (see below)
DELUXE  = 0b10000
LEGACY  = 0b01000
REMAKE  = 0b00100
CLASSIC = 0b00010 # listed as "cross-platform" in menu
# "Inferno" is an available setting but it's currently unused.
# Basically it would be treated as Classic with fewer tiles/objects.
INFERNO = 0b00001

AUTODETECT = 0b00000 # Only for convert_from

# OBJECT DATABASE
# Format:
# (name, compatibility, deluxe_id, legacy_id)
# id of -1 means the tile doesn't exist in that version.
#
# compatibility is a binary number with bits in format <dlrci>, where:
# - i for InfernoPlus (1.0.0 - 2.1.0),
#   last common ancestor of Deluxe + all others
# - c for Classic (by Igor & Cyuubi; 2.1.1 - 3.7.0),
#   last common ancestor of Remake and Legacy
# - r for Remake (by GoNow; no version numbers),
#   new codebase but mostly backwards-compatible with Classic levels
# - l for Legacy (by Terminal & Casini Loogi; 3.7.1 - 5.2.0)
# - d for Deluxe (by Terminal & Casini Loogi)
# EXAMPLES:
# - 0b11011 means it's compatible with everything but Remake
# - Semisolid at ID 6 is only compatible with Deluxe (0b10000) because it had a
#   different ID in Classic, Legacy, and Remake
ObjDbEntry = Tuple[str, int, int, int]
OBJ_DATABASE : Tuple[ObjDbEntry, ...] = (
    ('player',                  0b11111,1,  1),

    ('goombrat',                0b11000,16, 16),
    ('goomba',                  0b11111,17, 17),
    ('green koopa troopa',      0b11111,18, 18),
    ('red koopa troopa',        0b11111,19, 19),
    ('koopa shell',             0b01000,-1, 20),
    ('flying fish',             0b11111,21, 21),
    ('piranha plant',           0b11111,22, 22),
    ('spiny',                   0b11000,23, 23),
    ('buzzy beetle',            0b11000,24, 24),
    ('bowser',                  0b11111,25, 25),
    ('dry bones',               0b01000,-1, 26),

    ('made-up rabbit enemy',    0b01000,-1, 30),
    ('boo',                     0b01000,-1, 31),
    ('rotodisc',                0b01000,-1, 32),
    ('fire bar',                0b11111,33, 33),
    ('lava bubble',             0b11111,34, 34),
    ('bill blaster',            0b11111,35, 35),
    ('bullet bill',             0b11111,36, 36),
    ('object spawner',          0b11110,37, 37),
    ('banzai blaster',          0b01000,-1, 38),
    ('banzai bill',             0b01000,-1, 39),
    ('rex',                     0b10000,40, 40),
    ('cheep cheep',             0b11000,38, 41),
    ('thwomp',                  0b01000,-1, 42),
    ('tweeter',                 0b01000,-1, 43),
    ('icicle',                  0b01000,-1, 44),
    ('fuzzy',                   0b01000,-1, 45),

    ('hammer bro',              0b11111,49, 49),
    ('fire bro',                0b11000,50, 50),

    ('mushroom',                0b11111,81, 81),
    ('fire flower',             0b11111,82, 82),
    ('1up',                     0b11111,83, 83),
    ('star',                    0b11111,84, 84),
    ('axe',                     0b11111,85, 85),
    ('poison mushroom',         0b11111,86, 86),
    ('checkpoint',              0b01000,-1, 87),

    ('coin',                    0b11111,97, 97),

    ('gold flower',             0b01000,-1, 100),
        # in Remake editor but unused in game

    ('door',                    0b01000,-1, 129),
    ('key',                     0b01000,-1, 130),

    ('platform',                0b11111,145,145),
    ('bus platform',            0b11111,146,146),
    ('path platform',           0b01000,-1, 147),

    ('spring',                  0b11111,149,149),

    ('fireball projectile',     0b11111,161,161),
    ('fire breath projectile',  0b11111,162,162),
    ('hammer projectile',       0b11111,163,163),

    ('flag',                    0b11111,177,177),
    ('goalpost',                0b11000,178,178), # from SMW

    ('cheep cheep spawner',     0b01000,-1, 193),
    ('environment prop',        0b01000,-1, 200),

    ('text',                    0b11111,253,253),
    ('checkmark',               0b11111,254,254),

    # Deluxe only:
    ('blooper',                 0b10000,39, -1),
    ('leaf',                    0b10000,87, -1),
    ('hammer suit',             0b10000,88, -1),
)
UNKNOWN_OBJ = ('UNKNOWN', 0b00000, -1, -1)
    # generic entry for unknown object, e.g. if an invalid ID is removed
removed_objects = [] # Object IDs removed from the world will go here

# Misc. global variables
convert_fail = False

convert_from = IntVar()
convert_from.set(AUTODETECT)

convert_to = IntVar()
convert_to.set(DELUXE)

# Whether to convert standard item boxes (that contain a mushroom or flower)
# to progressive item boxes
use_prog = IntVar()

# TILE DATABASE
# Format: (tile_name, version_support, deluxe_id, legacy_id, remake_id,
#           (fallback1, fallback2, ...))
# id of -1 means the tile doesn't exist in that version.
# Fallback can be 0 (air), 1 (solid), or a valid tile_name.
# If possible, make the last fallback supported in all versions.
# If a version doesn't support any fallback, default to air.
TileDbEntry = Tuple[str, int, int, int, int, tuple]
TILE_DATABASE : Tuple[TileDbEntry, ...] = (
    # The program expects index 0 to be Air and index 1 to be Solid Standard.
    # All other indices do not have a guaranteed definition.
    ('air', 0b11111, 0, 0, 0, (0,)),
    ('solid standard', 0b11111, 1, 1, 1, (0,)),

    # Supported in all versions
    ('solid bumpable', 0b11111, 2, 2, 2, (0,)),
    ('solid breakable', 0b11111, 3, 3, 3, (0,)),
    ('item block', 0b11111, 17, 17, 17, (0,)),
    ('coin block', 0b11111, 18, 18, 18, (0,)),
    ('coin block multi', 0b11111, 19, 19, 19, (0,)),
    ('item block invisible', 0b11111, 21, 21, 21, (0,)),
    ('coin block invisible', 0b11111, 22, 22, 22, (0,)),
    ('vine block', 0b11111, 24, 24, 24, (0,)),
    ('warp tile', 0b11111, 81, 81, 81, (0,)),
    ('warp pipe down slow', 0b11111, 82, 82, 82, (0,)),
    ('warp pipe right slow', 0b11111, 83, 83, 83, (0,)),
    ('warp pipe down fast', 0b11111, 84, 84, 84, (0,)),
    ('warp pipe right fast', 0b11111, 85, 85, 85, (0,)),
    ('level end warp', 0b11111, 86, 86, 86, (0,)),
    ('flagpole', 0b11111, 160, 160, 160, (0,)),
    ('vine', 0b11111, 165, 165, 165, (0,)),
    ('vote block', 0b11111, 240, 240, 240, (0,)),

    # Added in Cyuubi builds (common ancestor of Remake and Legacy)
    # (sorted by Legacy ID)
    ('solid damage', 0b11110, 4, 4, 4, (1,)),
    ('semisolid', 0b11110, 6, 5, 5, (1,)),
    ('semisolid weak', 0b01110, -1, 6, 6, (0,)),
    ('water surface', 0b01110, -1, 8, 8, ('water', 0,)), # pushes you down
    ('water current', 0b01110, -1, 9, 9, ('water', 0,)), # pushes you left/right
    ('water', 0b11110, 7, 7, 7, (0,)),
    ('item block infinite', 0b11110, 25, 25, 25, (0,)),

    # Added in Remake (sorted by Remake ID)
    ('solid ice', 0b11100, 10, 10, 10, (1,)),
    ('note block', 0b11100, 11, 11, 11, (1,)),
        # ^ called "pop block" in Remake but works the same
    ('conveyor', 0b00100, -1, -1, 12, (1,)),
        # ^ in Deluxe but as 2 different tiles

    # Added in Legacy 4.x (sorted by Legacy ID)
    ('item note block', 0b11000, 12, 12, -1, ('note block', 'item block',)),
    ('ice -> tile', 0b01000, -1, 13, -1, ('ice -> object', 'solid ice', 1,)),
    ('flip block', 0b11000, 8, 14, -1, ('solid breakable',)),
    ('air damage', 0b11000, 5, 15, -1, ('solid damage', 0,)),
    ('ice -> object', 0b11000, 13, 16, -1, ('solid ice', 1,)),
    ('item block progressive', 0b11000, 20, 20, -1, ('item block',)),
    ('semisolid ice', 0b01000, -1, 23, -1, ('semisolid', 1,)),
    ('item block invisible progressive', 0b11000, 27, 26, -1,
        ('item block invisible',)),
    ('scroll lock x', 0b11000, 30, 30, -1, (0,)),
    ('scroll unlock x', 0b11000, 31, 31, -1, (0,)),
    ('checkpoint', 0b01000, -1, 40, -1, (0,)),
    ('warp pipe single slow', 0b11000, 93, 87, -1, (1,)),
    ('warp pipe single fast', 0b11000, 94, 88, -1, (1,)),
    ('warp pipe left slow', 0b11000, 89, 89, -1, (1,)),
    ('warp pipe left fast', 0b11000, 90, 90, -1, (1,)),
    ('warp pipe up slow', 0b11000, 91, 91, -1, (1,)),
    ('warp pipe up fast', 0b11000, 92, 92, -1, (1,)),
    ('flagpole level end warp', 0b01000, -1, 161, -1, ('level end warp',)),

    # ONLY in Deluxe (sorted by Deluxe ID)
    ('conveyor left', 0b10000, 14, -1, -1, ('conveyor', 1,)),
    ('conveyor right', 0b10000, 15, -1, -1, ('conveyor', 1,)),
    ('item block regen', 0b10000, 26, -1, -1,
        ('item block infinite', 'item block',)),
    ('warp tile relative', 0b10000, 80, -1, -1, (0,)),
        # ^ not compatible with td32
    ('warp tile random', 0b10000, 87, -1, -1, (0,)),
    ('message block', 0b10000, 241, -1, -1, (1,)),
    ('sound block', 0b10000, 239, -1, -1, (0,)),

    # Added in Legacy 5.x and later (sorted by Legacy ID)
    ('half tile bumpable', 0b01000, -1, 27, -1, ('solid bumpable',)),
    ('half tile solid', 0b01000, -1, 28, -1, (1,)),
    ('half tile semisolid', 0b01000, -1, 29, -1, ('semisolid', 1,)),
    ('scroll lock y', 0b01000, -1, 32, -1, (0,)),
    ('scroll unlock y', 0b01000, -1, 33, -1, (0,)),
    ('scroll lock x/y', 0b01000, -1, 34, -1, (0,)),
    ('scroll unlock x/y', 0b01000, -1, 35, -1, (0,)),
    ('player barrier', 0b11000, 9, 36, -1, (1,)),
    ('enemy barrier', 0b01000, -1, 37, -1, (0,)),
)

# List of tuple(str, str) with any incompatible tiles that got replaced
replacement_list = []

# Build lookups for obj database based on L/D tile IDs
# KEY: the object's ID in L/D
# VALUE: the tuple index of the object's database entry
# Loading this from a file would be faster but also less secure
deluxe_obj_lookup : Dict[int, int] = {}
for i_index, i_item in enumerate(OBJ_DATABASE):
    obj_id = i_item[2]
    if obj_id >= 0: # negative ID = obj doesn't exist in this version
        deluxe_obj_lookup[obj_id] = i_index
legacy_obj_lookup : Dict[int, int] = {}
for i_index, i_item in enumerate(OBJ_DATABASE):
    obj_id = i_item[3]
    if obj_id >= 0: # negative ID = obj doesn't exist in this version
        legacy_obj_lookup[obj_id] = i_index
# Unlike tile lookups, there's no remake ID because that's the same as legacy

# Build lookups for tile database based on R/L/D tile IDs
# KEY: the tile's ID in R/L/D
# VALUE: the tuple index of the tile's database entry
# Loading this from a file would be faster but also less secure
deluxe_tile_lookup : Dict[int, int] = {}
for i_index, i_item in enumerate(TILE_DATABASE):
    tile_id = i_item[2]
    if tile_id >= 0: # negative ID = tile doesn't exist in this version
        deluxe_tile_lookup[tile_id] = i_index
legacy_tile_lookup : Dict[int, int] = {}
for i_index, i_item in enumerate(TILE_DATABASE):
    tile_id = i_item[3]
    if tile_id >= 0: # negative ID = tile doesn't exist in this version
        legacy_tile_lookup[tile_id] = i_index
remake_tile_lookup : Dict[int, int] = {}
for i_index, i_item in enumerate(TILE_DATABASE):
    tile_id = i_item[4]
    if tile_id >= 0:
        remake_tile_lookup[tile_id] = i_index

def get_obj_by_name(name:str) -> Optional[Tuple[str, int, int, int]]:
    '''
    Given an obj's standard string name as it appears in the above database,
    return that obj's database entry.
    '''
    for i in OBJ_DATABASE:
        if i[0] == name:
            return i
    # If name doesn't exist in database, return None
    return None

def get_obj_id_for_version(obj:Tuple[str, int, int, int]) -> int:
    '''
    Given an obj database entry, return the correct obj ID int for the game
    version set in the global variable convert_to
    '''
    if convert_to.get() == DELUXE:
        new_id = obj[2]
    else: # legacy/remake/classic/inferno
        new_id = obj[3]
    return new_id

def get_tile_by_name(name:str) -> TileDbEntry:
    '''
    Given a tile's standard string name as it appears in the above database,
    return that tile's database entry.
    '''
    for i in TILE_DATABASE:
        if i[0] == name:
            return i
    # If name doesn't exist in database, return air
    return TILE_DATABASE[0]

def get_tile_id_for_version(tile:TileDbEntry) -> int:
    '''
    Given a tile database entry, return the correct tile data int for the game
    version set in the global variable convert_to
    '''
    if convert_to.get() == DELUXE:
        new_id = tile[2]
    elif convert_to.get() == REMAKE:
        new_id = tile[4]
    else: # legacy/classic/inferno
        new_id = tile[3]
    return new_id

def convert_tile(old_td:list) -> Union[list, int]:
    '''
    Convert a tile from one version to another, including any ID changes and
    replacements of incompatible tiles.
    Takes in an int[5] list, i.e. the Deluxe tile format.
    Returns the new tile in the target version's format.
    '''
    # Deluxe TD format:
    # 0. sprite index (keep)
    # 1. bump state (keep)
    # 2. depth (keep)
    # 3. tile data (change)
    # 4. extra data (keep except in special cases)
    new_td = old_td.copy()

    # Get data of the tile that the old ID refers to
    if convert_from.get() == DELUXE:
        try:
            db_entry = TILE_DATABASE[deluxe_tile_lookup[old_td[3]]]
        except KeyError:
            # If tile ID is invalid, turn it into air
            db_entry = TILE_DATABASE[0]
    elif convert_from.get() == REMAKE:
        try:
            db_entry = TILE_DATABASE[remake_tile_lookup[old_td[3]]]
        except KeyError:
            # If tile ID is invalid, turn it into air
            db_entry = TILE_DATABASE[0]
    else: # legacy/classic/inferno
        try:
            db_entry = TILE_DATABASE[legacy_tile_lookup[old_td[3]]]
        except KeyError:
            # If tile ID is invalid, turn it into air
            db_entry = TILE_DATABASE[0]

    # Find that tile's new ID
    new_td[3] = get_tile_id_for_version(db_entry)

    # If converting to L/D, use progressive item blocks where appropriate
    if convert_to.get() & (LEGACY|DELUXE) and use_prog.get() \
            and old_td[4] in (81, 82): # mushroom, flower
        if db_entry[0] == 'item block':
            new_td[3] = 20 # progressive item block ID in both Legacy & Deluxe
        if db_entry[0] == 'item block invisible':
            new_td[3] = 27 if convert_to.get()==DELUXE else 26

    # If tile not compatible with target version, follow fallback chain
    if not (db_entry[1] & convert_to.get()):
        replacement = ('error', 'error')

        for i in db_entry[5]: # tuple of possible fallback tiles
            if i == 0 or i == 1:
                # In the database, 0 and 1 are accepted shorthands for
                # air and solid, respectively -- for convenience
                fallback_id = i
                fallback_entry = TILE_DATABASE[i]
            else:
                fallback_entry = get_tile_by_name(i)
                fallback_id = get_tile_id_for_version(fallback_entry)

            # If the fallback tile is compatible with the target version:
            if fallback_entry[1] & convert_to.get():
                new_td[3] = fallback_id

                # Get data for fallback tile to add to log
                # (may be changed by special cases below)
                replacement = (db_entry[0], fallback_entry[0])

                # BEGIN SPECIAL CASES (mostly for extra data)

                # Convert conveyors from Remake to Deluxe format
                if db_entry[0] == 'conveyor' and convert_to.get() == DELUXE:
                    if old_td[4] < 128:
                        new_td[3] = 14 # Conveyor left
                        replacement = (db_entry[0], 'conveyor left')
                    elif old_td[4] > 128:
                        new_td[3] = 15 # Conveyor right
                        replacement = (db_entry[0], 'conveyor right')
                    else: # Remake conveyor speed = 0
                        new_td[3] = 1 # Solid standard

                # Convert conveyors from Deluxe to Remake format
                # Make the custom Remake speed about the same as
                # the only Deluxe speed
                if db_entry[0] == 'conveyor left' and \
                        convert_to.get() == REMAKE:
                    new_td[4] = 124
                if db_entry[0] == 'conveyor right' and \
                        convert_to.get() == REMAKE:
                    new_td[4] = 132

                # Make former progressive item blocks
                # always spit out a mushroom
                if 'progressive' in db_entry[0]:
                    new_td[4] = 81 # mushroom

                # turn ice -> tile blocks into ice -> object blocks
                # that turn into 0 object
                if 'ice -> tile' in db_entry[0]:
                    new_td[4] = 0

                # END SPECIAL CASES

                break
            # If fallback tile is NOT compatible with target
            # version, do another round of the loop

        # When loop is done, leave note that tile was replaced
        if replacement not in replacement_list:
            replacement_list.append(replacement)

    # End fallback code

    if convert_to.get() == DELUXE:
        # If we're converting to Deluxe,
        # we're already using the right tile format
        return new_td
    else:
        # If we're converting to an older version,
        # return the tile in td32 format
        return new_td[0] + new_td[1]*(2**11) + new_td[2]*(2**15) + \
                new_td[3]*(2**16) + new_td[4]*(2**24)

def web_file_exists(path:str):
    '''
    Test if an image file exists on the web.
    Return True if the specified string is a valid URL.
    Return False if attempting to visit the URL returns an HTTP error.
    Return None if GoNow forgot to renew his TLS certificate again.
    '''
    try:
        # Assign to throwaway variable, just call to check for error
        _ = urllib.request.urlopen(path).status
        return True
    except AttributeError:
        # If using Python 3.8.x or earlier, use `code` instead of `status`
        # Assign to throwaway variable, just call to check for error
        _ = urllib.request.urlopen(path).code
        return True
    except urllib.error.HTTPError:
        # If the path leads to a 404, or the server is down
        return False
    except urllib.error.URLError:
        # If Remake's certificate expired AGAIN. (URLError could also mean
        # "no internet", but that case is handled elsewhere.)
        return None

def extract_tile(tile:abc.Sequence):
    '''
    Given a tile of unknown format, return
    the tile normalized to a list of 5 ints
    '''
    global warnings

    # Start with an empty tile
    extracted_tile = [30,0,0,0,0]

    try:
        if isinstance(tile, list):
            # Deluxe: list-based format
            # ValueError = not an int (e.g. extra data in relative warp tiles)
            # IndexError = out of range (e.g. if tile data is just [30])
            try:
                extracted_tile[0] = int(tile[0])
            except (ValueError, IndexError):
                extracted_tile[0] = 30 # empty sprite
            try:
                extracted_tile[1] = int(tile[1])
            except (ValueError, IndexError):
                extracted_tile[1] = 0
            try:
                extracted_tile[2] = int(tile[2])
            except (ValueError, IndexError):
                extracted_tile[2] = 0
            try:
                extracted_tile[3] = int(tile[3])
            except (ValueError, IndexError):
                extracted_tile[3] = 0
            try:
                extracted_tile[4] = int(tile[4])
            except (ValueError, IndexError):
                extracted_tile[4] = 0
        elif isinstance(tile, int):
            # Legacy and earlier: td32
            extracted_tile[0] = tile % 2**11 # sprite: 11-bit
            extracted_tile[1] = tile // 2**11 % 2**4 # bump state: 4-bit
            extracted_tile[2] = tile // 2**15 % 2 # depth: 1-bit
            extracted_tile[3] = tile // 2**16 % 2**8 # definition: 8-bit
            extracted_tile[4] = tile // 2**24 % 2**8 # extra data: 8-bit
        # Else, it's a format we just don't recognize at all, so we stick to
        # the default extracted_tile
    except Exception:
        warnings += f'Failed to convert tile: {tile}\n'

    return extracted_tile

def absolute_path(version: int, rel_path: str):
    '''
    Given a relative path, convert to an absolute URL path
    '''
    if version == DELUXE:
        return 'https://raw.githubusercontent.com/mroyale/assets-dx/main/' + \
                rel_path
    elif version == REMAKE:
        return 'https://mroyale.net/' + rel_path
    else: # LEGACY
        return 'https://raw.githubusercontent.com/mroyale/assets/legacy/' + \
                rel_path

def is_abs_path(url: str):
    return (url.startswith('http://') or \
            url.startswith('https://') or \
            url.startswith('//'))

def convert(open_path: str, save_path: str):
    '''
    Convert 1 world file from Legacy TO DELUXE, and return string
    containing all converter warnings
    '''
    global convert_fail, warnings
    convert_fail = False # Wipe away previous failed conversions
    warnings = '' # Reset warnings

    if open_path == save_path:
        convert_fail = True
        error_msg = f'For your safety, this program does not allow you to \
overwrite your existing world files. \
Please try a different file path.\n{open_path}\n'
        return error_msg

    try:
        # Open and read the old world file
        read_file = codecs.open(open_path, 'r', 'utf-8-sig')
        content = json.load(read_file)
        read_file.close()
    except FileNotFoundError:
        # Not sure if we can get here now that the GUI handles file opening,
        # but this can't hurt
        convert_fail = True
        error_msg = f'The selected file does not exist.\n{open_path}\n'
        return error_msg
    except IsADirectoryError:
        convert_fail = True
        error_msg = f'The selected file is a folder.\n{open_path}\n'
        return error_msg
    except UnicodeDecodeError:
        # File is an image, movie, or other binary
        convert_fail = True
        error_msg = f'The selected file is a binary file such as an image, \
song, or movie, and could not be read.\n{open_path}\n'
        return error_msg
    except json.decoder.JSONDecodeError:
        # File is not JSON
        convert_fail = True
        error_msg = f'''The selected text file could not be read.
Are you sure it’s a world?\n{open_path}\n'''
        return error_msg

    # Create a file at the save path if it doesn't already exist.
    # No overwriting yet because if the user is saving over an existing level
    # and the program crashes, we don't want the user to lose previous progress
    try:
        open(save_path, 'a', encoding='utf-8').close()
    except PermissionError:
        # If user tries to save to a folder they don't have write access to
        convert_fail = True
        error_msg = f'Your computer blocked World Converter from saving to \
the selected folder: \n{save_path}\n'
        return error_msg

    try:
        # Might as well check for layers now,
        # so we don't have to do it over and over again
        if 'layers' in content['world'][0]['zone'][0]:
            has_layers = True
        else:
            has_layers = False

        # Auto-detect version of source file if necessary
        # Why is this a while loop when I only want to run it once?
        # Because Python doesn't have goto
        while convert_from.get() == AUTODETECT:
            # Test for Deluxe format by checking if tiles are lists
            if has_layers:
                dx_check = isinstance(content['world'][0]['zone'][0]['layers']\
                        [0]['data'][0][0], list)
            else:
                dx_check = isinstance(content['world'][0]['zone'][0]\
                        ['data'][0][0], list)
            if dx_check:
                convert_from.set(DELUXE)
                break

            # Remake-exclusive World attributes
            if 'vertical' in content or 'autoMove' in content:
                convert_from.set(REMAKE)
                break

            # Legacy-exclusive World attributes
            if 'group' in content or 'longname' in content:
                convert_from.set(LEGACY)
                break

            # Try to detect version based on map availability
            # (if we have internet)
            for index, item in enumerate(content['resource']):
                # Expand relative map paths to the correct full URL,
                # based on the version selected/detected earlier.
                # First of all, only do this if it *is* a relative path, because
                # if it's already a full URL, then we shouldn't have any issues
                if item['id'] == 'map' and not is_abs_path(item['src']):
                    try:
                        # Basic internet connection test
                        urllib.request.urlopen('http://google.com')
                        # If this causes an error, there's a 99% chance you're
                        # not connected to the internet

                        # First try Legacy URL
                        legacy_url = absolute_path(LEGACY, item['src'])
                        exists_in_legacy = web_file_exists(legacy_url)
                        if exists_in_legacy is True:
                            convert_from.set(LEGACY)
                        elif exists_in_legacy is None:
                            convert_from.set(LEGACY)
                            warnings += \
'Security warning on Legacy map image.\n'
                        else:
                            # If it's not in Legacy, fall back to Remake URL
                            remake_url = absolute_path(REMAKE, item['src'])
                            exists_in_remake = web_file_exists(remake_url)
                            if exists_in_remake is True:
                                convert_from.set(REMAKE)
                            elif exists_in_remake is None:
                                convert_from.set(REMAKE)
                                warnings += \
'Security warning on Remake map image, what a surprise.\n'
                            # If it's not in Legacy or Remake, give up
                            else:
                                warnings += \
f'Couldn’t find the map sheet {open_path.split(os.sep)[-1]} in Legacy or \
Remake. Defaulting to Legacy for the world version.\n'
                    except urllib.error.HTTPError:
                        # If test page 404s, fall through to the "detect
                        # everything else as Legacy" code
                        warnings += 'No internet connection! Version \
detection will be less accurate.\n'
                    except urllib.error.URLError:
                        # If no internet, fall through to the "detect
                        # everything else as Legacy" code
                        warnings += 'No internet connection! Version \
detection will be less accurate.\n'
                    finally:
                        pass
                    # Since we've found the map sheet, we don't need to
                    # keep looping anymore
                    break

            # Remake-exclusive feature check #1:
            # Fire bars have 4 params in Remake, and 3 in Legacy
            for level_i, level in enumerate(content['world']): # Loop thru lvls
                for zone_i, zone in enumerate(level['zone']): # Loop thru zones
                    for obj_i, obj in enumerate(zone['obj']): # Loop thru objs
                        if obj['type'] == 33: # fire bar
                            if len(obj['param']) == 4:
                                convert_from.set(REMAKE)

            # Remake-exclusive feature check #2: conveyors
            for level_i, level in enumerate(content['world']): # Loop thru lvls
                for zone_i, zone in enumerate(level['zone']): # Loop thru zones
                    if has_layers:
                        for layer_i, layer in enumerate(zone['layers']):
                                                        # Loop thru layers
                            for row_i, row in enumerate(layer['data']):
                                                            # Loop thru rows
                                for tile_i, tile in enumerate(row):
                                                            # Loop tiles by col
                                    test_tile = extract_tile(tile)
                                    # Check for conveyor tile (see below)
                                    if test_tile[3] == 12 \
                                            and test_tile[4] >= 112 \
                                            and test_tile[4] < 144:
                                        convert_from.set(REMAKE)
                    else:
                        for row_i, row in enumerate(zone['data']):
                                                        # Loop thru rows
                            for tile_i, tile in enumerate(row):
                                                        # Loop tiles by col
                                test_tile = extract_tile(tile)
                                # Check for conveyor tile (ID 12 in Remake).
                                # In Legacy, ID 12 = Item Note Block, so we also
                                # make sure Extra Data has a reasonable speed
                                # value that ISN'T a valid object ID.
                                if test_tile[3] == 12 and test_tile[4] >= 112 \
                                        and test_tile[4] < 144:
                                    convert_from.set(REMAKE)

            # Treat everything else as Legacy because it has more tile options
            # and it's harder to detect from file contents
            # This could make conveyors get misconverted, but they only show
            # up in 2 known worlds (Royale City and Stiz 1)
            if convert_from.get() == AUTODETECT:
                warnings += 'Failed to definitively detect world version; \
defaulting to Legacy. Please check to make sure this is correct.\n'
                convert_from.set(LEGACY)
            else:
                warnings += \
                    f'World version detected as {game_ver_str(convert_from)}\n'
            break

        # Vertical (really free-roam) scrolling is set zone-by-zone in L/D
        vertical_world = False
        if convert_from.get() == REMAKE and 'vertical' in content:
            if content['vertical'] == 'true':
                vertical_world = True
            del content['vertical']
        # If ANY zone in a Deluxe or Legacy world is set to
        # Vertical or Free-Roam camera, make the whole world vertical in Remake
        if convert_from.get() & (DELUXE|LEGACY) \
                and convert_to.get() == REMAKE:
            # Yup, we gotta loop thru EVERY world, level, and zone
            for level_i, level in enumerate(content['world']):
                for zone_i, zone in enumerate(level['zone']):
                    # If world was vertical, add free-roam camera to each zone
                    if zone['camera'] != 0:
                        vertical_world = True
                        break
                if vertical_world: # Second break after detecting vertical
                    break
            # If we detected a vertical zone at any point in the loop,
            # add the vertical flag to the world
            content['vertical'] = 'true'

        if convert_to.get() == DELUXE:
            # Add extra effects sprite sheet that's not in Legacy or Remake
            content['resource'].append({"id":"effects",
                    "src":"img/game/smb_effects.png"})

            # Add audio override so Legacy worlds play their original music/SFX
            # if convert_from.get() == REMAKE:
            #     content["audioOverrideURL"] = absolute_path(REMAKE,'audio/')
            if convert_from.get() & (LEGACY|CLASSIC|INFERNO):
                content["audioOverrideURL"] = absolute_path(LEGACY, 'audio/')

            # Remove effects sheet that's only in Deluxe
            for index, dict_ in enumerate(content['resource']):
                if dict_['id'] == 'effects':
                    del content['resource'][index]

        if convert_to.get() & (DELUXE|INFERNO):
            # Delete world data that isn't in Deluxe
            if 'shortname' in content:
                del content['shortname']
            if 'longname' in content:
                del content['longname']
            if 'autoMove' in content:
                del content['autoMove']
            if 'musicOverridePath' in content:
                del content['musicOverridePath']
            if 'soundOverridePath' in content:
                del content['soundOverridePath']
            # NOTE: This is only necessary because the Java (Inferno/Deluxe)
            # server rejects any world with a parameter it doesn't recognize,
            # while the Python (Classic/Legacy) server simply ignores unknown
            # parameters. (The Remake server also ignores them.)

        if convert_to.get() & (LEGACY|REMAKE|CLASSIC):
            # Add shortname to make world pass validation in
            # Classic and Legacy. For Remake, it's just useful as a watermark.
            if 'shortname' not in content:
                content['shortname'] = '[WC]'
            # longname isn't *necessary* anywhere, but again, watermark
            if 'longname' not in content:
                content['longname'] = \
                    f"Converted with Clippy's World Converter (v{VERSION})"
            if 'mode' not in content:
                content['mode'] = 'royale'
            # Legacy music overrides only work with relative paths,
            # not full URLs, so we can't play music in Legacy yet

        # Turn lobbies into regular worlds so they don't crash the game
        content['type'] = 'game'
        # Any valid level should have a type, so no existence check needed.
        # If the level is missing a type, it will throw a KeyError, which will
        # make the program say the level is corrupted

        # Add full URL for Legacy assets when converting to Deluxe
        if convert_to.get() == DELUXE:
            if convert_from.get() == LEGACY and 'assets' in content:
                if not is_abs_path(content['assets']):
                    content['assets'] = absolute_path(LEGACY,
                                                  "assets/"+content['assets'])
            # If the world doesn't specify assets (i.e. Classic & Remake),
            # use Legacy assets because they're a superset of Classic/Remake's
            # hardcoded animations
            else:
                content['assets'] = absolute_path(LEGACY,
                        'assets/assets.json')
        # Similar situation but for Deluxe->Legacy assets
        elif convert_from.get() == DELUXE and convert_to.get() == LEGACY:
            if 'assets' in content:
                if not is_abs_path(content['assets']):
                    content['assets'] = absolute_path(DELUXE,
                                                  "assets/"+content['assets'])
            else:
                # Deluxe worlds won't use the Legacy animations
                content['assets'] = absolute_path(DELUXE,
                        'assets/assets-noanim.json')
        # DX->R assets will just be wrong and there's nothing I can do about it

        # Convert map & obj sheets
        for index, item in enumerate(content['resource']):
            # Expand relative map paths to the correct full URL,
            # based on the version selected/detected earlier.
            # First of all, only do this if it *is* a relative path, because
            # if it's already a full URL, then we shouldn't have any issues
            if item['id'] == 'map' and not is_abs_path(item['src']):
                if convert_from.get() == DELUXE:
                    dx_url = absolute_path(DELUXE, item['src'])
                    content['resource'][index]['src'] = dx_url
                elif convert_from.get() == REMAKE:
                    remake_url = absolute_path(REMAKE, item['src'])
                    content['resource'][index]['src'] = remake_url
                else: # legacy
                    legacy_url = absolute_path(LEGACY, item['src'])
                    content['resource'][index]['src'] = legacy_url

            # Either convert obj URL from relative to absolute, or if conversion
            # involves Deluxe, change the obj to a set default because Deluxe
            # uses a different obj sheet layout from other versions
            if item['id'] == 'obj':
                # Converting from Any to Deluxe: Switch to Deluxe default obj
                if convert_to.get() == DELUXE:
                    content['resource'][index]['src'] = absolute_path(DELUXE,
                            'img/game/smb_obj.png')
                # Converting from Deluxe to Any: Switch to Legacy's SMAS obj
                elif convert_from.get() == DELUXE:
                    content['resource'][index]['src'] = absolute_path(LEGACY,
                            'img/game/smas_obj.png')
                # Don't need a special case for Legacy->Remake because Legacy
                # obj is a superset of Remake's
                # If the conversion doesn't involve Deluxe but it uses a
                # relative path
                elif not is_abs_path(item['src']):
                    # Converting from Remake to Legacy: Expand obj sheet URL
                    # to absolute path on Remake domain
                    if convert_from.get() == REMAKE:
                        content['resource'][index]['src'] = \
                                absolute_path(REMAKE, item['src'])
                    # Converting from Legacy to Remake: Expand obj sheet URL
                    # to absolute path on Legacy domain
                    else:
                        legacy_url = \
                        content['resource'][index]['src'] = \
                                absolute_path(LEGACY, item['src'])
                # Else (i.e. if the conversion doesn't involve Deluxe and it
                # already uses an absolute path), leave it

        for level_i, level in enumerate(content['world']): # Loop thru levels
            for zone_i, zone in enumerate(level['zone']): # Loop thru zones
                # Calculate zone height (for flagpole placement and
                # per-zone vertical setting)
                if has_layers:
                    zone_height = len(zone['layers'][0]['data'])
                else:
                    zone_height = len(zone['data'])
                # Calculate zone width (for background looping)
                zone_width = 0
                if convert_from.get() == DELUXE:
                    if has_layers:
                        zone_width = len(zone['layers'][0]['data'][0])
                    else:
                        zone_width = len(zone['data'][0])

                if convert_to.get() == DELUXE:
                    # Delete world data that isn't in Deluxe because it
                    # doesn't like extra parameters
                    if 'winmusic' in content['world'][level_i]['zone'][zone_i]:
                        del content['world'][level_i]['zone'][zone_i]\
                                ['winmusic']
                    if 'victorymusic' in \
                                content['world'][level_i]['zone'][zone_i]:
                        del content['world'][level_i]['zone'][zone_i]\
                                ['victorymusic']
                    if 'levelendoff' in \
                                content['world'][level_i]['zone'][zone_i]:
                        del content['world'][level_i]['zone'][zone_i]\
                                ['levelendoff']

                    # If world was vertical in Remake, add free-roam camera
                    # to each zone in Deluxe if zone is above height limit 14
                    if vertical_world and zone_height > 14:
                        content['world'][level_i]['zone'][zone_i]['camera'] = 2
                elif convert_to.get() == LEGACY:
                    # If world was vertical in Remake, add free-roam camera
                    # to each zone in Legacy if zone is above height limit 16
                    if vertical_world and zone_height > 16:
                        content['world'][level_i]['zone'][zone_i]['camera'] = 2

                # Fix background image URLs in Deluxe worlds
                if convert_from.get() == DELUXE and 'background' in zone:
                    for i in zone['background']:
                        dx_url = absolute_path(DELUXE, i['url'])
                        i['url'] = dx_url
                        # Legacy doesn't yet support infinite bg looping,
                        # so we need to calculate it from zone width + speed.
                        # Assume bg image width is ≥128px (the lowest width
                        # found in Deluxe's assets). In most cases our estimate
                        # will be too high, but that should be fine because
                        # there's background culling
                        if i['loop'] <= 0:
                            i['loop'] = (zone_width // 8) + 1

                # Adjust position of left warp exits
                # Remake and Legacy have a bug where you need to place a warp
                # three tiles right of the pipe if you want the player to exit
                # in the right place. Deluxe fixed this bug, so we need to
                # shift any left warps in the zone
                for warp in zone['warp']:
                    # Replace no-offset warps if converting to anything other
                    # than Deluxe or Legacy
                    if convert_to.get() < LEGACY:
                        if warp['data'] == 5:
                            warp['data'] = 1
                        elif warp['data'] == 6:
                            warp['data'] = 2
                    if warp['data'] == 3:
                        if convert_to.get() == DELUXE:
                            if warp['pos'] % 65536 >= 3:
                                # Shift 3 left to "correct" position
                                # (though it's still 1 tile left of
                                # what I'd expect)
                                warp['pos'] -= 3
                            else:
                                # If warp is all the way at the left for some
                                # reason, clip its x tile to 0
                                warp['pos'] -= (warp['pos'] % 65536)
                        elif convert_from.get() == DELUXE:
                            # Shift 3 right to "incorrect" position
                            # Note that warps CAN be placed outside the zone
                            # as long as they're to the RIGHT
                            warp['pos'] += 3

                flagpole_pos = None
                # Two different conversion options based on if level has layers
                if has_layers:
                    # Loop thru the layers
                    for layer_i, layer in enumerate(zone['layers']):
                        # Loop thru the rows
                        for row_i, row in enumerate(layer['data']):
                            # Loop thru tiles by column
                            for tile_i, tile in enumerate(row):
                                # Convert the tile to a 5-element list
                                # (Deluxe tile format) regardless of its
                                # original format
                                old_tile = extract_tile(tile)

                                # Overwrite the old tiledata with the new
                                # tile in the appropriate format
                                # (list or td32, depending on game version)
                                content['world'][level_i]['zone'][zone_i]\
                                        ['layers'][layer_i]['data']\
                                        [row_i][tile_i] = \
                                    convert_tile(old_tile)

                                # WATER HITBOX WORKAROUND for conv. TO DELUXE
                                #   (see extended notes in no-layers section)
                                # Make sure we’re not in top row
                                if convert_to.get() == DELUXE and \
                                        (old_tile[3] == 7 or \
                                         old_tile[3] == 8 or \
                                         old_tile[3] == 9) and row_i >= 1:
                                    # Get data for the tile 1 row up
                                    above_tile = content['world'][level_i]\
                                            ['zone'][zone_i]['layers'][layer_i]\
                                            ['data'][row_i-1][tile_i]
                                    # If td-1 is air, change it to water
                                    if (above_tile[3] == 0):
                                        above_tile[3] = 7

                                # FLAGPOLE CHECK
                                # See no-layer section for notes
                                if convert_from.get() != DELUXE \
                                        and flagpole_pos is None \
                                        and (old_tile[3] == 161):
                                    flagpole_pos = (tile_i, row_i) # (x, y)
                else:
                    for row_i, row in enumerate(zone['data']): # Loop thru rows
                        for tile_i, tile in enumerate(row): # Loop tiles by col
                            # Convert the tile to a 5-element list
                            # (Deluxe tile format) regardless of its
                            # original format
                            old_tile = extract_tile(tile)

                            # Overwrite the old tiledata with the new
                            # tile in the appropriate format
                            # (list or td32, depending on game version)
                            content['world'][level_i]['zone'][zone_i]['data']\
                                    [row_i][tile_i] = \
                                convert_tile(old_tile)

                            # WATER HITBOX WORKAROUND
                            # The water hitboxes in Legacy (and probably Remake)
                            # are infamously bad—they’re about a tile too tall.
                            # Deluxe fixes them, but it means we have to change
                            # old worlds built with these hitboxes in mind.
                            # This will work because the row(s) above already
                            # have their “final” data (in list format).
                            # Make sure we’re not in top row
                            if convert_to.get() == DELUXE and \
                                    (old_tile[3] == 7 or old_tile[3] == 8 or \
                                    old_tile[3] == 9) and row_i >= 1:
                                # Get data for the tile 1 row up/same col
                                above_tile = content['world'][level_i]\
                                        ['zone'][zone_i]['data'][row_i-1]\
                                        [tile_i]
                                # If td-1 is air, change it to water
                                if (above_tile[3] == 0):
                                    above_tile[3] = 7

                            # FLAGPOLE CHECK
                            # Check if this zone has a flagpole. If it does,
                            # then check later if it has a flag object.
                            # If it doesn't, add one at the top of the pole.
                            # This is needed because Remake doesn't use the
                            # flag object, but all other versions require
                            # a flag object if the zone has a flagpole.
                            if flagpole_pos is None \
                                    and (old_tile[3] == 161):
                                # Log the highest position with a flagpole
                                # tile, so we can place a flag object there
                                # if necessary
                                flagpole_pos = (tile_i, row_i) # (x, y) coord
                                # Note that the tile array does the top row
                                # first, while int-based coordinates use the
                                # bottom row first.

                # Check for unsupported objects and remove them
                # Need to use a while loop because length of obj list may
                # change while program runs
                obj_i = 0 # START
                has_flag = False
                while True:
                    # STOP
                    if obj_i >= len(zone['obj']):
                        break

                    # Object is incompatible if it's either:
                    #   - Not in the list of all objects
                    #   - In the list but not flagged as supported in
                    #     the target version
                    # This data is collected differently based on which
                    # object lookup table we need to use
                    in_obj_db : bool
                    obj_entry : Optional[Tuple[str,int,int,int]] = None
                    if convert_from.get() == DELUXE:
                        in_obj_db = zone['obj'][obj_i]['type'] \
                                in deluxe_obj_lookup
                        if in_obj_db:
                            obj_entry = OBJ_DATABASE[deluxe_obj_lookup[
                                zone['obj'][obj_i]['type']
                            ]]
                    else:
                        in_obj_db = zone['obj'][obj_i]['type'] \
                                in legacy_obj_lookup
                        if in_obj_db:
                            obj_entry = OBJ_DATABASE[legacy_obj_lookup[
                                zone['obj'][obj_i]['type']
                            ]]
                    # This part below is the same regardless of version/lookup
                    if not in_obj_db or not obj_entry or \
                            not (obj_entry[1] & convert_to.get()):
                        # Log the removed object if it's not already in the
                        # removed objects list
                        if zone['obj'][obj_i]['type'] not in removed_objects:
                            removed_objects.append(zone['obj'][obj_i]['type'])
                        # Actually remove the object from the world
                        # Must do AFTER logging to avoid out-of-range errors
                        del content['world'][level_i]['zone'][zone_i]\
                                ['obj'][obj_i]
                        # Reduce the loop variable to account for the removal
                        obj_i -= 1

                    # Remake<->Legacy fire bar conversion
                    # Deluxe only has 2 params (phase & length), like Classic
                    if obj_entry and obj_entry[0] == 'fire bar':
                        if convert_from.get() == REMAKE \
                                and convert_to.get() == LEGACY:
                            # Remake firebar params:
                            # [phase, length, clockwise, speed_mult]
                            old_param = zone['obj'][obj_i]['param']

                            if len(old_param) == 2: # clockwise
                                old_param.append(0)
                                # fallthrough
                            if len(old_param) == 3: # speed_mult
                                old_param.append(1)
                            # len(old_param) is now at least 4

                            # The game doesn't care if params are int or str,
                            # but Python does
                            try:
                                old_param[0] = int(old_param[0])
                            except (ValueError, TypeError):
                                # Default value if a param is invalid or blank
                                old_param[0] = 0 # phase
                            try:
                                old_param[1] = int(old_param[1])
                            except (ValueError, TypeError):
                                # Default value if a param is invalid or blank
                                old_param[1] = 6 # length
                            try:
                                old_param[2] = int(old_param[2])
                            except (ValueError, TypeError):
                                # Default value if a param is invalid or blank
                                old_param[2] = 0 # clockwise
                            try:
                                old_param[3] = float(old_param[3])
                            except (ValueError, TypeError):
                                # Default value if a param is invalid or blank
                                old_param[3] = 1.0 # speed_mult

                            cw = -1 if zone['obj'][obj_i]['param'][2] else 1
                            zone['obj'][obj_i]['param'] = [
                                old_param[0], old_param[1],
                                23//old_param[3]*cw
                            ]
                        elif convert_from.get() == LEGACY \
                                and convert_to.get() == REMAKE:
                            # Legacy firebar params:
                            # [phase, length, rate]
                            # Default rate is 23. Lower is faster.
                            old_param = zone['obj'][obj_i]['param']
                            if len(old_param) == 2: # rate
                                old_param.append(23)
                            # len(old_param) is now at least 4

                            # The game doesn't care if params are int or str,
                            # but Python does
                            try:
                                old_param[0] = int(old_param[0])
                            except (ValueError, TypeError):
                                # Default value if a param is invalid or blank
                                old_param[0] = 0 # phase
                            try:
                                old_param[1] = int(old_param[1])
                            except (ValueError, TypeError):
                                # Default value if a param is invalid or blank
                                old_param[1] = 6 # length
                            try:
                                old_param[2] = int(old_param[2])
                            except (ValueError, TypeError):
                                # Default value if a param is invalid or blank
                                old_param[2] = 23 # rate

                            zone['obj'][obj_i]['param'] = [
                                old_param[0], old_param[1],
                                0, 23/old_param[2] # decimals allowed here
                            ]
                            # Don't bother setting "clockwise" param
                            # because negating speed_mult does the same thing

                    # Deluxe<->Legacy cheep cheep conversion
                    # In Deluxe, the variant param is 0=green, 1=red
                    # In Legacy, the variant param is 0=red, 1=gray
                    if obj_entry and obj_entry[0] == 'cheep cheep' \
                            and convert_from.get() & (DELUXE|LEGACY) \
                            and convert_to.get() & (DELUXE|LEGACY) \
                            and convert_from.get() != convert_to.get():
                        # In both Legacy and Deluxe, the first param is the
                        # color variant, but in Legacy, 0=red and 1=gray,
                        # while in Deluxe, 0=green and 1=red.
                        # So we need to flip these
                        old_param = zone['obj'][obj_i]['param']
                        if len(old_param) >= 1:
                            try:
                                # Parse int
                                old_param[0] = int(old_param[0])
                                # Flip 0 to 1, and 1 to 0
                                old_param[0] = int(not bool(old_param[0]))
                            except (ValueError, TypeError):
                                # Default value if a param is invalid or blank
                                old_param[0] = 0 # variant

                    # FLAG CHECK
                    if obj_entry and obj_entry[0] == 'flag':
                        has_flag = True

                    # STEP
                    obj_i += 1

                # Now that we've left the loop, if we still don't have a flag,
                # add one at the position we found earlier
                if flagpole_pos is not None and not has_flag:
                    # Create object
                    new_flag_obj : Dict[str, Any] = {
                        'type': 177,
                        'pos': flagpole_pos[0] + \
                            (zone_height - 1 - flagpole_pos[1]) * (2**16),
                        'param': []
                    }
                    # Add object to JSON
                    zone['obj'].append(new_flag_obj)

#     except KeyError:
#         # File is missing required fields
#         convert_fail = True
#         error_msg = '''The selected file appears to be corrupted.
# Are you sure it’s a world?\n%s\n''' % open_path
#         return error_msg
    finally:
        pass

    # Open the file for real and wipe it
    write_file = open(save_path, 'w', encoding='utf-8')
    # Save the file's new contents
    json.dump(content, write_file, separators=(',',':'))
    # Close the file to prevent bugs that occur in large levels
    write_file.close()

    warnings += f'\nYOUR CONVERTED WORLD HAS BEEN SAVED TO:\n{save_path}\n\n'

    # Report the IDs of incompatible objects that were removed
    if removed_objects:
        warnings += 'Removed incompatible objects with the following IDs: '
        for index, item in enumerate(removed_objects):
            # Print the name of the incompatible object if available
            removed_obj_entry : Tuple[str, int, int, int]
            if convert_from.get() == DELUXE and item in deluxe_obj_lookup:
                removed_obj_entry = OBJ_DATABASE[
                    deluxe_obj_lookup[item]
                ]
            elif item in legacy_obj_lookup: # legacy/remake/etc
                removed_obj_entry = OBJ_DATABASE[
                    legacy_obj_lookup[item]
                ]
            else: # unknown/invalid object ID
                removed_obj_entry = UNKNOWN_OBJ
            warnings += f'{item} ({removed_obj_entry[0]})'
            # Add comma if we aren't at the end of the removed objects list
            if index < (len(removed_objects) - 1):
                warnings += ', '
        warnings += '\n'

    # Report the IDs of incompatible tiles that were replaced
    if replacement_list:
        for i in replacement_list:
            warnings += f'Incompatible tile definition “{i[0]}” \
replaced with “{i[1]}”\n'
    # Tiles that work the same but have different IDs across versions are
    # converted silently as of v3.0.0

    return warnings

def game_ver_str(v:IntVar):
    '''
    Given an IntVar (from convert_from or convert_to),
    return the string associated with that game version number
    (e.g. 'INFERNO' for v=1)
    '''
    i = v.get()
    if i == 0b10000:
        return 'DELUXE'
    elif i == 0b01000:
        return 'LEGACY'
    elif i == 0b00100:
        return 'REMAKE'
    elif i == 0b00010:
        return 'CLASSIC'
    elif i == 0b00001:
        return 'INFERNO'
    elif i == 0:
        return 'AUTODETECT'
    # else
    return 'UNKNOWN'

def convert_file():
    '''
    Ask user for a single file, then pass its path to the main
    convert() function
    '''
    open_path = filedialog.askopenfilename(
        title='Select a world file to convert',
        # filetypes=[('MR World JSON', '*.json *.txt *.game')],
        initialdir='./')
    # If script file path is still empty, user cancelled, back to menu
    if open_path == '':
        menu()
        return

    save_path = filedialog.asksaveasfilename(\
        title='Select a path to save to', defaultextension='.json',
        filetypes=[('MR World JSON', '*.json *.txt *.game')],
        initialdir='./')
    # If save_path is still empty, user cancelled, back to menu
    if save_path == '':
        menu()
        return

    # Start the conversion timer here!
    t1 = time()

    # Run main conversion function
    final_warnings = convert(open_path, save_path)

    # Stop the timer
    t2 = time()

    # Show off how fast my program is
    done_heading = f'Done in {round(t2-t1, 3)} seconds'
    # Overwrite done message if conversion failed
    if convert_fail:
        done_heading = 'Failed to convert world'

    # Tell the user the conversion is done
    simple_dialog(done_heading, final_warnings, 'Continue',
                  icon=('error' if convert_fail else 'done'))
    menu()

def convert_folder():
    '''
    Ask user to select a folder, then convert every file in that folder
    '''
    open_dir = filedialog.askdirectory(
        title='Select a folder. All worlds in the folder will be converted.',
        initialdir='./')
    # If script file path is still empty, user cancelled, back to menu
    if open_dir == '':
        menu()
        return

    # Start the conversion timer here!
    t1 = time()
    time_last_refresh = t1
    time_since_refresh = 0

    # Get list of files in the folder
    files = glob(open_dir + '/*')
    all_warnings = '' # distinct from global warnings because it doesn't reset
                      # for each file

    # Make a folder (inside the working directory)
    # to drop all the converted worlds in
    save_dir = './converted'
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    else:
        # If there's already a subfolder called _converted,
        # tack a number on the end
        i = 1
        # Keep trying numbers until we get a folder name
        # that doesn't exist yet
        while os.path.exists(save_dir + str(i)):
            i += 1
        # Now that we know it works, permanently add the number to save_dir
        save_dir += str(i)
        # Create the folder with the number that works
        os.makedirs(save_dir)

    # Set up progress updates
    heading = Label(main_frame, text=f'Converting {len(files)} files',
            font=f_heading, bg=colors['BG'])
    heading.place(x=0, y=0)
    subhead = Label()

    # Go thru each file in the selected folder and try to convert it
    for index, item in enumerate(files):
        # Update user on conversion progress.
        # Update only once per second so we don't slow things down too much
        # from updating the UI
        time_since_refresh += (time() - time_last_refresh)
        if time_since_refresh > 1:
            update_subhead(subhead, index, len(files))
            window.update()
            time_last_refresh = time()
            time_since_refresh = 0

        filename = item.split(os.sep)[-1] # Get just the filename w/o the path

        all_warnings += convert(item, save_dir + os.sep + filename) + '\n\n'

    # Save all warnings to a log file in the "converted" folder
    log_file = open(save_dir + '/_WARNINGS.LOG', 'a', encoding='utf-8')
    log_file.write(all_warnings)
    log_file.close()

    # Stop the timer
    t2 = time()

    # Show off how fast my program is
    done_heading = f'Done in {round(t2-t1, 3)} seconds'
    # No "Failed to convert" message for folder conversions
    # because we're not converting a single world

    # Tell the user the conversion is done
    simple_dialog(done_heading,
[f'All converted worlds have been saved to the folder with path “{save_dir}”.',
 'If there were any converter warnings, they have been logged to \
_WARNINGS.LOG.'], 'Continue', icon='done')
    menu()

def setup():
    #### INITIAL GUI SETUP ####
    # setup is a separate function from menu()
    # because we only need to do everything here once

    # Place frames
    main_frame.place(x=0, y=0)
    footer_frame.place(x=0, y=320)
    # Note that all object positions are RELATIVE to their parent frame

    # Place footer items
    footer.place(x=5, y=15, anchor=W)
    back_btn.place(x=470, y=15, anchor=E)
    back_btn.bind('<Button-1>', lambda _: menu())

    # Put window on top
    window.focus_force()
    # Display message of the day
    motd()
    # Show menu
    menu()

def menu():
    cls()

    # Reset convert_from and convert_to because they may be changed during the
    # conversion process
    convert_from.set(AUTODETECT)
    convert_to.set(DELUXE)

    menu_heading.place(x=240, y=0, anchor=N)
    menu_subhead.place(x=240, y=30, anchor=N)

    btn_run_single = Button(main_frame, text='Convert world',
            font=f_large, highlightbackground=colors['BG'],
            command=convert_file)
    btn_run_single.place(x=240, y=240, anchor=NE)

    btn_run_multi = Button(main_frame, text='Convert folder',
            font=f_large, highlightbackground=colors['BG'],
            command=convert_folder)
    btn_run_multi.place(x=240, y=240, anchor=NW)

    btn_help = Button(main_frame, text='Warnings',
            highlightbackground=colors['BG'],
            command=warnings_bugs)
    btn_help.place(x=240, y=280, anchor=NE)

    btn_exit = Button(main_frame, text='Exit',
                      highlightbackground=colors['BG'],
                      command=exit_app)
    btn_exit.place(x=240, y=280, anchor=NW)

    col1_header = Label(main_frame, text='Convert FROM:', font=f_bold,
                        bg=colors['BG'])
    col1_header.place(x=80, y=80)

    col1_options = [
        # Radiobutton(main_frame, text='InfernoPlus builds', bg=colors['BG'],
        #             variable=convert_from, value=INFERNO),
        # Radiobutton(main_frame, text='Cyuubi builds', bg=colors['BG'],
        #             variable=convert_from, value=CLASSIC),
        Radiobutton(main_frame, text='Remake', bg=colors['BG'],
                    variable=convert_from, value=REMAKE),
        Radiobutton(main_frame, text='Legacy', bg=colors['BG'],
                    variable=convert_from, value=LEGACY),
        Radiobutton(main_frame, text='Deluxe', bg=colors['BG'],
                    variable=convert_from, value=DELUXE),
        Radiobutton(main_frame, text='Auto-detect (default)', bg=colors['BG'],
                    variable=convert_from, value=AUTODETECT),
    ]
    for index, item in enumerate(col1_options):
        item.place(x=80, y=100+(20*index))

    col2_header = Label(main_frame, text='Convert TO:', font=f_bold,
                        bg=colors['BG'])
    col2_header.place(x=240, y=80)

    col2_options = [
        # Radiobutton(main_frame, text='InfernoPlus builds', bg=colors['BG'],
        #             variable=convert_to, value=INFERNO),
        Radiobutton(main_frame, text='Cross-platform (R+L)', bg=colors['BG'],
                    variable=convert_to, value=CLASSIC),
        Radiobutton(main_frame, text='Remake', bg=colors['BG'],
                    variable=convert_to, value=REMAKE),
        Radiobutton(main_frame, text='Legacy (default)', bg=colors['BG'],
                    variable=convert_to, value=LEGACY),
        Radiobutton(main_frame, text='Deluxe', bg=colors['BG'],
                    variable=convert_to, value=DELUXE),
    ]
    # Make Legacy the default option
    col2_options[2].select()
    for index, item in enumerate(col2_options):
        item.place(x=240, y=100+(20*index))

    # Checkbox options
    prog_option = Checkbutton(main_frame,
            text='Use progressive item boxes (Legacy/Deluxe only)',
            bg=colors['BG'], variable=use_prog)
    prog_option.select()
    prog_option.place(x=80, y=200)

    window.update_idletasks()

    window.mainloop()

def warnings_bugs():
    simple_dialog('WARNING - HEALTH AND SAFETY',
        [
            'This program is designed for use in private lobbies, or as a \
starting point for manual conversion. It is not designed to be used to put \
converted-but-otherwise-untouched levels into public rotation.',
            '<i>You may encounter the following issues with levels converted \
using this tool:',
            '''\
- Custom music may not load (except for Legacy->Deluxe conversions).
- For Legacy->Deluxe conversions, \
assets.json animations will play at 2× speed in Deluxe since Deluxe is \
60fps. Similarly, Deluxe->Legacy conversions will play animations at ½× speed.
- Worlds converted to/from Deluxe will use the target version’s object sheet \
(e.g. Legacy->Deluxe will use the default Deluxe obj).
- Vines may not render properly in worlds converted to/from Deluxe.'''
        ], icon='warning')
    menu()

def motd():
    '''
    Download and display the online Message of the Day.

    For each line, everything before the first space is the full list versions
    that should show the message. The rest of the line is the message itself.
    The program displays *up to 1* MOTD (the first that matches its version).

    EXAMPLE MOTD FORMAT:

    # This line is a comment and will be ignored.
    u_2.3.0 Deluxifier v3.0.0 is now available!^Click the "View Update" button \
        to open Github and download the update.
    # Use caret (^) for newlines.
    2.2.1_2.2.2 WARNING: Please update your program to 2.3.0 or later. \
        Your current version has a bug that could damage your files.
    * Chat was a mistake.

    This version of the program would display "Chat was a mistake."
    because it doesn't match any of the versions specified for the warnings.
    '''

    motd_url = 'https://raw.githubusercontent.com/ClippyRoyale/\
SkinConverter/main/motd.txt'
    try:
        # Download and read MOTD
        urllib.request.urlretrieve(motd_url, 'motd.txt')
        motd_file = open('motd.txt', encoding='utf-8')
        motd_lines = motd_file.read().splitlines()
        motd_data : List[List[str]] = []
        motd_file.close()
        for i in range(len(motd_lines)):
            # Split into version and message
            motd_data[i] = motd_lines[i].split(' ', 1)
            if (len(motd_lines[i]) >= 2) and \
                    ((VERSION in motd_data[i][0]) or \
                        (motd_data[i][0] == '*')):
                motd_text = motd_data[i][1].replace('^','\n')
                motd_header = 'News!'
                motd_buttons = ['Exit', 'Continue']
                # Add update button if MOTD is flagged as an update notice
                if 'u' in motd_data[i][0].lower():
                    motd_buttons.insert(0, 'View Update')
                    motd_header = 'Update available'

                motd_continue = button_dialog(motd_header, motd_text,
                                              tuple(motd_buttons))
                if motd_continue == 'Exit':
                    exit_app()
                elif motd_continue == 'View Update':
                    webbrowser.open('https://github.com/ClippyRoyale/\
SkinConverter/releases/latest')
                    exit_app()
                else: # Continue
                    return
    except Exception:
        # If the internet isn't cooperating or the MOTD file is malformed,
        # no big deal, just skip it
        pass

def crash(exctype=None, excvalue=None, _=None):
    try:
        bomb = PhotoImage(file='ui/bomb.gif')
        window.iconphoto(False, bomb)
    finally:
        # Tkinter doesn't have a "public" way to show the error dialog I want,
        # but the options are hidden under the hood.
        # Code based on Tkinter messagebox.py
        btn = messagebox._show('Error', f'''An error has occurred.
{str(exctype)[8:-2]}: {excvalue}''',
messagebox.ERROR, messagebox.ABORTRETRYIGNORE)
        # btn might be a Tcl index object, so convert it to a string
        btn = str(btn)
        if btn == 'abort':
            exit_app()
        elif btn == 'retry':
            setup()
        # else ignore

def exit_app():
    window.destroy()
    sys.exit()

#### MAIN PROGRAM START ####
try:
    # Comment out during development if you want crashes to be logged to the
    # console instead of displaying a bomb dialog
    window.report_callback_exception = crash

    # Determine if we're running on replit
    if os.path.isdir("/home/runner") is True:
        # Ask user to enter fullscreen
        messagebox.showinfo(message='''\
Looks like you’re running the online (Replit) version of the world converter!
You may want to enter fullscreen so you can click all the buttons.
Click the ⋮ on the “Output” menu bar then click “Maximize”.
If you’re on a phone, rotate it sideways, zoom out, \
and hide your browser’s toolbar.''')

        # show online instructions
        messagebox.showinfo(message='''Before converting your first file:
1. Create a Replit account. You can use an existing Google or GitHub account.
2. Click “Fork Repl” and follow the instructions.
3. In your newly-forked project, drag the world JSONs you want to convert \
into the list of files in the left sidebar.''')
        setup()
    else:
        setup()

except Exception as _:
    ei = sys.exc_info()
    crash(ei[0], ei[1])
