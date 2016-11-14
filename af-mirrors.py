from subprocess import Popen, PIPE, STDOUT
import os
import sys
import re
import fileinput

if not os.geteuid() == 0:
    sys.exit("\nOnly root can run this script\n")

repo = "testing"

p = Popen(["/usr/bin/netselect-apt", repo, "-n", "-s",
          "-o /etc/apt/sources.list.d/sources_testing.list"],
          universal_newlines=True,
          stdout=PIPE, stderr=STDOUT)

print("Searching for fastest mirrors...")

i = 0
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

#  print(mirrors)

found_mirrors = False
for line in fileinput.input("/etc/apt-fast.conf", inplace=True):
    match = re.match("MIRRORS\s*=\s*\[", line)
    if match:
        found_mirrors = True
        print("MIRRORS={0!s}".format(mirrors))
    else:
        sys.stdout.write(line)

if not found_mirrors:
    print("couldn't find MIRRORS var, adding at the end")
    with open("/etc/apt-fast.conf", "a") as myfile:
        myfile.write("\n\n# This mirrors are found with sftl/af_mirrors.py\n")
        myfile.write("MIRRORS={0!s}".format(mirrors))


# unstable experimental
# -o /home/stefan/sources_{0}.list


