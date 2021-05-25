#!/bin/bash
# # Command of the day
# Version 3, much wow. I guess I can't code consistently huh.
# Well anyway, this is *supposed* to print the description of a random command :P
#
# > alek3y, 24 May 2021;

readonly COMMAND_MAX_LENGTH=10
readonly COLORS=(31 32 33 34 35 36)		# Red, Green, Yellow, Blue, Magenta, Cyan

readonly ORIGINAL_IFS="$IFS"
IFS=$'\n'		# Set array separators to newline

function safe_exit {
	IFS="$ORIGINAL_IFS"		# Restore original field separator
	exit $@
}

function repeat {
	placeholder=$(printf "%*s" $1)
	printf "%s" ${placeholder// /$2}
}

# Ensure the `whatis` command exists
function whatis {
	man -f $@
}

# Find the directories where man pages are stored
which manpath >/dev/null 2>&1
if [[ $? != 0 ]]; then
	if [[ -n "$PREFIX" ]]; then
		MANDIR="$PREFIX/share/man"		# Use termux prefix
	else
		if [[ -d /usr/share/man ]]; then
			MANDIR="/usr/share/man"
		else
			printf "Couldn't find any man pages directory\n" >&2
			safe_exit 1
		fi
	fi
else
	MANDIR=$(manpath)
fi
MANDIRS=($(printf $MANDIR | tr ":" "\n"))

# Find all the available pages (with filtering)
pages_dupes=()
for dir in ${MANDIRS[@]}; do
	pages_dupes+=($(
		find $dir \
			-type f \
			-iname "*.gz" \
			-not -iname ".*" \
			\
			-not -iname "*_*" -not -iname "*-*" \
			-not -ipath "*man2*" \
			-not -ipath "*man3*" \
			\
			-printf "%f\n" \
		| sed -E 's/\.[0-9]+.*\.gz$//'
	))
done

pages=($(printf "%s\n" "${pages_dupes[@]}" | sort -u))		# Make pages unique
pages_len=${#pages[@]}

while true; do

	# Chose a random page
	page_index=$(shuf -i 0-$(($pages_len-1)) | head -n 1)
	page_chosen=${pages[$page_index]}
	#page_chosen=diff3		# TODO: Handle '(unknown subject)'
	#page_chosen=enc2xs		# FIXME: There is a '-' at the start (why?)

	if [[ ${#page_chosen} -ge $COMMAND_MAX_LENGTH ]]; then
		continue
	fi

	whatis_page=$(whatis -l $page_chosen 2>/dev/null)

	# Retry command without `-l` if it fails.. Why termux?
	if [[ $? != 0 ]]; then
		whatis_page=$(COLUMNS=1000 whatis $page_chosen 2>/dev/null)		# Try to fix long lines with the COLUMNS var.. >:(
	fi

	# When it fails assume the page doesn't exists (happend once.. wth?)
	if [[ $? != 0 ]]; then
		continue
	fi

	raw_description=$(printf "%s\n" "$whatis_page" | awk -F " - " '{print $NF; exit}' | sed 's/\.$//')		# Remove '.' at the end of the line

	# Check if the output is going to be truncated
	columns=$(tput cols)
	if [[ $((${#raw_description}+3)) -ge $columns ]]; then
		continue
	fi

	description="$(printf ${raw_description:0:1} | tr [:lower:] [:upper:])$(printf ${raw_description:1})"		# Capitalize
	title=$(printf $page_chosen | sed 's/./& /g' | head -c -1)		# Add a space between each letter

	# Choose a random color for the title
	color_index=$(shuf -i 0-$((${#COLORS[@]}-1)) | head -n 1)
	color_chosen=${COLORS[$color_index]}

	# Bubble setup
	title_border=$(repeat ${#title} "─")
	description_border=$(repeat ${#description} "─")

	printf "╭──%s──╮\n" $title_border
	printf "│  %b%s%b  │\n" "\e[1m\e[${color_chosen}m" $title "\e[0m"		# Make the title bold and colored
	printf "├──%s──╯\n" $title_border
	printf "│ %s\n" $description
	printf "╰─%s─\n" $description_border

	break
done

safe_exit 0
