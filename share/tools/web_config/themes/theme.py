#!/usr/bin/env python3

import argparse
import json
import plistlib
import sys

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-g', help='use global scope (default scope: universal)', action='store_true')
    parser.add_argument('theme_file')
    args = parser.parse_args()
    infile = args.theme_file
    variable_scope = '--global' if args.g else '--universal'
    variable_map = {}

    #print('Parsing theme from file: {}'.format(infile))
    if infile.endswith('.sublime-color-scheme'):
        process_sublime_theme(variable_map, infile)
    elif infile.endswith('.tmTheme'):
        process_textmate_theme(variable_map, infile)
    else:
        print(parser.format_usage())

    #print(variable_map)
    for variable_name in variable_map:
        print('set {} {} {}'.format(variable_scope, variable_name, variable_map[variable_name]))

# TODO: which should take precedence, global or scoped?
def process_sublime_theme(variable_map, theme_file):
    with open(theme_file) as fp:
        theme_data = json.load(fp)

    apply_global_sublime(variable_map, theme_data['globals'])

    for rule in theme_data['rules']:
        color_scopes = [x.strip() for x in rule['scope'].split(',')]
        color_values = {
            'foreground': rule.get('foreground', '').strip(),
            'background': rule.get('background', '').strip(),
            'font_style': rule.get('font_style', '').strip()
        }
        fish_color = make_fish_color(color_values)
        apply_scoped(variable_map, color_scopes, fish_color)

# TODO: which should take precedence, global or scoped?
def process_textmate_theme(variable_map, theme_file):
    with open(theme_file, 'rb') as fp:
        theme_data = plistlib.load(fp, fmt=plistlib.FMT_XML)

    for setting in theme_data['settings']:
        if 'settings' not in setting:
            continue

        if 'scope' not in setting:
            color_settings = setting['settings']
            apply_global_textmate(variable_map, color_settings)
        else:
            color_settings = setting['settings']
            color_scopes = [x.strip() for x in setting['scope'].split(',')]
            color_values = {
                'foreground': color_settings.get('foreground', '').strip(),
                'background': color_settings.get('background', '').strip(),
                'font_style': color_settings.get('fontStyle', '').strip()
            }
            fish_color = make_fish_color(color_values)
            apply_scoped(variable_map, color_scopes, fish_color)

    #outfile = theme_file.replace('.tmTheme', '.json')
    #print('Writing color scheme to file: {}'.format(outfile))
    #with open(outfile, 'w') as fp:
    #    fp.write(json.dumps(theme_data, separators=(',', ': '), indent=2))

######################
#  Utility functions #
######################

# https://en.wikipedia.org/wiki/ANSI_escape_code#Colors
ANSI_COLORS = [
    'black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white',
    'brblack', 'brred', 'brgreen', 'bryellow', 'brblue', 'brmagenta', 'brcyan', 'brwhite'
]

# https://en.wikipedia.org/wiki/X11_color_names
X11_COLORS = ['TBD']

# TextMate theme color formats:
#   - Hex RGB        example: #FF0000   (red)
#   - Hex RGBA       example: #FF000080 (red with 50% opacity)
#   - Named (X11)    example: aquamarine
#
# Sublime theme color formats:
#   - Hex RGB        example: #FF0000   (red)
#   - Hex RGBA       example: #FF000080 (red with 50% opacity)
#   - RGB notation   example: rgb(255, 0, 0)
#   - RGBA notation  example: rgba(255, 0, 0, 0.5)
#   - HSL notation   example: hsl(0, 100%, 100%)
#   - HSLA notation  example: hsla(0, 100%, 100%, 0.5)
#   - Named (CSS)    example: lemonchiffon
#   - Variables are allowed too

# TODO: handle X11 colors
# TODO: find better solution for RGBA
def convert_to_fish_color(color_string):
    if color_string.startswith('#'):
        # truncate RGB to 6 hex digits
        return color_string[1:7]
    elif color_string in ANSI_COLORS:
        return color_string
    elif color_string in X11_COLORS:
        # https://www.sublimetext.com/docs/3/color_schemes_tmtheme.html#X11_COLORS
        # TODO: use hard-coded RGB mapping, OR use system's rgb.txt
        return color_string
    else:
        return color_string

# Generate the color string in fish format
def make_fish_color(color_map):
    style = get_fish_color_style(color_map)
    fg = get_fish_color_foreground(color_map)
    bg = get_fish_color_background(color_map)
    return ' '.join('{} {} {}'.format(style, fg, bg).split())

def get_fish_color_style(color_map):
    styles = []
    if 'bold' in color_map['font_style']:
        styles.append('--bold')
    if 'italic' in color_map['font_style']:
        styles.append('--italics')
    return ' '.join(styles)

def get_fish_color_foreground(color_map):
    foreground = color_map['foreground']
    if foreground != '':
        foreground = convert_to_fish_color(foreground)
    return foreground

def get_fish_color_background(color_map):
    background = color_map['background']
    if background != '':
        background = '--background={}'.format(convert_to_fish_color(background))
    return background

#####################
#   Global styles   #
#####################

def set_variable_on_match(variable_map, variable_name, color_settings, color_attribute, background=False):
    if color_attribute in color_settings:
        color_fish = convert_to_fish_color(color_settings[color_attribute])
        if background:
            color_fish = '--background={}'.format(color_fish)
        variable_map[variable_name] = color_fish

'''
Capture values from the global color settings.

  - foreground: default color for text
  - background: default background color
  - selection: background color of selected text
  - lineHighlight: background color of line containing the caret
  - findHighlight: background color of text matched by the Find panel

See: https://www.sublimetext.com/docs/3/color_schemes_tmtheme.html#global_settings
'''
def apply_global_sublime(variable_map, color_settings):
    set_variable_on_match(variable_map, 'fish_color_normal', color_settings, 'foreground')
    set_variable_on_match(variable_map, 'fish_color_selection', color_settings, 'selection', background=True)
    set_variable_on_match(variable_map, 'fish_color_match', color_settings, 'line_highlight', background=True)
    set_variable_on_match(variable_map, 'fish_color_search_match', color_settings, 'line_highlight', background=True)
    set_variable_on_match(variable_map, 'fish_color_search_match', color_settings, 'find_highlight', background=True)

def apply_global_textmate(variable_map, color_settings):
    set_variable_on_match(variable_map, 'fish_color_normal', color_settings, 'foreground')
    set_variable_on_match(variable_map, 'fish_color_selection', color_settings, 'selection', background=True)
    set_variable_on_match(variable_map, 'fish_color_match', color_settings, 'lineHighlight', background=True)
    set_variable_on_match(variable_map, 'fish_color_search_match', color_settings, 'lineHighlight', background=True)
    set_variable_on_match(variable_map, 'fish_color_search_match', color_settings, 'findHighlight', background=True)

#####################
#   Scoped styles   #
#####################

def set_variable_on_match_scope(variable_map, variable_name, fish_color, color_scopes, scope):
    if scope in color_scopes:
        variable_map[variable_name] = fish_color

'''
Capture values from the scoped color settings.

  - comment: code comments
  - constant.character.escape: character escapes in strings (\n, \x20)
  - entity.name.function: function and method names (definition site)
  - invalid.illegal: elements that are illegal in a specific context
  - keyword.operator: operators are typically symbols (*, ~)
  - punctuation.definition.comment: symbols that delineate a comment (//, /*)
  - punctuation.separator: separators such as commas and colons
  - punctuation.terminator: semicolons or other statement terminators
  - string.quoted: single, double, and triple quoted strings
  - string.unquoted: unquoted strings, such as in shell scripts
  - variable.function: function and method names (call site only)
  - variable.parameter: parameters to a function or method

See: https://www.sublimetext.com/docs/3/scope_naming.html
'''
def apply_scoped(variable_map, color_scopes, fish_color):
    set_variable_on_match_scope(variable_map, 'fish_color_comment', fish_color, color_scopes, 'comment')
    set_variable_on_match_scope(variable_map, 'fish_color_autosuggestion', fish_color, color_scopes, 'comment')
    set_variable_on_match_scope(variable_map, 'fish_color_end', fish_color, color_scopes, 'punctuation.terminator')
    set_variable_on_match_scope(variable_map, 'fish_color_escape', fish_color, color_scopes, 'constant.character.escape')
    set_variable_on_match_scope(variable_map, 'fish_color_error', fish_color, color_scopes, 'invalid.illegal') # TODO: should this ever change? what about backgrounds?
    set_variable_on_match_scope(variable_map, 'fish_color_param', fish_color, color_scopes, 'string.unquoted')
    set_variable_on_match_scope(variable_map, 'fish_color_param', fish_color, color_scopes, 'string')
    set_variable_on_match_scope(variable_map, 'fish_color_param', fish_color, color_scopes, 'string.quoted')
    set_variable_on_match_scope(variable_map, 'fish_color_quote', fish_color, color_scopes, 'string')
    set_variable_on_match_scope(variable_map, 'fish_color_quote', fish_color, color_scopes, 'string.quoted')
    set_variable_on_match_scope(variable_map, 'fish_color_command', fish_color, color_scopes, 'entity.name.function')
    set_variable_on_match_scope(variable_map, 'fish_color_command', fish_color, color_scopes, 'variable.function')
    set_variable_on_match_scope(variable_map, 'fish_color_param', fish_color, color_scopes, 'variable.parameter')
    set_variable_on_match_scope(variable_map, 'fish_color_operator', fish_color, color_scopes, 'keywork.operator')
    set_variable_on_match_scope(variable_map, 'fish_color_redirection', fish_color, color_scopes, 'keywork.operator')

main()
