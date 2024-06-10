# CHAT UI IMPLEMENTATION

import curses

stdscr = None
output_lines = []

def init_windows():
    global stdscr
    stdscr = curses.initscr()
    curses.noecho()
    curses.cbreak()
    stdscr.keypad(True)

def end_windows():
    global stdscr
    curses.nocbreak()
    stdscr.keypad(False)
    curses.echo()
    curses.endwin()

def read_command(prompt):
    global stdscr
    stdscr.addstr(curses.LINES-1, 0, prompt)
    stdscr.clrtoeol()
    stdscr.refresh()
    curses.echo()
    command = stdscr.getstr(curses.LINES-1, len(prompt)).decode('utf-8')
    curses.noecho()
    stdscr.clrtoeol()
    return command

def print_message(message, prompt="Me> "):
    global stdscr, output_lines
    output_lines.append(message)
    if len(output_lines) >= curses.LINES - 2:
        output_lines.pop(0)

    stdscr.clear()
    for i, line in enumerate(output_lines):
        stdscr.addstr(i, 0, line)
    stdscr.addstr(curses.LINES-1, 0, prompt)
    stdscr.refresh()
