#!/usr/bin/env python3

from subprocess import Popen, PIPE, STDOUT, STDERR
import os
from shlex import shlex, quote
import sys
import re
import fileinput
import lsb_release

if not os.geteuid() == 0:
    sys.exit("\nOnly root can run this script\n")

popen_args = {
    universal_newlines: True,
    stdout: PIPE,
    stderr: STDOUT,
}

# decide repo to use
distribution = lsb_release.get_distro_information().get("ID", "debian")
repo = lsb_release.get_distro_information().get("CODENAME", "testing")

# Do not translate!
environ = os.environ
environ['LC_ALL'] = "C"

print("Searching for fastest mirrors...")
p = Popen(
    [
        "/usr/bin/netselect-apt", repo, "-n", "-s",
        "-o /etc/apt/sources.list.d/sources_testing.list"
    ],
    **popen_args,
    env=environ)

mirrors = []
state = "fastest"
#  while(True):
for line in p.stdout.readlines():
    if state == "fastest" and "fastest" in line:
        state = "http"
    elif state == "http":
        match = re.match("\s*(http\S+)", line)
        if match:
            mirrors.append(match.group(1))
            print(match.group(1))
        elif "Of the hosts" in line:
            state = "finished"


def judge_mirror(entry):
    """
    Accept an entry, and depending on whether it looks like a mirror netselect would
    know, replace it with the fastest mirror set or leave it alone.
    """
    if entry is None:
        return (entry, False)

    # the members are separated by a comma or a quoted space
    lead = entry.partition(',')[0].partition(' ')[0]
    if lead.endswith('/'):
        lead = lead[:-2]
    if lead.endswith(distribution):
        return (','.join(mirrors), True)
    else:
        return (entry, False)


found_mirrors = False
in_mirrors = False
mirror_toks = []
advert = '# Mirrors found with sftl/af_mirrors.py\n'

for line in fileinput.input("/etc/apt-fast.conf", inplace=True):
    # We try to parse it almost right with shlex.
    ts = shlex(line, posix=True)
    if not in_mirrors:
        if ts.get_token() == 'MIRRORS' and ts.get_token(
        ) == '=' and ts.get_token() == '(':
            if found_mirrors == True:
                sys.stderr.write("Got more than one MIRRORS?")

            in_mirrors = True
            found_mirrors = True

            buf = advert + 'MIRRORS=('
            mirror_entry = tokens.get_token()
            mirror_entry, _ = judge_mirror(mirror_entry)
            if mirror_entry is not None:
                buf += quote(mirror_entry)
            print(buf)
        else:
            sys.stdout.write(line)
            continue
    else:
        for tok in tokens:
            if tok != ')':
                mirror_toks.append(tok)
            else:
                # finish the buffer
                sys.stdout.write(' '.join(
                    quote(judge_mirror(m)[0]) for m in mirror_toks))
                print(')')
                mirror_toks = []
                in_mirrors = False

if not found_mirrors:
    print("couldn't find MIRRORS var, adding at the end")
    with open("/etc/apt-fast.conf", "a") as myfile:
        myfile.write('{0}MIRRORS=({1})'.format(advert, quote(
            ','.join(mirrors))))

# unstable experimental
# -o /home/stefan/sources_{0}.list
