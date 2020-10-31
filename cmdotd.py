#!/usr/bin/python3

"""
 # Command of the day
 Version 2 of my little bubbly bubble to randomize a command and give its description

 > AleK3y, 14 June 2020;
"""

import os, sys
import requests
import json
from colorama import Fore, Back, Style, init
from random import choice

MAXIMUM_CMD_LEN = 10
SPACES_ON_TITLE = True
COLORS = (Fore.BLUE, Fore.CYAN, Fore.GREEN, Fore.MAGENTA, Fore.RED, Fore.YELLOW)

UPDATE_SOURCE = "https://linux.die.net/man/"
SECTIONS = ["1", "6", "8"]
HOME = os.environ["HOME"] if os.name != "nt" else os.environ["USERPROFILE"]
CACHEFILE = f"{HOME}/.cache/cmdotd/manpages.json"		# Every now and then delete this file (back it up first)
MIRRORS = ["https://pastebin.com/raw/79Gb6y3V", "https://pastebin.com/raw/tnvMYmsZ"]		# Raw JSON Mirrors

# Setting up for windows
if os.name == "nt":
	init()

"""
Functions
"""

def info(log):
	sys.stdout.write(f"{Fore.CYAN}[I] {log}{Fore.RESET}")
	sys.stdout.flush()

def error(reason, errno, leave=True):
	sys.stderr.write(f"{Fore.RED}[{errno}] {reason}{Fore.RESET}")
	sys.stderr.flush()

	if leave:
		sys.exit(errno)

def inner_html(html, element):
	"""
	Get the inner HTML of `element` as a string
	"""

	element_close = (element.replace(" ", ">").split(">")[0] + ">").replace("<", "</")

	start = 0
	for index, line in enumerate(html):
		if element in line:
			start = index
			break
	
	stop = 0
	for index, line in enumerate(html):
		if element_close in line:
			stop = index
			break
	
	return "\n".join(html[start+1:stop])

"""
Get the json list of manpages
"""

MANPAGES = {}

# Read the cache file
try:
	MANPAGES = eval(open(CACHEFILE, "r").read())

# Download the pages and cache them
except FileNotFoundError:
	info("Updating the manual pages..\n")

	# Try the source website itself
	try:
		for section in SECTIONS:
			req = requests.get(UPDATE_SOURCE + section)
			html = req.content.decode().split("\n")
			
			# Follow the webiste structure,
			# get the content of the dl element
			dl = inner_html(html, "<dl compact")
			
			# Every iteration is an item to be parsed
			for dt in dl.split("<dt>")[1:]:
				item = dt.split("</dd>")[0]
				binary = item.split("<a")[1].split(">")[1].split("</a")[0]
				description = item.split("<dd>")[1].replace("\n", "")
				MANPAGES[binary] = description		# Finally update the manual

		# Check if the manpages were updated, otherwise try with the mirrors
		if not MANPAGES:
			raise ValueError

	# Otherwise try with the mirrors
	except (requests.exceptions.ConnectionError, IndexError, ValueError):
		error("Couldn't update using the source website\n", -1, False)
		info("Using mirrors\n")
		for mirror in MIRRORS:
			try:
				MANPAGES = eval(requests.get(mirror).content)
				break
			except (requests.exceptions.ConnectionError, SyntaxError):
				continue

		if not MANPAGES:
			error("Couldn't update using mirrors too\n", -2)

	cachedir = "/".join(CACHEFILE.split("/")[:-1])
	os.makedirs(cachedir, exist_ok=True)

	open(CACHEFILE, "w").write(json.dumps(MANPAGES, sort_keys=True, indent=3))

"""
Main loop to choose the command and
print the bubble
"""

while True:
	width = os.get_terminal_size()[0]

	command = choice(list(MANPAGES.keys()))

	try:
		description = MANPAGES[command][0].upper() + MANPAGES[command][1:]		# Make the first letter uppercase

	# Check if the description exists
	except IndexError:
		continue

	# Check if the length of the command is within limits
	title = " ".join(list(command)) if SPACES_ON_TITLE else command
	if len(title) + 4 + 2 >= width or len(command) > MAXIMUM_CMD_LEN:
		continue

	# Setup the head of the bubble to be print
	head = [
		"╭" + "─"*(len(title) + 4) + "╮",
		"│" + " "*2 + choice(COLORS) + Style.BRIGHT + title + Style.RESET_ALL + " "*2 + "│",		# Style.RESET_ALL might break things if the previous text had custom Back or Style
		"├" + "─"*(len(title) + 4) + "╯",
	]

	# Calculate the body respecting the width limit
	body = [[]]
	for word in description.split(" "):
		if len(" ".join(body[-1] + [word])) + 2 + 1 >= width:
			body.append([word])
		else:
			body[-1].append(word)

	# Get the length of the longest line for the horizontal rule
	longest = 0
	for line in body:
		if len(" ".join(line)) > longest:
			longest = len(" ".join(line))

	# Add the body to the bubble
	bubble = head[:]
	for line in body:
		bubble.append("│ " + " ".join(line))

	# Finally, add the horizontal rule to the body
	bubble.append("╰" + "─"*(longest + 2))

	# Print it :D
	print("\r" + "\n".join(bubble))
	break
