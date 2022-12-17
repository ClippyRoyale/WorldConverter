'''
DELUXIFIER — A Python-based MRDX world converter
Version 1.0.0

Copyright © MMXXII clippy#4722

WARNING:
MR Deluxe is in closed alpha. The world format may change at any time.
Don't delete your old world files (even after the game is out).

LICENSE INFO:
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

For a copy of the license, see <https://www.gnu.org/licenses/>.

CHANGELOG:
Version 0.0 (Sep. 1, 2022): Preliminary version; based on sample world files.
    Converted worlds cannot be tested in-game yet.

Version 0.1 (Sep. 30, 2022): Based on the latest private world 1 file.
  + Inserts default resources.effects (which wasn't in Legacy)
  + Deletes data only used in Legacy/Remake (e.g. layers, shortname)
  + Fixes relative resource URLs so they use Legacy sprites instead of
    glitched Deluxe ones
  - Removed insertion of resources.player (no longer part of DX world JSON)

Version 0.2 (Oct. 2, 2022):
  + Deletes objects that Deluxe doesn't support
      * The converter should now produce playable conversions for all worlds,
        though some features may be missing from newer worlds. I haven't
        tested it on every world yet, so please report any bugs/game crashes!
  + Better warnings if you try to overwrite an existing file
      * Basically went back to how it was in v0.0 but with a major bug fixed
  * Convert ALL obj sheets to the Deluxe default, not just Legacy default objs
  * Many more comments explaining how the code works
  + Jacob

Version 0.2.1 (Oct. 2, 2022):
  * Spinies are no longer deleted when converting
      * They got added back into Deluxe

Version 0.2.2 (Oct. 15, 2022):
  * Buzzy beetles are no longer deleted when converting
      * They got added back into Deluxe

Version 0.3 (Oct. 16, 2022):
  * Assets file is no longer deleted when converting
      * Side effect of fixing animation bugs
  + Add fallback assets if the world never had assets URL to begin with
    (e.g. if it's a remake world)

Version 0.4 (Oct. 18, 2022):
  + Converter now flags unsupported tile definitions and tries to degrade
    them gracefully

Version 0.5 (Oct. 23, 2022):
  + Auto-converts air damage and semisolid
  + Now distinguishes between incompatible tiles being replaced with fallbacks
    and tiles whose IDs just changed
  + Put framework in place for more compatibility checking to be added later
  * No longer deletes warp pipe left (slow and fast)
      * They got added back into Deluxe

Version 0.5.1 (Oct. 25, 2022):
  * Water standard is no longer deleted when converting
      * It got added back into Deluxe

Version 0.6 (Oct. 31, 2022):
  + Added ability to convert multiple worlds without having to restart program
  + Sound blocks added to Deluxe

Version 0.6.1 (Nov. 2, 2022):
  * Fixed crashes when converting a file without an assets.json link

Version 0.6.2 (Nov. 29, 2022):
  + Now supports Goombrats
      * They were added to Deluxe; not sure why a Legacy world would have the
        ID but if you add it in manually because you're using the Remake
        editor or something, they won't get taken out
  + Warning about anticheat false positives
  * Removes "vertical" metadata because Deluxe doesn't support vertical (yet)
  - Removed Jacob
      * Sorry, it took up too much space

Version 0.6.3 (Nov. 30, 2022):
  + No longer deletes gamemode

Version 1.0.0 (Dec. 16, 2022):
  + Added GUI
      * Based on the Skin Converter GUI
      * Helpfully colored blue so you can tell it apart
  + Added batch conversion (convert every world in a folder)
  * Increased stability when handling invalid files
  * Fixed loading of JSON files so converter can read files with byte order
    marks (e.g. Legacy hell1.json)
  * While the program itself is stable, it should still be treated as a
    public beta because Deluxe isn't out yet.

KNOWN BUGS: See warnings_bugs() in code for list
'''

import codecs, json, copy, sys, os

from time import time
from glob import glob

from tkinter import *
import tkinter.font as tkfont
import tkinter.filedialog as filedialog

#### BEGIN UI SETUP ####

VERSION = '1.0.0 beta'

window = Tk()
window.wm_title('Deluxifier v' + VERSION)
window.geometry('640x320')
# UNCOMMENT THIS LINE ON REPL.IT BUILDS OR TO RUN THE APP IN FULLSCREEN
window.attributes('-fullscreen', True)

COLORS = {
    'red': '#c00000',
    'green': '#008000',
    'blue': '#0080ff',
    'gray': '#808080',
    'silver': '#c0c0c0',
    # Background color is baby blue to distinguish this app from Skin Converter
    'BG': '#c0e0ff',
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

side_frame = LabelFrame(window, width=160, height=320, bg=COLORS['BG'])

'''
gray = not yet reached
blue = in progress
green = completed
red = failed
'''
step_status = ['blue', 'gray', 'gray', 'gray']
steps = [
    Label(side_frame, text='● Main Menu', fg=COLORS[step_status[0]], 
        justify='left', bg=COLORS['BG']),
    Label(side_frame, text='● Open & Save Paths', 
        fg=COLORS[step_status[1]], 
        justify='left', bg=COLORS['BG']),
    Label(side_frame, text='● Run Script', fg=COLORS[step_status[2]], 
        justify='left', bg=COLORS['BG']),
    Label(side_frame, text='● Summary', fg=COLORS[step_status[3]], 
        justify='left', bg=COLORS['BG']),
]

title = Label(side_frame, text='Deluxifier v'+VERSION, 
        font=f_bold, bg=COLORS['BG'])
footer = Label(side_frame, text='a Clippy production', 
        fg=COLORS['gray'], bg=COLORS['BG'])

main_frame = LabelFrame(window, width=480, height=320, bg=COLORS['BG'])
main_frame.grid_propagate(False)

menu_heading = Label(main_frame, text='Welcome to Deluxifier', 
        font=f_heading, bg=COLORS['BG'])
menu_subhead = Label(main_frame, 
        text='The community-supported MR Deluxe world converter', bg=COLORS['BG'])

menu_btns = [
    Button(main_frame, text='Convert one world',
            font=f_large, highlightbackground=COLORS['BG']),
    Button(main_frame, text='Convert every world in a folder',
            font=f_large, highlightbackground=COLORS['BG']),
    Label(main_frame, bg=COLORS['BG']), # filler
    Button(main_frame, text='Warnings & Bugs', 
            highlightbackground=COLORS['BG']),
    Label(main_frame, bg=COLORS['BG']), # filler
    Button(main_frame, text='Exit', highlightbackground=COLORS['BG']),
]

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
        item.config(fg=COLORS[step_status[index]])
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
            justify='left', bg=COLORS['BG'])
    subhead.place(x=0, y=36)

    return subhead

# Generic function to display a dialog box in the window, 
# with text and buttons.
# The code here is copied dialog() from my Skin Converter.
# Deluxifier doesn’t use icons, to reduce the number of dependencies, and
# because it has fewer dialog boxes. However, the 
def dialog(heading_text, msg_text, bottom_text, icon_name: None, 
        btn1_text, btn1_event, btn2_text=None, btn2_event=None):
    cls()

    # if icon_name in icons:
    #     icon = Label(main_frame, image=icons[icon_name])
    #     icon.place(x=470, y=10, anchor=NE)

    if heading_text:
        heading = Label(main_frame, text=heading_text, font=f_heading, 
                justify='left', bg=COLORS['BG'])
        heading.place(x=0, y=0)

    msg = []
    if isinstance(msg_text, str): 
        # Convert to list if message is only one line / a string
        msg_text = [msg_text]
    for index, item in enumerate(msg_text):
        if item.startswith('<b>'):
            msg.append(Label(main_frame, text=item[3:], justify='left', 
                wraplength=470, font=f_bold, bg=COLORS['BG']))
        else:
            msg.append(Label(main_frame, text=item, justify='left', 
                wraplength=470, bg=COLORS['BG']))

        if heading_text:
            msg[index].place(x=0, y=36+index*24)
        else: # Empty heading = place text at top
            msg[index].place(x=0, y=index*24)

    if bottom_text:
        bottom = Label(main_frame, text=bottom_text, justify='left', 
                bg=COLORS['BG'])
        bottom.place(x=0, y=280, anchor=SW)

    btn1 = Button(main_frame, text=btn1_text,
            highlightbackground=COLORS['BG'])
    if btn2_text:
        btn2 = Button(main_frame, text=btn2_text,
                highlightbackground=COLORS['BG'])

    if btn2_text:
        btn1.place(x=230, y=310, anchor=SE)
        btn2.place(x=250, y=310, anchor=SW)
    else:
        btn1.place(x=240, y=310, anchor=S)

    btn1.bind('<Button-1>', lambda _: btn1_event())
    if btn2_text:
        btn2.bind('<Button-1>', lambda _: btn2_event())

#### END UI CODE ####

# Tuple of every valid object ID in Deluxe
VALID_OBJECTS = (
    1, # player
    16, # goombrat (DELUXE ONLY)
    17, # goomba
    18, # green koopa troopa/paratroopa
    19, # red koopa troopa/paratroopa
    21, # flying fish
    22, # p. plant
    23, # spiny (LEGACY/DELUXE ONLY)
    24, # buzzy beetle (LEGACY/DELUXE ONLY)
    25, # bowser
    33, # fire bar
    34, # lava bubble
    35, # bill blaster
    36, # bullet bill
    49, # hammer bro
    50, # fire bro (DELUXE ONLY)
    81, # mushroom
    82, # fire flower
    83, # 1up
    84, # star
    85, # axe
    86, # poison mushroom
    97, # coin
    145, # platform
    146, # bus platform
    149, # spring
    161, # fireball projectile
    162, # fire breath projectile
    163, # hammer projectile
    177, # flag
    253, # text
    254, # checkmark
)
# Dictionary of every object ID+name from Legacy/Remake that's NOT in Deluxe
INCOMPATIBLE_OBJECTS = {
    37 : 'Object Spawner', # REMAKE/LEGACY
    100 : 'Gold Flower', # LEGACY (in Remake editor but unused)
}
removed_objects = [] # Object IDs removed from the world will go here

# Compatibility contants
DELUXE  = 0b10000
LEGACY  = 0b01000
REMAKE  = 0b00100
CLASSIC = 0b00010
INFERNO = 0b00001

# Tile definitions that exist in Deluxe at the same ID as Legacy/Remake.
# Format:
# id: (name, compatibility)
# compatibility is a binary number with bits in format <dlrci>, where:
# - i for InfernoPlus (1.0.0 - 2.1.0), 
#   last common ancestor of Deluxe + all others
# - c for Classic (by Igor & Cyuubi; 2.1.1 - 3.7.0), 
#   last common ancestor of Remake and Legacy
# - r for Remake (by GoNow; no version numbers)
# - l for Legacy (by Terminal and Casini Loogi; 3.7.1 - 4.5.0)
# - d for Deluxe (by Terminal and Casini Loogi)
# EXAMPLES:
# - 0b11011 means it's compatible with everything but Remake
# - Semisolid at ID 6 is only compatible with Deluxe (0b10000) because it had a
#   different ID in Classic, Legacy, and Remake
VALID_TILES = {
    0: ('air', 0b11111),
    1: ('solid', 0b11111),
    2: ('solid bumpable', 0b11111),
    3: ('solid breakable', 0b11111),
    4: ('solid damage', 0b11110),
    5: ('air damage', 0b10000), # was semisolid in Remake/Legacy
    6: ('semisolid', 0b10000), # was semisolid weak in Remake/Legacy
    7: ('water', 0b11110),
    17: ('item block', 0b11111),
    18: ('coin block', 0b11111),
    19: ('coin block multi', 0b11111),
    20: ('item block progressive', 0b11000), # (LEGACY/DELUXE ONLY)
    21: ('item block invisible', 0b11111),
    22: ('coin block invisible', 0b11111),
    24: ('vine block', 0b11111),
    25: ('item block infinite', 0b11110),
    30: ('scroll lock', 0b11000), # (LEGACY/DELUXE ONLY)
    31: ('scroll unlock', 0b11000), # (LEGACY/DELUXE ONLY)
    81: ('warp tile', 0b11111),
    82: ('warp pipe down slow', 0b11111),
    83: ('warp pipe right slow', 0b11111),
    84: ('warp pipe down fast', 0b11111),
    85: ('warp pipe right fast', 0b11111),
    86: ('level end warp', 0b11111),
    89: ('warp pipe left slow', 0b11000), # (LEGACY/DELUXE ONLY)
    90: ('warp pipe left fast', 0b11000), # (LEGACY/DELUXE ONLY)
    160: ('flagpole', 0b11111),
    165: ('vine', 0b11111),
    239: ('sound block', 0b10000), # Deluxe only, unused in Legacy at diff. ID
    240: ('vote block', 0b11111),
    241: ('message block', 0b10000), # (DELUXE ONLY)
}
# Format:
# old_id: (old_name, new_id, is_fallback)
# If is_fallback is True, the conversion is a fallback to a different tile.
# If is_fallback is False, the tile just has a different ID in Deluxe.
CONVERT_TILES = {
    # Supported but under a new ID
    5: ('semisolid', 6, False),
    15: ('air damage', 5, False), # LEGACY ONLY

    # Unsupported, to replace with fallbacks
    # 5 moved
    6: ('semisolid weak', 6, True), 
        # Confirmed as REMOVED IN DELUXE: was semisolid if Small; air if Super
    8: ('water surface', 7, True), # pushes you down?
    9: ('water current', 7, True), # pushes you left/right
    10: ('solid ice', 1, True),
    11: ('note block', 1, True),
    12: ('item note block OR conveyor block', 17, True), 
        # LEGACY: item note block; REMAKE: conveyor (custom levels only)
    13: ('solid ice into tile', 1, True), 
        # fireball turns ice into tile def specified in extra data
    14: ('flip block', 3, True), # LEGACY ONLY
    # 15 moved
    16: ('solid ice into object', 1, True),
        # fireball turns ice into object id specified in extra data
    23: ('semisolid ice', 1, True), # LEGACY ONLY
    26: ('item block progressive invisible', 21, True), # LEGACY ONLY
    40: ('checkpoint (legacy beta)', 40, True), # LEGACY ONLY (unused)
    87: ('warp pipe single slow', 81, True), # LEGACY ONLY
    88: ('warp pipe single fast', 81, True), # LEGACY ONLY
    91: ('warp pipe up slow', 81, True), # LEGACY ONLY
    92: ('warp pipe up fast', 81, True), # LEGACY ONLY
    161: ('flagpole level end warp', 86, True),
        # LEGACY ONLY: ends level only if you went down flagpole
        # Suspected REMOVED IN DELUXE
}
replaced_tiles = []

convert_fail = False

# Convert 1 world file, and return string containing all converter warnings
def convert(open_path: str, save_path: str):
    global convert_fail
    warnings = ''

    if open_path == save_path:
        status_fail()
        dialog('Error', 'For your safety, this program does not allow you to \
overwrite your existing world files. Please try a different file path.', None,
                None, 'Okay', menu)

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
    # If one does, it will be wiped.
    write_file = open(save_path, 'w')

    try:
        # Add extra effects sprite sheet that's not in Legacy or Remake
        content['resource'].append({"id":"effects",
                "src":"img/game/smb_effects.png"})

        # Delete world data that isn't in Deluxe
        if 'vertical' in content:
            del content['vertical']
            warnings += 'This world is vertical. Vertical worlds are not \
supported in Deluxe and may be difficult or impossible to play. They are also \
known to the state of California to cause anticheat false positives.'
        if 'shortname' in content:
            del content['shortname']
        if 'musicOverridePath' in content:
            del content['musicOverridePath']
        if 'soundOverridePath' in content:
            del content['soundOverridePath']

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

        # Convert the sprites
        for index, item in enumerate(content['resource']):
            # Convert relative map paths to the final Legacy map
            # because the Deluxe sheets are different
            if item['id'] == 'map' and item['src'] == 'img/game/smb_map.png':
                content['resource'][index]['src'] = '\
https://raw.githubusercontent.com/mroyale/assets/master/img/game/smb_map.png'

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
                
                # Check for unsupported objects and remove them
                # Need to use a while loop because length of obj list may
                # change while program runs
                obj_i = 0 # START
                while True:
                    # STOP
                    if obj_i >= len(zone['obj']):
                        break

                    if zone['obj'][obj_i]['type'] not in VALID_OBJECTS:
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
                        if layer['z'] == 0:
                            # Deep-copy layer data
                            content['world'][level_i]['zone'][zone_i]['data'] =\
                                    copy.deepcopy(content['world'][level_i]
                                        ['zone'][zone_i]['layers'][layer_i]\
                                        ['data'])

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
                                    # list-based data
                                    content['world'][level_i]['zone'][zone_i]\
                                            ['data'][row_i][tile_i] = \
                                            [tile_sprite, tile_bump, tile_depth,
                                            tile_def, tile_extra]

                            # Delete the layers then get out
                            # Comment out the next line if layers come back
                            del content['world'][level_i]['zone'][zone_i]\
                                    ['layers']
                            break
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
                                    [row_i][tile_i] = [tile_sprite, tile_bump, 
                                    tile_depth, tile_def, tile_extra]
    except KeyError:
        # File is missing required fields
        convert_fail = True
        error_msg = '''The selected file appears to be corrupted.
Are you sure it’s a world?\n%s\n''' % open_path
        return error_msg

    # Overwrite the file
    json.dump(content, write_file, separators=(',',':'))
    # Close the file to prevent bugs
    write_file.close()

    warnings += 'YOUR CONVERTED WORLD HAS BEEN SAVED TO:\n' + save_path + '\n\n'
    # Report the IDs of incompatible objects that were removed
    if removed_objects:
        warnings += 'Removed incompatible objects with the following IDs: '
        for index, item in enumerate(removed_objects):
            # Print the name of the incompatible object if available
            try:
                warnings += '%i (%s)' % (item, INCOMPATIBLE_OBJECTS[item])
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

# Ask user for a single file then pass its path to the main convert() function
def convert_file():
    status_complete()

    open_path = filedialog.askopenfilename(
        title='Select a world file to convert', 
        # filetypes=[('MR World JSON', '*.json *.txt *.game')],
        initialdir='../')
    # If script file path is still empty, user cancelled, back to menu
    if open_path == '':
        menu()
        return

    save_path = filedialog.asksaveasfilename(\
        title='Select a path to save to', defaultextension='.json',
        filetypes=[('MR World JSON', '*.json *.txt *.game')],
        initialdir='../')
    # If save_path is still empty, user cancelled, back to menu
    if save_path == '':
        main()
        return

    status_complete()

    # Start the conversion timer here!
    t1 = time()

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
    dialog(done_heading, warnings, None, None, 'Continue', main)

def convert_folder():
    status_complete()

    open_dir = filedialog.askdirectory(
        title='Select a folder. All worlds in the folder will be converted.',
        initialdir='../')
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
            font=f_heading, bg=COLORS['BG'])
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

        filename = item.split('/')[-1] # Get just the filename w/o the path
        warnings += convert(item, save_dir + '/' + filename) + '\n\n'

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
    dialog(done_heading, 
            'Converter warnings have been logged to _WARNINGS.LOG.',
            None, None, 'Continue', main)

def main():
    #### INITIAL GUI SETUP ####
    # main is a separate function from menu() 
    # because we only need to do everything here once

    # Place frames
    side_frame.place(x=0, y=0)
    main_frame.place(x=160, y=0) 

    # Place sidebar items
    title.place(x=0, y=0)
    footer.place(x=80, y=315, anchor=S)
    for index, item in enumerate(steps):
        item.place(x=0, y=24+24*index)
    # Note that the position of anything with main_frame as parent is 
    # RELATIVE (i.e. 160 will be added to x)

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
            lambda _: warnings_bugs())

    menu_btns[5].bind('<Button-1>', 
            lambda _: exit_app())

    window.update()

    window.mainloop()

def warnings_bugs():
    dialog('⚠️ WARNING - HEALTH AND SAFETY', 
        '''Playing converted worlds may get you banned from the game!
This appears to be a false positive in the game's anticheat.
This bug is known to be triggered by converting the Royale City world.
It may affect other worlds with vertical scrolling or Remake-only features.
I am not responsible if this program lands you in jail!!!

OTHER KNOWN BUGS:
- MRDX will not load music in converted worlds
- All worlds use the Deluxe obj sheet
- assets.json animations will play at 2× speed since the game is now 60fps
''', None, None,
        'Okay', menu)

def crash(exctype=None, excvalue=None, tb=None):
    import tkinter.messagebox as messagebox
    try:
        bomb = PhotoImage(file='bomb.gif')
        window.iconphoto(False, bomb)
    finally:
        messagebox.showerror(window, 
            message='''An error has occurred:
%s''' % (excvalue))
        exit_app()

def exit_app():
    window.destroy()
    sys.exit()

#### MAIN PROGRAM START ####
try:
    # window.report_callback_exception = crash
    
    # Test if we're running on replit
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
        main()
    else:
        main()

except Exception as e:
    ei = sys.exc_info()
    crash(None, ei[1])
