'''
DELUXIFIER — A Python-based MRDX world converter
Version 2.3.0

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

import codecs, json, sys, os, requests
import urllib.request
import PIL.ImageTk
from typing import Union
from time import time
from glob import glob
from tkinter import *
import tkinter.font as tkfont
import tkinter.filedialog as filedialog

#### BEGIN UI SETUP ####

VERSION = '2.3.0'

window = Tk()
window.wm_title('Deluxifier v' + VERSION)
window.geometry('640x320')
# Run in fullscreen on Replit only
if os.path.isdir("/home/runner") == True:
    window.attributes('-fullscreen', True)

app_icon = PhotoImage(file='ui/icon.png')
window.iconphoto(False, app_icon)

colors = {
    'red': '#c00000',
    'green': '#008000',
    'blue': '#0080ff',
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

# f_italic = tkfont.Font(slant='italic')
f_bold = tkfont.Font(weight='bold', size=relative_font_size(1))
f_large = tkfont.Font(size=relative_font_size(1.5))
f_heading = tkfont.Font(weight='bold', size=relative_font_size(1.5))

side_frame = LabelFrame(window, width=160, height=320, bg=colors['BG'])

'''
gray = not yet reached
blue = in progress
green = completed
red = failed
'''
step_status = ['blue', 'gray', 'gray', 'gray']
steps = [
    Label(side_frame, text='● Main Menu', fg=colors[step_status[0]], 
        justify='left', bg=colors['BG']),
    Label(side_frame, text='● Open & Save Paths', 
        fg=colors[step_status[1]], 
        justify='left', bg=colors['BG']),
    Label(side_frame, text='● Run Converter', fg=colors[step_status[2]], 
        justify='left', bg=colors['BG']),
    Label(side_frame, text='● Summary', fg=colors[step_status[3]], 
        justify='left', bg=colors['BG']),
]

title = Label(side_frame, text='Deluxifier v'+VERSION, 
        font=f_bold, bg=colors['BG'])
footer = Label(side_frame, text='a Clippy production', 
        fg=colors['gray'], bg=colors['BG'])

main_frame = LabelFrame(window, width=480, height=320, bg=colors['BG'])
main_frame.grid_propagate(False)

menu_heading = Label(main_frame, text='Welcome to Deluxifier', 
        font=f_heading, bg=colors['BG'])
menu_subhead = Label(main_frame, 
        text='The community-supported MR Deluxe world converter', bg=colors['BG'])

menu_btns = [
    Button(main_frame, text='Convert one world',
            font=f_large, highlightbackground=colors['BG']),
    Button(main_frame, text='Convert every world in a folder',
            font=f_large, highlightbackground=colors['BG']),
    Label(main_frame, text='Reverse Mode is OFF (converting to DELUXE format)',
            bg=colors['BG']), # filler
    Button(main_frame, text='Toggle Reverse Mode (BETA)', 
            highlightbackground=colors['BG']),
    Button(main_frame, text='Warnings & Bugs', 
            highlightbackground=colors['BG']),
    Label(main_frame, bg=colors['BG']), # filler
    Button(main_frame, text='Exit', highlightbackground=colors['BG']),
]

back_btn = Button(side_frame, text='Back to Menu', 
        highlightbackground=colors['BG'])

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

# Redraw each step in its current color
def status_refresh():
    cls()
    # Update fill color for each step, then draw it
    for index, item in enumerate(steps):
        item.config(fg=colors[step_status[index]])
        item.place(x=0, y=24+24*index)

# Update the status for each step and redraw the steps
def status_set(newStatus):
    global step_status
    step_status = newStatus
    status_refresh()

# Mark the current step as complete and move to next step
def status_complete():
    global step_status

    next_step = 0
    for i in range(len(step_status)):
        if step_status[i] == 'gray':
            next_step = i
            break
        else:
            step_status[i] = 'green'

    step_status[next_step] = 'blue'

    status_refresh()

# Mark the current step as failed
def status_fail():
    global step_status

    curr_step = 0
    for i in range(1, len(step_status)):
        if step_status[i] == 'blue':
            curr_step = i
            break

    step_status[curr_step] = 'red'

    status_refresh()

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

        # Apply bold styling as needed
        if item.startswith('<b>'):
            dialog_message[-1].config(font=f_bold, 
                                      text=item[3:]) # strip <b> tag

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
CLASSIC = 0b00010
INFERNO = 0b00001

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
    177: ('goalpost', 0b10000), # from SMW
    253: ('text', 0b11111),
    254: ('checkmark', 0b11111),
}
removed_objects = [] # Object IDs removed from the world will go here

# Tile definitions that exist in Deluxe at the same ID as Legacy/Remake.
# Format:
# id: (name, compatibility)
VALID_TILES = {
    0: ('air', 0b11111),
    1: ('solid', 0b11111),
    2: ('solid bumpable', 0b11111),
    3: ('solid breakable', 0b11111),
    4: ('solid damage', 0b11110),
    5: ('air damage', 0b10000), # was semisolid in Remake/Legacy
    6: ('semisolid', 0b10000), # was semisolid weak in Remake/Legacy
    7: ('water', 0b11110),
    8: ('flip block', 0b10000),
    10: ('solid ice', 0b11100),
    11: ('note block', 0b11100), # called "pop block" in Remake but works same
    12: ('item note block', 0b11000), # conveyor in Remake (custom levels only)
    13: ('ice -> object', 0b10000), # was ice -> tile in Legacy
    14: ('conveyor left', 0b10000), # Conveyors worked differently in Remake...
    15: ('conveyor right', 0b10000), # Due to the ID conflict
    17: ('item block', 0b11111),
    18: ('coin block', 0b11111),
    19: ('coin block multi', 0b11111),
    20: ('item block progressive', 0b11000), # (LEGACY/DELUXE ONLY)
    21: ('item block invisible', 0b11111),
    22: ('coin block invisible', 0b11111),
    24: ('vine block', 0b11111),
    25: ('item block infinite', 0b11110),
    26: ('item block regen', 0b10000),
    27: ('item block invisible progressive', 0b10000),
    30: ('scroll lock', 0b11000), # (LEGACY/DELUXE ONLY)
    31: ('scroll unlock', 0b11000), # (LEGACY/DELUXE ONLY)
    81: ('warp tile', 0b11111),
    82: ('warp pipe down slow', 0b11111),
    83: ('warp pipe right slow', 0b11111),
    84: ('warp pipe down fast', 0b11111),
    85: ('warp pipe right fast', 0b11111),
    86: ('level end warp', 0b11111),
    87: ('warp tile random', 0b10000),
    89: ('warp pipe left slow', 0b11000), # (LEGACY/DELUXE ONLY)
    90: ('warp pipe left fast', 0b11000), # (LEGACY/DELUXE ONLY)
    91: ('warp pipe up slow', 0b11000), # (LEGACY/DELUXE ONLY)
    92: ('warp pipe up fast', 0b11000), # (LEGACY/DELUXE ONLY)
    160: ('flagpole', 0b11111),
    165: ('vine', 0b11111),
    239: ('sound block', 0b10000), # Deluxe only, unused in Legacy at diff. ID
    240: ('vote block', 0b11111),
    241: ('message block', 0b10000), # (DELUXE ONLY)
}
# Dictionary of tiles that need to be converted, either due to incompatibility
# or because their ID was changed.
# Format:
# legacy_id: (legacy_name, deluxe_id, is_fallback)
# If is_fallback is True, the conversion is a fallback to a different tile.
# If is_fallback is False, the tile just has a different ID in Deluxe.
CONVERT_TILES = {
    # Supported but under a new ID
    # Make sure the new ID has an entry in VALID_TILES!
    5: ('semisolid', 6, False),
    14: ('flip block', 8, False), # LEGACY ONLY
    15: ('air damage', 5, False), # LEGACY ONLY
    16: ('ice -> object', 13, False),
        # fireball turns ice into object id specified in extra data
    26: ('item block invisible progressive', 27, False), # LEGACY ONLY
    87: ('warp pipe single slow', 93, False), # LEGACY ONLY
    88: ('warp pipe single fast', 94, False), # LEGACY ONLY

    # Unsupported, to replace with fallbacks
    # 5 moved
    6: ('semisolid weak', 6, True), 
        # Confirmed REMOVED IN DELUXE: was semisolid if Small; air if Super
    8: ('water surface', 7, True), # pushes you down?
    9: ('water current', 7, True), # pushes you left/right
    13: ('ice -> tile', 13, True), 
        # Maybe coming soon to Deluxe?
        # fireball turned ice into tile def specified in extra data
        # Turning this into IceObject without updating extra data may cause
        # bugs in-game... we'll see
    # 14 moved
    # 15 moved
    # 16 moved
    23: ('semisolid ice', 1, True), # LEGACY ONLY
    # 26 moved
    40: ('checkpoint (legacy beta)', 0, True), # LEGACY ONLY (unused)
    # 93 moved
    # 94 moved
    161: ('flagpole level end warp', 86, True),
        # LEGACY ONLY: ends level only if you went down flagpole
        # Suspected REMOVED IN DELUXE
}
replaced_tiles = []

# Dictionary of REVERSE tile conversions for De-Deluxifier.
# Anything in CONVERT_TILES that's not a fallback should be included here,
# with key and value[0] reversed.
# Format: 
# deluxe_id: (legacy_id, legacy_name)
REVERSE_CONVERT_TILES = {
    6: (5, 'semisolid'),
    8: (14, 'flip block'),
    5: (15, 'air damage'),
    13: (16, 'ice -> object'),
    27: (26, 'item block invisible progressive'),
    93: (87, 'warp pipe single slow'),
    94: (88, 'warp pipe single fast'),
}

# Misc. global booleans
reverse_mode = False
convert_fail = False

# Test if an image file exists on the web
# Return True if the specified string is a valid URL.
# Return False if attempting to visit the URL returns an HTTP error.
# Return None if GoNow forgot to renew his TLS certificate again.
def web_file_exists(path):
    try:
        r = requests.head(path)
        return r.status_code == requests.codes.ok
    except requests.exceptions.SSLError: 
        # If Remake's certificate expired AGAIN
        return None

# Convert 1 world file from Legacy TO DELUXE, and return string 
# containing all converter warnings
def convert(open_path: str, save_path: str):
    global convert_fail
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
song, movie, or app, and could not be read.\n%s\n''' % open_path
        return error_msg
    except json.decoder.JSONDecodeError:
        # File is not JSON
        convert_fail = True
        error_msg = '''The selected text file could not be read.
Are you sure it’s a world?\n%s\n''' % open_path
        return error_msg

    # Open the save path for writing. 
    # If no file exists at the given path, it will be created.
    # No overwriting yet because if the user is saving over an existing level
    # and the program crashes, we don't want the user to lose previous progress
    write_file = open(save_path, 'a')

    try:
        # First, make sure the world isn't already in Deluxe format.
        # The main giveaway is that the tiles are stored as lists, 
        # not 32-bit integers. 

        dx_cond = False
        # To prevent errors, do a different Deluxe check based on whether the
        # loaded world has layers. If dx_cond is true, the world is already
        # in Deluxe format.
        if 'layers' in content['world'][0]['zone'][0]:
            dx_cond = type(content['world'][0]['zone'][0]['layers'][0]\
                    ['data'][0][0]) == list
        else:
            dx_cond = type(content['world'][0]['zone'][0]['data'][0][0]) == list

        # Apply the appropriate Deluxe conditional and block conversion if True
        if dx_cond:
            convert_fail = True
            error_msg = '''The selected file appears to already be in Deluxe \
format.\n%s\n''' % open_path
            return error_msg
        
        # Add extra effects sprite sheet that's not in Legacy or Remake
        content['resource'].append({"id":"effects",
                "src":"img/game/smb_effects.png"})

        # Vertical (really free-roam) scrolling is now set zone-by-zone
        vertical_world = False
        if 'vertical' in content:
            if content['vertical'] == 'true':
                vertical_world = True
            del content['vertical']

        # Delete world data that isn't in Deluxe
        if 'shortname' in content:
            del content['shortname']
        if 'musicOverridePath' in content:
            del content['musicOverridePath']
        if 'soundOverridePath' in content:
            del content['soundOverridePath']

        # Turn lobbies into regular worlds so they don't crash the game
        content['type'] = 'game'
        # Any valid level should have a type, so no existence check needed.
        # If the level is missing a type, it will throw a KeyError, which will
        # make the program say the level is corrupted

        # Add full URL for Legacy assets
        if 'assets' in content:
            content['assets'] = \
"https://raw.githubusercontent.com/mroyale/assets/legacy/assets/" + \
content['assets']
        # If the world doesn't specify assets (i.e. Classic & Remake worlds), 
        # use Legacy assets because they're a superset of Classic/Remake's 
        # hardcoded animations
        else:
            content['assets'] = \
"https://raw.githubusercontent.com/mroyale/assets/legacy/assets/assets.json"

        # Convert map & obj sheets
        for index, item in enumerate(content['resource']):
            # Convert relative map paths to the full Legacy URL, or if it
            # doesn't exist (because it's a Remake-only world), then use the
            # remake URL.
            # First of all, only do this if it *is* a relative path, because
            # if it's already a full URL, then we shouldn't have any issues
            if item['id'] == 'map' and not \
                    (item['src'].startswith('http://') or \
                    item['src'].startswith('https://') or \
                    item['src'].startswith('//')):
                try:
                    # Preferred option: detect Remake vs. Legacy by checking for
                    # the map sheet online
                    
                    # First try Legacy URL
                    legacy_url = \
'https://raw.githubusercontent.com/mroyale/assets/master/' + item['src']
                    exists_in_legacy = web_file_exists(legacy_url)
                    if exists_in_legacy == True:
                        content['resource'][index]['src'] = legacy_url
                    elif exists_in_legacy == None:
                        content['resource'][index]['src'] = legacy_url
                        warnings += 'Security warning on Legacy map image.\n\n'
                    else:
                        # If it's not in Legacy at all, fall back to Remake URL
                        remake_url = 'https://mroyale.net/' + item['src']
                        exists_in_remake = web_file_exists(remake_url)
                        if exists_in_remake == True:
                            content['resource'][index]['src'] = remake_url
                        elif exists_in_remake == None:
                            content['resource'][index]['src'] = remake_url
                            warnings += \
'Security warning on Remake map image, what a surprise.\n\n'
                        # If it's not in Legacy or Remake, give up
                        else:
                            warnings += '''Could not expand URL of map image.
Your converted world may not be playable.\n\n'''
                except requests.exceptions.ConnectionError:
                    # If no internet, ask the user which map URL to use
                    use_legacy = bool_dialog('Couldn’t connect to the internet',
                            ['Deluxifier couldn’t connect to the internet, so \
you’ll have to answer this question yourself:', 
                            'Was this world made for Remake or Legacy?'],
                            'Remake', 'Legacy', icon='warning')
                    if use_legacy:
                        legacy_url = \
'https://raw.githubusercontent.com/mroyale/assets/master/' + item['src']
                        content['resource'][index]['src'] = legacy_url
                    else: # remake
                        remake_url = 'https://mroyale.net/' + item['src']
                        content['resource'][index]['src'] = remake_url

            # Convert obj path to relative path so it uses the new Deluxe
            # obj and not the Legacy/Remake one which is now glitched
            # I tried using replacing with base64 but it didn't work
            if item['id'] == 'obj':
                content['resource'][index]['src'] = 'img/game/smb_obj.png'

        for level_i, level in enumerate(content['world']): # Loop thru levels
            for zone_i, zone in enumerate(level['zone']): # Loop thru zones
                # Delete world data that isn't in Deluxe
                if 'winmusic' in content['world'][level_i]['zone'][zone_i]:
                    del content['world'][level_i]['zone'][zone_i]\
                            ['winmusic']
                if 'victorymusic' in content['world'][level_i]['zone'][zone_i]:
                    del content['world'][level_i]['zone'][zone_i]\
                            ['victorymusic']
                if 'levelendoff' in content['world'][level_i]['zone'][zone_i]:
                    del content['world'][level_i]['zone'][zone_i]\
                            ['levelendoff']
                    
                # If world was vertical, add free-roam camera setting for zone
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
                    #   - In the list but not flagged as supported in Deluxe
                    if zone['obj'][obj_i]['type'] not in ALL_OBJECTS or not \
                            ALL_OBJECTS[zone['obj'][obj_i]['type']][1] & DELUXE:
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
                                # Separate out the data in the tile format
                                tile_sprite = tile % 2**11
                                tile_bump = tile // 2**11 % 2**4
                                tile_depth = tile // 2**15 % 2
                                tile_def = tile // 2**16 % 2**8
                                tile_extra = tile // 2**24 % 2**8

                                # Replace incompatible tile defs
                                if tile_def in CONVERT_TILES:
                                    if tile_def not in replaced_tiles:
                                        replaced_tiles.append(tile_def)
                                    tile_def = CONVERT_TILES[tile_def][1]

                                # Overwrite the int tiledata with the new 
                                # list-based data. This is the one part that's 
                                # different when the world has layers.
                                content['world'][level_i]['zone'][zone_i]\
                                        ['layers'][layer_i]['data']\
                                        [row_i][tile_i] = \
                                    [tile_sprite, tile_bump, tile_depth,
                                        tile_def, tile_extra]

                                # WATER HITBOX WORKAROUND
                                #   (see extended notes in no-layers section)
                                # Make sure we’re not in top row
                                if (tile_def == 7 or tile_def == 8 or \
                                        tile_def == 9) and row_i >= 1:
                                    # Get data for the tile 1 row up
                                    tile = content['world'][level_i]\
                                            ['zone'][zone_i]['layers'][layer_i]\
                                            ['data'][row_i-1][tile_i]
                                    # If td-1 is air, change it to water
                                    if (tile[3] == 0):
                                        tile[3] = 7
                        # Layers used to be deleted here
                else:
                    for row_i, row in enumerate(zone['data']): # Loop thru rows
                        for tile_i, tile in enumerate(row): # Loop tiles by col
                            # Separate out the data in the tile format
                            tile_sprite = tile % 2**11
                            tile_bump = tile // 2**11 % 2**4
                            tile_depth = tile // 2**15 % 2
                            tile_def = tile // 2**16 % 2**8
                            tile_extra = tile // 2**24 % 2**8

                            # Replace incompatible tile defs
                            if tile_def in CONVERT_TILES:
                                if tile_def not in replaced_tiles:
                                    replaced_tiles.append(tile_def)
                                tile_def = CONVERT_TILES[tile_def][1]

                            # Overwrite the int tiledata w/ new list-based data
                            content['world'][level_i]['zone'][zone_i]['data']\
                                    [row_i][tile_i] = \
                                [tile_sprite, tile_bump, 
                                    tile_depth, tile_def, tile_extra]

                            # WATER HITBOX WORKAROUND
                            # The water hitboxes in Legacy (and probably Remake)
                            # are infamously bad—they’re about a tile too tall.
                            # Deluxe fixes them, but it means we have to change
                            # on old worlds that were build with these
                            # hitboxes in mind.
                            # This will work because the row(s) above already
                            # have their “final” data (in list format).
                            # Make sure we’re not in top row
                            if (tile_def == 7 or tile_def == 8 or \
                                    tile_def == 9) and row_i >= 1:
                                # Get data for the tile 1 row up/same col
                                tile = content['world'][level_i]\
                                        ['zone'][zone_i]['data'][row_i-1]\
                                        [tile_i]
                                # If td-1 is air, change it to water
                                if (tile[3] == 0):
                                    tile[3] = 7

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

    warnings += 'YOUR CONVERTED WORLD HAS BEEN SAVED TO:\n' + save_path + '\n\n'

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
    if replaced_tiles:
        for i in replaced_tiles:
            if CONVERT_TILES[i][2]: # if fallback
                warnings += 'Incompatible tile definition %i (%s) \
replaced with %i (%s)\n' % (i, CONVERT_TILES[i][0], CONVERT_TILES[i][1],
                        VALID_TILES[CONVERT_TILES[i][1]][0])
            else: # tiles with different IDs in different versions
                warnings += 'Tile definition %i (%s) updated to %i\n' % \
                        (i, CONVERT_TILES[i][0], CONVERT_TILES[i][1])

    return warnings

# Reverse convert 1 world file from Deluxe TO LEGACY, and return string 
# containing all converter warnings
def reverse_convert(open_path: str, save_path: str):
    global convert_fail
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
song, movie, or app, and could not be read.\n%s\n''' % open_path
        return error_msg
    except json.decoder.JSONDecodeError:
        # File is not JSON
        convert_fail = True
        error_msg = '''The selected text file could not be read.
Are you sure it’s a world?\n%s\n''' % open_path
        return error_msg

    # Open the save path for writing. 
    # If no file exists at the given path, it will be created.
    # No overwriting yet because if the user is saving over an existing level
    # and the program crashes, we don't want the user to lose previous progress
    write_file = open(save_path, 'a')

    try:
        # First, make sure the world isn't already in Legacy format.
        # The main giveaway: the tiles are stored as integers not lists.

        l_cond = False
        # To prevent errors, do a different Deluxe check based on whether the
        # loaded world has layers. If dx_cond is true, the world is already
        # in Deluxe format.
        if 'layers' in content['world'][0]['zone'][0]:
            l_cond = type(content['world'][0]['zone'][0]['layers'][0]\
                    ['data'][0][0]) == int
        else:
            l_cond = type(content['world'][0]['zone'][0]['data'][0][0]) == int

        # Apply the appropriate Deluxe conditional and block conversion if True
        if l_cond:
            convert_fail = True
            error_msg = '''The selected file appears to already be in Legacy \
format.\n%s\n''' % open_path
            return error_msg

        # Turn lobbies into regular worlds so they don't crash the game
        content['type'] = 'game'
        # Any valid level should have a type, so no existence check needed.
        # If the level is missing a type, it will throw a KeyError, which will
        # make the program say the level is corrupted

        # Add shortname and mode to make world pass validation
        content['shortname'] = 'DXIFY'
        content['mode'] = 'royale'

#         # Add full URL for Legacy assets
#         if 'assets' in content:
#             content['assets'] = \
# "https://raw.githubusercontent.com/mroyale/assets/legacy/assets/" + \
# content['assets']
#         # If the world doesn't specify assets (i.e. Classic & Remake worlds), 
#         # use Legacy assets because they're a superset of Classic/Remake's 
#         # hardcoded animations
#         else:
#             content['assets'] = \
# "https://raw.githubusercontent.com/mroyale/assets/legacy/assets/assets.json"

        # Convert map & obj sheets
        for index, item in enumerate(content['resource']):
            # Convert relative smb_map path to the current Deluxe map
            # because it's different from Legacy.
            if item['id'] == 'map':
                content['resource'][index]['src'] = \
'https://marioroyale.com/royale/' + item['src']

        for level_i, level in enumerate(content['world']): # Loop thru levels
            for zone_i, zone in enumerate(level['zone']): # Loop thru zones
                # Delete world data that isn't in Deluxe
                if 'winmusic' in content['world'][level_i]['zone'][zone_i]:
                    del content['world'][level_i]['zone'][zone_i]\
                            ['winmusic']
                if 'victorymusic' in content['world'][level_i]['zone'][zone_i]:
                    del content['world'][level_i]['zone'][zone_i]\
                            ['victorymusic']
                if 'levelendoff' in content['world'][level_i]['zone'][zone_i]:
                    del content['world'][level_i]['zone'][zone_i]\
                            ['levelendoff']
                
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
                    #   - In the list but not flagged as supported in Deluxe
                    if zone['obj'][obj_i]['type'] not in ALL_OBJECTS or not \
                            ALL_OBJECTS[zone['obj'][obj_i]['type']][1] & LEGACY:
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
                                # If the tile is still an int and not a list
                                # (for whatever reason), leave it
                                if type(tile) != list:
                                    continue

                                # Separate out the data in the tile format
                                try:
                                    tile_sprite = int(tile[0])
                                except ValueError:
                                    tile_sprite = 0
                                try:
                                    tile_bump = int(tile[1])
                                except ValueError:
                                    tile_bump = 0
                                try:
                                    tile_depth = int(tile[2])
                                except ValueError:
                                    tile_depth = 0
                                try:
                                    tile_def = int(tile[3])
                                except ValueError:
                                    tile_def = 0
                                try:
                                    tile_extra = int(tile[4])
                                except ValueError:
                                    tile_extra = 0

                                # Replace incompatible tile defs
                                if tile_def in REVERSE_CONVERT_TILES:
                                    if tile_def not in replaced_tiles:
                                        replaced_tiles.append(tile_def)
                                    tile_def=REVERSE_CONVERT_TILES[tile_def][1]

                                # Overwrite the list tiledata with the new 
                                # int32-based data. This is the one part that's 
                                # different when the world has layers.
                                content['world'][level_i]['zone'][zone_i]\
                                        ['layers'][layer_i]['data']\
                                        [row_i][tile_i] = \
                                    tile_sprite + tile_bump*(2**11) + \
                                    tile_depth*(2**15) + tile_def*(2**16) + \
                                    tile_extra*(2**24)
                else:
                    for row_i, row in enumerate(zone['data']): # Loop thru rows
                        for tile_i, tile in enumerate(row): # Loop tiles by col
                            # If the tile is still an int and not a list
                            # (for whatever reason), leave it
                            if type(tile) != list:
                                continue

                            # Separate out the data in the tile format
                            try:
                                tile_sprite = int(tile[0])
                            except ValueError:
                                tile_sprite = 0
                            try:
                                tile_bump = int(tile[1])
                            except ValueError:
                                tile_bump = 0
                            try:
                                tile_depth = int(tile[2])
                            except ValueError:
                                tile_depth = 0
                            try:
                                tile_def = int(tile[3])
                            except ValueError:
                                tile_def = 0
                            try:
                                tile_extra = int(tile[4])
                            except ValueError:
                                tile_extra = 0

                            # Replace incompatible tile defs
                            if tile_def in REVERSE_CONVERT_TILES:
                                if tile_def not in replaced_tiles:
                                    replaced_tiles.append(tile_def)
                                tile_def=REVERSE_CONVERT_TILES[tile_def][1]

                            # Overwrite the list tiledata with the new 
                            # int32-based data
                            content['world'][level_i]['zone'][zone_i]['data']\
                                    [row_i][tile_i] = \
                                tile_sprite + tile_bump*(2**11) + \
                                tile_depth*(2**15) + tile_def*(2**16) + \
                                tile_extra*(2**24)

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

    warnings += 'YOUR REVERSE-CONVERTED WORLD HAS BEEN SAVED TO:\n' + \
            save_path + '\n\n'

    # # Report the IDs of incompatible objects that were removed
    # if removed_objects:
    #     warnings += 'Removed incompatible objects with the following IDs: '
    #     for index, item in enumerate(removed_objects):
    #         # Print the name of the incompatible object if available
    #         try:
    #             warnings += '%i (%s)' % (item, INCOMPATIBLE_OBJECTS[item])
    #         except KeyError:
    #             warnings += str(item)
    #         # Add comma if we aren't at the end of the removed objects list
    #         if index < (len(removed_objects) - 1):
    #             warnings += ', '
    #     warnings += '\n'

    # Report the IDs of incompatible tiles that were replaced
    if replaced_tiles:
        for i in replaced_tiles:
#             if CONVERT_TILES[i][2]: # if fallback
#                 warnings += 'Incompatible tile definition %i (%s) \
# replaced with %i (%s)\n' % (i, CONVERT_TILES[i][0], CONVERT_TILES[i][1],
#                         VALID_TILES[CONVERT_TILES[i][1]][0])
#             else: # tiles with different IDs in different versions
                warnings += 'Tile definition %i (%s) updated to %i\n' % \
                        (i, CONVERT_TILES[i][0], CONVERT_TILES[i][1])

    return warnings

# Ask user for a single file then pass its path to the main convert() function
def convert_file():
    status_complete()

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

    status_complete()

    # Start the conversion timer here!
    t1 = time()

    if reverse_mode:
        warnings = reverse_convert(open_path, save_path)
    else:
        warnings = convert(open_path, save_path)

    # Stop the timer
    t2 = time()

    status_complete()

    done_heading = '''If you’re seeing this text, it’s an error.
Please tell Clippy!'''
    if convert_fail:
        status_fail()
        done_heading = 'Failed to convert world'
    else:
        # Show off how fast my program is
        done_heading = 'Done in %f seconds' % (t2-t1)

    # Tell the user the conversion is done
    simple_dialog(done_heading, warnings, 'Continue', icon='done')
    menu()

def convert_folder():
    status_complete()

    open_dir = filedialog.askdirectory(
        title='Select a folder. All worlds in the folder will be converted.',
        initialdir='./')
    # If script file path is still empty, user cancelled, back to menu
    if open_dir == '':
        menu()
        return

    status_complete()

    # Start the conversion timer here!
    t1 = time()
    time_last_refresh = t1
    time_since_refresh = 0

    # Get list of files in the folder
    files = glob(open_dir + '/*')
    warnings = ''

    # Make a folder to drop all the converted worlds in
    save_dir = open_dir + '/_converted'
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    else:
        # If there's already a subfolder called _converted, 
        # tack a number on the end
        i = 1
        # Keep trying numbers until we get a folder name that doesn't exist yet
        while os.path.exists(save_dir + str(i)):
            i += 1
        # Permanently add number to save_dir path then create the folder
        save_dir += str(i)
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

        if reverse_mode:
            warnings += reverse_convert(item, save_dir+os.sep+filename) + '\n\n'
        else:
            warnings += convert(item, save_dir + os.sep + filename) + '\n\n'

    # Save all warnings to a log file in the "converted" folder
    log_file = open(save_dir + '/_WARNINGS.LOG', 'a')
    log_file.write(warnings)
    log_file.close()

    # Stop the timer
    t2 = time()

    status_complete()

    # Show off how fast my program is
    done_heading = 'Done in %f seconds' % (t2-t1)
    # No "Failed to convert" message for folder conversions
    # because we're not converting a single world

    # Tell the user the conversion is done
    simple_dialog(done_heading, 
            'If there were any converter warnings, they have been logged to \
_WARNINGS.LOG.', 'Continue', icon='done')
    menu()

def setup():
    #### INITIAL GUI SETUP ####
    # setup is a separate function from menu() 
    # because we only need to do everything here once

    # Place frames
    side_frame.place(x=0, y=0)
    main_frame.place(x=160, y=0) 

    # Place sidebar items
    title.place(x=0, y=0)
    footer.place(x=80, y=315, anchor=S)
    for index, item in enumerate(steps):
        item.place(x=0, y=24+24*index)
    back_btn.place(x=80, y=295, anchor=S)
    back_btn.bind('<Button-1>', lambda _: menu())
    # Note that the position of anything with main_frame as parent is 
    # RELATIVE (i.e. 160 will be added to x)

    # Display message of the day
    motd()
    # Show menu
    menu()
        
def menu():
    status_set(['blue', 'gray', 'gray', 'gray'])

    menu_heading.place(x=240, y=0, anchor=N)
    menu_subhead.place(x=240, y=30, anchor=N)

    next_y = 0
    for i in (menu_btns):
        i.place(x=240, y=60+next_y, anchor=N)
        if str(i.cget('font')) == 'TkDefaultFont':
            next_y += 30
        else: # user-defined large font
            next_y += 40

    menu_btns[0].bind('<Button-1>', 
            lambda _: convert_file())
    menu_btns[1].bind('<Button-1>', 
            lambda _: convert_folder())

    menu_btns[3].bind('<Button-1>', 
            lambda _: toggle_reverse())
    menu_btns[4].bind('<Button-1>', 
            lambda _: warnings_bugs())

    menu_btns[6].bind('<Button-1>', 
            lambda _: exit_app())

    window.update()

    window.mainloop()

def toggle_reverse():
    global reverse_mode
    reverse_mode = not reverse_mode
    if reverse_mode:
        menu_btns[2].config(text=\
'Reverse Mode is ON (converting to LEGACY format)')
    else:
        menu_btns[2].config(text=\
'Reverse Mode is OFF (converting to DELUXE format)')

def warnings_bugs():
    simple_dialog('WARNING - HEALTH AND SAFETY', 
        [
            '<b>Playing converted worlds may cause false positives in the \
game’s anticheat. I am not responsible if this program gets you banned!',
            '''OTHER KNOWN BUGS:
- MRDX will not load music in converted worlds
- All worlds use the Deluxe obj sheet
- assets.json animations will play at 2× speed since the game is now 60fps
- Conveyors (from Remake) are not yet converted properly. A fix will be \
released in the near future.
- Vines may not render properly.''',
            'Reverse Mode is in beta, and I make no guarantees that any \
worlds converted with it will work.'
        ], icon='warning')
    menu()

# Download and display the online Message of the Day
'''
For each line, everything before the first space is the full list versions that should show the message. The rest of the line is the message itself.
The program displays a maximum of 1 MOTD -- the first that matches its version.

EXAMPLE MOTD FORMAT:

2.2.1_2.2.2 WARNING: Please update your program to 2.3.0 or later. \
    The version you're currently using has a bug that could damage your files.
* We will only be adding the W.

This version of the program would display "We will only be adding the W."
because it doesn't match any of the versions specified for the warning.
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
                motd_continue = bool_dialog('News!', motd, 'Exit', 'Continue')
                if motd_continue:
                    return
                else:
                    exit_app()
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

        # Get screen width and height
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()

        # Check screen size and if it's too small, ask user to enter fullscreen
        if screen_width < 640 or screen_height < 320:
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
