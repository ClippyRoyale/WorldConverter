'''
DELUXIFIER — A Python-based MRDX world converter
Version 3.2.0

Copyright © 2022–2023 clippy#4722

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

KNOWN BUGS: See warnings_bugs() in code for list
'''

import codecs, json, sys, os, webbrowser
import urllib.request
from typing import Union
from time import time
from glob import glob
from tkinter import *
import tkinter.font as tkfont
import tkinter.filedialog as filedialog
# PIP modules:
# This is probably TERRIBLE coding practice, but this is the easiest way to 
# make the program run "out of the box" for non-developers.
try:
    import requests
except ModuleNotFoundError:
    import os
    os.system('pip3 install requests')
try:
    import PIL.Image, PIL.ImageTk # pillow
except ModuleNotFoundError:
    import os
    os.system('pip3 install pillow')

#### BEGIN UI SETUP ####

VERSION = '3.2.0'

window = Tk()
window.wm_title('Deluxifier')
window.geometry('480x360')
window.resizable(False, False)
# Run in fullscreen on Replit only
if os.path.isdir("/home/runner") == True:
    window.attributes('-fullscreen', True)

app_icon = PhotoImage(file='ui/icon.png')
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

# Different platforms use different default font sizes.
# Get this system's default size to use as a base. 
# All other font sizes will be a multiple of it.
def relative_font_size(multiple):
    base_font_size = tkfont.Font(font='TkDefaultFont').cget('size')
    return int(multiple * base_font_size)

f_italic = tkfont.Font(slant='italic', size=relative_font_size(1))
f_bold = tkfont.Font(weight='bold', size=relative_font_size(1))
f_large = tkfont.Font(size=relative_font_size(1.5))
f_heading = tkfont.Font(weight='bold', size=relative_font_size(1.5))

footer_frame = LabelFrame(window, width=480, height=40, bg=colors['BG'])
footer = Label(footer_frame, 
        text='Deluxifier v%s — a Clippy production' % VERSION, 
        fg=colors['gray'], bg=colors['BG'])
back_btn = Button(footer_frame, text='Back to Menu', 
        highlightbackground=colors['BG'])

main_frame = LabelFrame(window, width=480, height=320, bg=colors['BG'])
main_frame.grid_propagate(False)

menu_heading = Label(main_frame, text='Welcome to Deluxifier', 
        font=f_heading, bg=colors['BG'])
menu_subhead = Label(main_frame, 
        text='The community-supported MR Deluxe world converter', 
        bg=colors['BG'])

icons = {
    'info': \
        PIL.ImageTk.PhotoImage(PIL.Image.open('ui/info.png')),
    'question': \
        PIL.ImageTk.PhotoImage(PIL.Image.open('ui/question.png')),
    'warning': \
        PIL.ImageTk.PhotoImage(PIL.Image.open('ui/warning.png')),
    'error': \
        PIL.ImageTk.PhotoImage(PIL.Image.open('ui/denied.png')),
    'done': \
        PIL.ImageTk.PhotoImage(PIL.Image.open('ui/accepted.png')),
}

#### BEGIN UI FUNCTIONS ####

# Clear the main content frame -- remove text, buttons, etc.
def cls():
    for child in main_frame.winfo_children():
        child.place_forget()

# Update the user on the progress of a large conversion task.
def update_subhead(subhead, current, target):

    rounded_pct = round(current/target*100, 1)

    subhead = Label(main_frame, 
            text='Now converting file %i of %i (%s%%)' % \
                    (current+1, target, rounded_pct), 
            justify='left', bg=colors['BG'])
    subhead.place(x=0, y=36)

    return subhead

# Displays a dialog box with one or more buttons to the user. Holds until the
# user clicks a button. Returns the name of the button clicked.
# icon is one of: info, question, warning, error, done, bomb
def button_dialog(title:str, message:Union[str, list],
                  buttons=['Cancel', 'Okay'], *, icon:str=None):
    cls()

    button_clicked = None
    # Local function that all button event bindings point to
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
        dialog_title = Label(main_frame, text=title, font=f_heading, 
                justify='left', bg=colors['BG'])
        dialog_title.place(x=0, y=0)
        # If there’s title text, leave space so msg_text doesn't cover it up
        next_y = 30

    dialog_message = []
    if isinstance(message, str): 
        # Convert to list if message is only one line / a string
        message = [message]

    for index, item in enumerate(message): # TODO: Scroll if not enough space
        dialog_message.append(Label(main_frame, text=item, justify='left', 
                wraplength=470, bg=colors['BG']))

        # Apply bold/italic styling as needed
        if item.startswith('<b>'):
            dialog_message[-1].config(font=f_bold, 
                                      text=item[3:]) # strip <b> tag
        if item.startswith('<i>'):
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
    while button_clicked == None:
        window.update()
    # Once we get here, a button has been clicked, so return the button's name
    return button_clicked

# Simplified version of button_dialog() that only allows 2 buttons and returns
# a boolean value. If the user clicks the right/Okay button, return True.
# Otherwise, if the user clicks the left/Cancel button, return False.
def bool_dialog(title:str, message:Union[str, list],
                  button1='Cancel', button2='Okay', *, icon:str=None):
    button_name = button_dialog(title, message, [button1, button2], icon=icon)
    if button_name == button2:
        return True
    else:
        return False
    
# yn_dialog is like bool_dialog but the buttons' return values are reversed.
# The left/Yes button returns True, and the right/No button returns false.
def yn_dialog(title:str, message:Union[str, list],
                  button1='Yes', button2='No', *, icon:str=None):
    button_name = button_dialog(title, message, [button1, button2], icon=icon)
    if button_name == button1:
        return True
    else:
        return False
    
# Single-button dialog. Returns None.
def simple_dialog(title:str, message:Union[str, list], 
                  button='Okay', *, icon:str=None):
    button_dialog(title, message, [button], icon=icon)

#### END UI CODE ####

# Compatibility constants (see below)
DELUXE  = 0b10000
LEGACY  = 0b01000
REMAKE  = 0b00100
# Classic and Inferno are in here but are currently unused.
# Basically they would be treated as Legacy with fewer tiles/objects.
CLASSIC = 0b00010 
INFERNO = 0b00001

AUTODETECT = 0b00000 # Only for convert_from

# Dictionary of all objects in all MR versions.
# Format:
# id: (name, compatibility)
#
# compatibility is a binary number with bits in format <dlrci>, where:
# - i for InfernoPlus (1.0.0 - 2.1.0), 
#   last common ancestor of Deluxe + all others
# - c for Classic (by Igor & Cyuubi; 2.1.1 - 3.7.0), 
#   last common ancestor of Remake and Legacy
# - r for Remake (by GoNow; no version numbers),
#   new codebase but mostly backwards-compatible with Classic levels
# - l for Legacy (by Terminal & Casini Loogi; 3.7.1 - 4.6.3)
# - d for Deluxe (by Terminal & Casini Loogi)
# EXAMPLES:
# - 0b11011 means it's compatible with everything but Remake
# - Semisolid at ID 6 is only compatible with Deluxe (0b10000) because it had a
#   different ID in Classic, Legacy, and Remake
ALL_OBJECTS = {
    1: ('player', 0b11111),
    16: ('goombrat', 0b10000),
    17: ('goomba', 0b11111),
    18: ('green koopa', 0b11111),
    19: ('red koopa', 0b11111),
    21: ('flying fish', 0b11111),
    22: ('piranha plant', 0b11111),
    23: ('spiny', 0b11000),
    24: ('buzzy beetle', 0b11000),
    25: ('bowser', 0b11111),
    33: ('fire bar', 0b11111),
    34: ('lava bubble', 0b11111),
    35: ('bill blaster', 0b11111),
    36: ('bullet bill', 0b11111),
    37: ('object spawner', 0b11110),
    38: ('cheep cheep', 0b10000),
    39: ('blooper', 0b10000),
    40: ('rex', 0b10000),
    49: ('hammer bro', 0b11111),
    50: ('fire bro', 0b10000),
    81: ('mushroom', 0b11111),
    82: ('fire flower', 0b11111),
    83: ('1up', 0b11111),
    84: ('star', 0b11111),
    85: ('axe', 0b11111),
    86: ('poison mushroom', 0b11111),
    87: ('leaf', 0b10000),
    88: ('hammer suit', 0b10000),
    97: ('coin', 0b11111),
    100: ('gold flower', 0b01000), 
        # LEGACY ONLY, not in Deluxe, in Remake editor but unused
    145: ('platform', 0b11111),
    146: ('bus platform', 0b11111),
    149: ('spring', 0b11111),
    161: ('fireball projectile', 0b11111),
    162: ('fire breath projectile', 0b11111),
    163: ('hammer projectile', 0b11111),
    177: ('flag', 0b11111),
    178: ('goalpost', 0b10000), # from SMW
    253: ('text', 0b11111),
    254: ('checkmark', 0b11111),
}
removed_objects = [] # Object IDs removed from the world will go here

# Misc. global variables
convert_fail = False

convert_from = IntVar()
convert_from.set(AUTODETECT)

convert_to = IntVar()
convert_to.set(DELUXE)

# NEW TILE DATABASE
# Format: (tile_name, version_support, deluxe_id, legacy_id, remake_id, 
#           (fallback1, fallback2, ...))
# Fallback can be 0 (air), 1 (solid), or a valid tile_name.
# If possible, make the last fallback supported in all versions.
# If a version doesn't support any fallback, default to air.
TILE_DATABASE = (
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
    ('semisolid', 0b11110, 6, 5, 5, (0,)), 
    ('semisolid weak', 0b01110, -1, 6, 6, (0,)), 
    ('water surface', 0b01110, -1, 8, 8, ('water', 0,)), # pushes you down
    ('water current', 0b01110, -1, 9, 9, ('water', 0,)), # pushes you left/right
        # ^ Confirmed REMOVED IN DELUXE: was semisolid if Small; air if Super
    ('water', 0b11110, 7, 7, 7, (0,)),
    ('item block infinite', 0b11110, 25, 25, 25, (0,)),
    # Added in Remake (sorted by Remake ID)
    ('solid ice', 0b11100, 10, 10, 10, (1,)),
    ('note block', 0b11100, 11, 11, 11, (1,)), 
        # ^ called "pop block" in Remake but works the same
    ('conveyor', 0b00100, -1, -1, 12, (1,)),
        # ^ in Deluxe but as 2 different tiles
    # Added in Legacy (sorted by Legacy ID)
    ('item note block', 0b11000, 12, 12, -1, ('note block', 'item block',)),
    ('ice -> tile', 0b01000, -1, 13, -1, ('ice -> object', 'solid ice', 1,)), 
    ('flip block', 0b11000, 8, 14, -1, ('solid breakable',)),
    ('air damage', 0b11000, 5, 15, -1, ('solid damage', 0,)),
    ('ice -> object', 0b11000, 13, 16, -1, ('solid ice', 1,)),
    ('item block progressive', 0b11000, 20, 20, -1, ('item block',)),
    ('semisolid ice', 0b01000, -1, 23, -1, ('semisolid', 1,)),
        # ^ Maybe I should add this to Deluxe? Probably wouldn't be too hard
    ('item block invisible progressive', 0b11000, 27, 26, -1, ('item block invisible',)),
    ('scroll lock', 0b11000, 30, 30, -1, (0,)),
    ('scroll unlock', 0b11000, 31, 31, -1, (0,)),
    ('checkpoint', 0b01000, -1, 40, -1, (0,)),
    ('warp pipe single slow', 0b11000, 93, 87, -1, (1,)),
    ('warp pipe single fast', 0b11000, 94, 88, -1, (1,)),
    ('warp pipe left slow', 0b11000, 89, 89, -1, (1,)),
    ('warp pipe left fast', 0b11000, 90, 90, -1, (1,)),
    ('warp pipe up slow', 0b11000, 91, 91, -1, (1,)),
    ('warp pipe up fast', 0b11000, 92, 92, -1, (1,)),
    ('flagpole level end warp', 0b01000, -1, 161, -1, ('level end warp',)),
    # Added in Deluxe (sorted by Deluxe ID)
    ('player barrier', 0b10000, 9, -1, -1, (0,)),
    ('conveyor left', 0b10000, 14, -1, -1, ('conveyor', 1,)),
    ('conveyor right', 0b10000, 15, -1, -1, ('conveyor', 1,)),
    ('item block regen', 0b10000, 26, -1, -1, 
        ('item block infinite', 'item block',)),
    ('warp tile random', 0b10000, 87, -1, -1, (0,)),
    ('message block', 0b10000, 241, -1, -1, (1,)),
    ('sound block', 0b10000, 239, -1, -1, (0,)), 
        # ^ unused in Legacy at diff. ID
)

# List of tuple(str, str) with any incompatible tiles that got replaced
replacement_list = []

# Build lookups for tile database based on r/l/d tile IDs
# Loading this from a file would be faster but also less secure
deluxe_lookup = {}
for index, item in enumerate(TILE_DATABASE):
    id = item[2]
    if id >= 0:
        deluxe_lookup[id] = index
legacy_lookup = {}
for index, item in enumerate(TILE_DATABASE):
    id = item[3]
    if id >= 0:
        legacy_lookup[id] = index
remake_lookup = {}
for index, item in enumerate(TILE_DATABASE):
    id = item[4]
    if id >= 0:
        remake_lookup[id] = index

# Given a tile's standard string name as it appears in the above database,
# return that tile's database entry.
def get_tile_by_name(name:str):
    for i in TILE_DATABASE:
        if i[0] == name:
            return i
    # If name doesn't exist in database, return air
    return TILE_DATABASE[0]

# Given a tile database entry, return the correct tile data int for the game
# version set in the global variable convert_to
def get_id_for_version(tile:tuple):
    if convert_to.get() == DELUXE:
        new_id = tile[2]
    elif convert_to.get() == REMAKE:
        new_id = tile[4]
    else: # legacy/classic/inferno
        new_id = tile[3]
    return new_id

# Convert a tile from one version to another, including any ID changes and 
# replacements of incompatible tiles.
# Takes in an int[5] list, i.e. the Deluxe tile format.
# Returns the new tile in the target version's format.
def convert_tile(old_td:list):
    global convert_from, convert_to
    # Deluxe TD format:
    # 0. sprite index (keep)
    # 1. bump state (keep)
    # 2. depth (keep)
    # 3. tile data (change)
    # 4. extra data (keep except in special cases)
    new_td = old_td.copy()

    # Get data of the tile that the old id refers to
    if convert_from.get() == DELUXE:
        try:
            db_entry = TILE_DATABASE[deluxe_lookup[old_td[3]]]
        except KeyError:
            # If tile ID is invalid, turn it into air
            db_entry = TILE_DATABASE[0]
    elif convert_from.get() == REMAKE:
        try:
            db_entry = TILE_DATABASE[remake_lookup[old_td[3]]]
        except KeyError:
            # If tile ID is invalid, turn it into air
            db_entry = TILE_DATABASE[0]
    else: # legacy/classic/inferno
        try:
            db_entry = TILE_DATABASE[legacy_lookup[old_td[3]]]
        except KeyError:
            # If tile ID is invalid, turn it into air
            db_entry = TILE_DATABASE[0]

    # Find that tile's new id
    new_td[3] = get_id_for_version(db_entry)

    # If tile not compatible with target version, follow fallback chain
    if not (db_entry[1] & convert_to.get()):
        for i in db_entry[5]: # tuple of possible fallback tiles
            if i == 0 or i == 1: 
                # In the database, 0 and 1 are accepted shorthands for 
                # air and solid, respectively -- for convenience
                new_td[3] = i
                # These will always be the last link in the fallback chain

                # When loop is done, leave note that tile was replaced
                replacement = (db_entry[0], TILE_DATABASE[i][0])
                if replacement not in replacement_list:
                    replacement_list.append(replacement)

                break
            else:
                fallback_entry = get_tile_by_name(i)
                fallback_id = get_id_for_version(fallback_entry)

                if (db_entry[1] | convert_to.get()):
                    # If the fallback tile is compatible: great, use that
                    new_td[3] = fallback_id

                    # BEGIN SPECIAL CASES (mostly for extra data)

                    # Convert conveyors from Remake to Deluxe format
                    if db_entry[0] == 'conveyor' and convert_to.get() == DELUXE:
                        if old_td[4] < 128:
                            new_td[3] = 14 # Conveyor left
                        elif old_td[4] > 128:
                            new_td[3] = 15 # Conveyor right
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
                        # This is where I wish Python had enums

                    # turn ice -> tile blocks into ice -> object blocks
                    # that turn into 0 object
                    if 'ice -> tile' in db_entry[0]:
                        new_td[4] = 0

                    # END SPECIAL CASES

                    # When loop is done, leave note that tile was replaced
                    replacement = (db_entry[0], fallback_entry[0])
                    if replacement not in replacement_list:
                        replacement_list.append(replacement)

                    break
                # Otherwise, do another round of the loop
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

# Test if an image file exists on the web.
# Return True if the specified string is a valid URL.
# Return False if attempting to visit the URL returns an HTTP error.
# Return None if GoNow forgot to renew his TLS certificate again.
def web_file_exists(path:str):
    try:
        r = requests.head(path)
        return r.status_code == requests.codes.ok
    except requests.exceptions.SSLError: 
        # If Remake's certificate expired AGAIN
        return None

# Given a tile of unknown format, return the tile normalized to a list of 5 ints
def extract_tile(tile):
    global warnings

    # Start with an empty tile
    extracted_tile = [30,0,0,0,0]

    try:
        if type(tile) == list:
            # Deluxe: list-based format
            try:
                extracted_tile[0] = int(tile[0])
            except ValueError:
                extracted_tile[0] = 30 # empty sprite
            try:
                extracted_tile[1] = int(tile[1])
            except ValueError:
                extracted_tile[1] = 0
            try:
                extracted_tile[2] = int(tile[2])
            except ValueError:
                extracted_tile[2] = 0
            try:
                extracted_tile[3] = int(tile[3])
            except ValueError:
                extracted_tile[3] = 0
            try:
                extracted_tile[4] = int(tile[4])
            except ValueError:
                extracted_tile[4] = 0
        elif type(tile) == int:
            # Legacy and earlier: td32
            extracted_tile[0] = tile % 2**11 # sprite: 11-bit
            extracted_tile[1] = tile // 2**11 % 2**4 # bump state: 4-bit
            extracted_tile[2] = tile // 2**15 % 2 # depth: 1-bit
            extracted_tile[3] = tile // 2**16 % 2**8 # definition: 8-bit
            extracted_tile[4] = tile // 2**24 % 2**8 # extra data: 8-bit
        # Else, it's a format we just don't recognize at all, so we stick to
        # the default extracted_tile
    except:
        warnings += 'Failed to convert tile: %s \n' % tile

    return extracted_tile

# Given a relative path, convert to an absolute URL path
def absolute_path(version: int, rel_path: str):
    if version == DELUXE:
        return 'https://marioroyale.com/royale/' + rel_path
    elif version == REMAKE:
        return 'https://mroyale.net/' + rel_path
    else: # LEGACY
        return 'https://raw.githubusercontent.com/mroyale/assets/legacy/' + \
                rel_path

# Convert 1 world file from Legacy TO DELUXE, and return string 
# containing all converter warnings
def convert(open_path: str, save_path: str):
    global convert_fail, convert_from, convert_to, warnings
    convert_fail = False # Wipe away previous failed conversions
    warnings = ''

    if open_path == save_path:
        convert_fail = True
        error_msg = 'For your safety, this program does not allow you to \
overwrite your existing world files. Please try a different file path.\n%s\n'\
                % open_path
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
        error_msg = 'The selected file does not exist.\n%s\n' \
                    % open_path
        return error_msg
    except IsADirectoryError:
        convert_fail = True
        error_msg = 'The selected file is a folder.\n%s\n' \
                    % open_path
        return error_msg
    except UnicodeDecodeError:
        # File is an image, movie, or other binary
        convert_fail = True
        error_msg = '''The selected file is a binary file such as an image, \
song, or movie, and could not be read.\n%s\n''' % open_path
        return error_msg
    except json.decoder.JSONDecodeError:
        # File is not JSON
        convert_fail = True
        error_msg = '''The selected text file could not be read.
Are you sure it’s a world?\n%s\n''' % open_path
        return error_msg

    # Create a file at the save path if it doesn't already exist.
    # No overwriting yet because if the user is saving over an existing level
    # and the program crashes, we don't want the user to lose previous progress
    try:
        open(save_path, 'a').close()
    except PermissionError:
        # If user tries to save to a folder they don't have write access to
        convert_fail = True
        error_msg = '''Your computer blocked Deluxifier from saving to the \
selected folder: \n%s\n''' % save_path
        return error_msg

    try:
        # Auto-detect version of source file if necessary
        # Why is this a while loop when I only want to run it once? 
        # Because Python doesn't have goto
        while convert_from.get() == AUTODETECT:
            # Test for Deluxe format by checking if tiles are lists
            if 'layers' in content['world'][0]['zone'][0]:
                dx_check = type(content['world'][0]['zone'][0]['layers'][0]\
                        ['data'][0][0]) == list
            else:
                dx_check = type(content['world'][0]['zone'][0]\
                        ['data'][0][0]) == list
            if dx_check:
                convert_from.set(DELUXE)
                break

            # If the World has "vertical" attribute, it's Remake
            if 'vertical' in content:
                convert_from.set(REMAKE)
                break

            # Try to detect version based on map availability
            # (if we have internet)
            for index, item in enumerate(content['resource']):
                # Expand relative map paths to the correct full URL,
                # based on the version selected/detected earlier.
                # First of all, only do this if it *is* a relative path, because
                # if it's already a full URL, then we shouldn't have any issues
                if item['id'] == 'map' and not \
                        (item['src'].startswith('http://') or \
                        item['src'].startswith('https://') or \
                        item['src'].startswith('//')):
                    try:
                        # First try Legacy URL
                        legacy_url = absolute_path(LEGACY, item['src'])
                        exists_in_legacy = web_file_exists(legacy_url)
                        if exists_in_legacy == True:
                            convert_from.set(LEGACY)
                        elif exists_in_legacy == None:
                            convert_from.set(LEGACY)
                            warnings += \
'Security warning on Legacy map image.\n'
                        else:
                            # If it's not in Legacy, fall back to Remake URL
                            remake_url = absolute_path(REMAKE, item['src'])
                            exists_in_remake = web_file_exists(remake_url)
                            if exists_in_remake == True:
                                convert_from.set(REMAKE)
                                break # break from for loop
                            elif exists_in_remake == None:
                                convert_from.set(REMAKE)
                                warnings += \
'Security warning on Remake map image, what a surprise.\n'
                            # If it's not in Legacy or Remake, give up
                            else:
                                convert_from.set(LEGACY)
                                warnings += \
'The auto-detector detected %s to be a LEGACY world, but it has low confidence \
in this detection. If this is in error, please send Clippy the world that’s \
getting this result.\n' % open_path.split(os.sep)[-1]
                    except requests.exceptions.ConnectionError:
                        # If no internet, fall through to the "detect
                        # everything else as Legacy" code
                        pass
                    finally:
                        break # break from for loop

            # Treat everything else as Legacy because it has more tile options
            # and it's harder to detect from file contents
            # This could make conveyors get misconverted but AFAIK Royale City
            # (which uses vertical) is the only world that has them
            if convert_from.get() == AUTODETECT:
                convert_from.set(LEGACY)
            break
        
        # Can't convert from one version to the same version
        if convert_from.get() == convert_to.get():
            convert_fail = True
            error_msg = 'You can’t convert from %s to %s!' % \
                    (game_ver_str(convert_from), game_ver_str(convert_to))
            return error_msg

        # Vertical (really free-roam) scrolling is now set zone-by-zone
        vertical_world = False
        if convert_from.get() == REMAKE and 'vertical' in content:
            if content['vertical'] == 'true':
                vertical_world = True
            del content['vertical']
        # If ANY zone in a Deluxe world is set to Vertical or Free-Roam camera,
        # make the whole world vertical
        if convert_from.get() == DELUXE and convert_to.get() == REMAKE:
            # Yup, we gotta loop thru EVERY world, level, and zone
            for level_i, level in enumerate(content['world']):
                for zone_i, zone in enumerate(level['zone']):
                    # If world was vertical, add free-roam camera to each zone
                    if content['world'][level_i]['zone'][zone_i]['camera'] != 0:
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
            #     content["audioOverrideURL"] = \
            #         "https://mroyale.net/audio/"
            if convert_from.get() in [LEGACY, CLASSIC, INFERNO]:
                content["audioOverrideURL"] = \
"https://raw.githubusercontent.com/mroyale/assets/legacy/audio/"

            # Delete world data that isn't in Deluxe
            if 'shortname' in content:
                del content['shortname']
            if 'musicOverridePath' in content:
                del content['musicOverridePath']
            if 'soundOverridePath' in content:
                del content['soundOverridePath']

        if convert_to.get() in [CLASSIC, REMAKE, LEGACY]:
            # Add shortname to make world pass validation in
            # Classic and Legacy. For Remake, it's simply useful as a watermark.
            if 'shortname' not in content:
                content['shortname'] = 'DXIFY'
            if 'mode' not in content:
                content['mode'] = 'royale' 

        # Turn lobbies into regular worlds so they don't crash the game
        content['type'] = 'game'
        # Any valid level should have a type, so no existence check needed.
        # If the level is missing a type, it will throw a KeyError, which will
        # make the program say the level is corrupted

        # Add full URL for Legacy assets
        if convert_to.get() == DELUXE:
            if convert_from.get() == LEGACY and 'assets' in content:
                content['assets'] = absolute_path(LEGACY, 
                                                  "assets/"+content['assets'])
            # If the world doesn't specify assets (i.e. Classic & Remake), 
            # use Legacy assets because they're a superset of Classic/Remake's 
            # hardcoded animations
            else:
                content['assets'] = \
"https://raw.githubusercontent.com/mroyale/assets/legacy/assets/assets.json"
        # Similar situation but for Deluxe->Legacy assets
        elif convert_from.get() == DELUXE and convert_to.get() == LEGACY:
            if 'assets' in content:
                content['assets'] = absolute_path(DELUXE, 
                                                  "assets/"+content['assets'])
            else:
                content['assets'] = \
                        "https://marioroyale.com/royale/assets/assets.json"
        # DX->R assets will just be wrong and there's nothing I can do about it

        # Convert map & obj sheets
        for index, item in enumerate(content['resource']):
            # Expand relative map paths to the correct full URL,
            # based on the version selected/detected earlier.
            # First of all, only do this if it *is* a relative path, because
            # if it's already a full URL, then we shouldn't have any issues
            if item['id'] == 'map' and not \
                    (item['src'].startswith('http://') or \
                    item['src'].startswith('https://') or \
                    item['src'].startswith('//')):
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
                    content['resource'][index]['src'] = \
'https://marioroyale.com/royale/img/game/smb_obj.png'
                # Converting from Deluxe to Any: Switch to Legacy default obj
                # Don't need a special case for Deluxe->Remake because Legacy
                # obj is a superset of Remake's
                elif convert_from.get() == DELUXE:
                    content['resource'][index]['src'] = \
'https://raw.githubusercontent.com/mroyale/assets/master/img/game/smb_obj.png'
                # If the conversion doesn't involve Deluxe but it uses a
                # relative path
                elif not (item['src'].startswith('http://') or \
                    item['src'].startswith('https://') or \
                    item['src'].startswith('//')):
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

                if convert_to.get() == DELUXE:
                    # Delete world data that isn't in Deluxe
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
                    
                    # If world was vertical, add free-roam camera to each zone
                    if vertical_world:
                        content['world'][level_i]['zone'][zone_i]['camera'] = 2
                
                # Check for unsupported objects and remove them
                # Need to use a while loop because length of obj list may
                # change while program runs
                obj_i = 0 # START
                while True:
                    # STOP
                    if obj_i >= len(zone['obj']):
                        break
                    
                    # Object is incompatible if it's either:
                    #   - Not in the list of all objects
                    #   - In the list but not flagged as supported in
                    #     the target version
                    if zone['obj'][obj_i]['type'] not in ALL_OBJECTS or not \
                            ALL_OBJECTS[zone['obj'][obj_i]['type']][1] & \
                            convert_to.get():
                        # Log the removed object if it's not already in the
                        # removed objects list
                        if zone['obj'][obj_i]['type'] not in removed_objects:
                            removed_objects.append(zone['obj'][obj_i]['type'])
                        # Actually remove the object from the world
                        del content['world'][level_i]['zone'][zone_i]\
                                ['obj'][obj_i]
                        # Reduce the loop variable to account for the removal
                        obj_i -= 1

                    # STEP
                    obj_i += 1

                # Two different conversion options based on if level has layers
                if 'layers' in zone:
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
                        # Layers used to be deleted here
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

    except KeyError:
        # File is missing required fields
        convert_fail = True
        error_msg = '''The selected file appears to be corrupted.
Are you sure it’s a world?\n%s\n''' % open_path
        return error_msg

    # Open the file for real and wipe it
    write_file = open(save_path, 'w')
    # Save the file's new contents
    json.dump(content, write_file, separators=(',',':'))
    # Close the file to prevent bugs that occur in large levels
    write_file.close()

    warnings += 'YOUR CONVERTED WORLD HAS BEEN SAVED TO:\n'+save_path+'\n\n'

    # Report the IDs of incompatible objects that were removed
    if removed_objects:
        warnings += 'Removed incompatible objects with the following IDs: '
        for index, item in enumerate(removed_objects):
            # Print the name of the incompatible object if available
            try:
                warnings += '%i (%s)' % (item, ALL_OBJECTS[item][0])
            except KeyError:
                warnings += str(item)
            # Add comma if we aren't at the end of the removed objects list
            if index < (len(removed_objects) - 1):
                warnings += ', '
        warnings += '\n'

    # Report the IDs of incompatible tiles that were replaced
    if replacement_list:
        for i in replacement_list:
            warnings += 'Incompatible tile definition “%s” \
replaced with “%s”\n' % (i[0], i[1])
    # Tiles that work the same but have different IDs across versions are
    # converted silently as of v3.0.0

    return warnings

# Given an IntVar (from convert_from or convert_to), 
# return the string associated with that game version number
# (e.g. 'INFERNO' for v=1)
def game_ver_str(v:IntVar):
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

# Ask user for a single file then pass its path to the main convert() function
def convert_file():
    global convert_from, convert_to

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
    warnings = convert(open_path, save_path)

    # Stop the timer
    t2 = time()

    # Show off how fast my program is
    done_heading = 'Done in %f seconds' % (t2-t1)
    # Overwrite done message if conversion failed
    if convert_fail:
        done_heading = 'Failed to convert world'

    # Tell the user the conversion is done
    simple_dialog(done_heading, warnings, 'Continue', 
                  icon=('error' if convert_fail else 'done'))
    menu()

def convert_folder():
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
    warnings = ''

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
    heading = Label(main_frame, text='Converting %i files' % len(files),
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

        warnings += convert(item, save_dir + os.sep + filename) + '\n\n'

    # Save all warnings to a log file in the "converted" folder
    log_file = open(save_dir + '/_WARNINGS.LOG', 'a')
    log_file.write(warnings)
    log_file.close()

    # Stop the timer
    t2 = time()

    # Show off how fast my program is
    done_heading = 'Done in %f seconds' % (t2-t1)
    # No "Failed to convert" message for folder conversions
    # because we're not converting a single world

    # Tell the user the conversion is done
    simple_dialog(done_heading, 
['All converted worlds have been saved to the folder with the path  “%s”.' % \
 save_dir, 'If there were any converter warnings, they have been logged to \
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

    # Display message of the day
    motd()
    # Show menu
    menu()
        
def menu():
    global convert_from, convert_to

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
        Radiobutton(main_frame, text='Cross-platform (R/L)', bg=colors['BG'],
                    variable=convert_to, value=CLASSIC),
        Radiobutton(main_frame, text='Remake', bg=colors['BG'],
                    variable=convert_to, value=REMAKE),
        Radiobutton(main_frame, text='Legacy', bg=colors['BG'],
                    variable=convert_to, value=LEGACY),
        Radiobutton(main_frame, text='Deluxe (default)', bg=colors['BG'],
                    variable=convert_to, value=DELUXE),
    ]
    for index, item in enumerate(col2_options):
        item.place(x=240, y=100+(20*index))

    window.update()

    window.mainloop()

def warnings_bugs():
    simple_dialog('WARNING - HEALTH AND SAFETY', 
        [
            'Deluxifier is designed for use in private lobbies, or as a \
starting point for manual conversion. It is not designed to be used to put \
converted-but-otherwise-untouched levels into public rotation.',
            '<i>You may encounter the following issues with levels converted \
using this tool:',
            '''\
- Music may not load (except for Legacy->Deluxe conversions).
- assets.json animations will play at 2× speed in Deluxe since the game is now \
60fps. Similarly, worlds converted FROM Deluxe will play animations
at ½× speed.
- Worlds converted to/from Deluxe will use the target version’s object sheet \
(e.g. Legacy->Deluxe will use Deluxe obj).
- Vines may not render properly in worlds converted to/from Deluxe.'''
        ], icon='warning')
    menu()

# Download and display the online Message of the Day
'''
For each line, everything before the first space is the full list versions 
that should show the message. The rest of the line is the message itself.
The program displays a maximum of 1 MOTD -- the first that matches its version.

EXAMPLE MOTD FORMAT:

# This line is a comment and will be ignored.
u_2.3.0 Deluxifier v3.0.0 is now available! Click the "View Update" button \
    to open Github and download the update.
2.2.1_2.2.2 WARNING: Please update your program to 2.3.0 or later. \
    The version you're currently using has a bug that could damage your files.
* We will only be adding the W.

This version of the program would display "We will only be adding the W."
because it doesn't match any of the versions specified for the warnings.
'''
def motd():
    motd_url = 'https://raw.githubusercontent.com/WaluigiRoyale/\
Deluxifier/main/motd.txt'
    try:
        # Download and read MOTD
        urllib.request.urlretrieve(motd_url, 'motd.txt')
        motd_file = open('motd.txt')
        motd_lines = motd_file.read().splitlines()
        for i in range(len(motd_lines)):
            # Split into version and message
            motd_lines[i] = motd_lines[i].split(' ', 1) 
            if (len(motd_lines[i]) == 2) and \
                    ((VERSION in motd_lines[i][0]) or \
                        (motd_lines[i][0] == '*')):
                motd = motd_lines[i][1]
                motd_header = 'News!'
                motd_buttons = ['Exit', 'Continue']
                # Add update button if MOTD is flagged as an update notice
                if 'u' in motd_lines[i][0].lower():
                    motd_buttons.insert(0, 'View Update')
                    motd_header = 'Update available'
                motd_continue = button_dialog(motd_header, motd, motd_buttons)
                if motd_continue == 'Exit':
                    exit_app()
                elif motd_continue == 'View Update':
                    webbrowser.open('https://github.com/WaluigiRoyale/\
Deluxifier/releases/latest')
                else: # Continue
                    return
    except:
        # If the internet isn't cooperating or the MOTD file is malformed, 
        # no big deal, just skip it
        pass

def crash(exctype=None, excvalue=None, tb=None):
    import tkinter.messagebox as messagebox
    try:
        bomb = PhotoImage(file='ui/bomb.gif')
        window.iconphoto(False, bomb)
    finally:
        # Tkinter doesn't have a "public" way to show the error dialog I want,
        # but the options are hidden under the hood. 
        # Code based on Tkinter messagebox.py
        btn = messagebox._show('Error', '''An error has occurred.
%s: %s''' % (str(exctype)[8:-2], excvalue), 
messagebox.ERROR, messagebox.ABORTRETRYIGNORE)
        # btn might be a Tcl index object, so convert it to a string
        btn = str(btn)
        if btn == 'ignore':
            return
        elif btn == 'retry':
            menu()
        else: # abort
            exit_app()

def exit_app():
    window.destroy()
    sys.exit()

#### MAIN PROGRAM START ####
try:
    # Comment out during development if you want crashes to be logged to the
    # console instead of displaying a bomb dialog
    window.report_callback_exception = crash
    
    # Determine if we're running on replit
    if os.path.isdir("/home/runner") == True:
        import tkinter.messagebox as messagebox

        # Ask user to enter fullscreen
        messagebox.showinfo(window, 
                message='''\
Looks like you’re running the online (Replit) version of the world converter! 
You may want to enter fullscreen so you can click all the buttons.
Click the ⋮ on the “Output” menu bar then click “Maximize”. 
If you’re on a phone, rotate it sideways, zoom out, \
and hide your browser’s toolbar.''')

        # show online instructions
        messagebox.showinfo(window, 
        message='''Before converting your first file:
1. Create a Replit account. You can use an existing Google or Github account.
2. Click “Fork Repl” and follow the instructions.
3. In your newly-forked project, drag the world JSONs you want to convert \
into the list of files in the left sidebar.''')
        setup()
    else:
        setup()

except Exception as e:
    ei = sys.exc_info()
    crash(ei[0], ei[1])
