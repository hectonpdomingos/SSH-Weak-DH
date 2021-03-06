#!/usr/bin/python -u

"""
This program analyzes the output produced by the
OpenSSH client which is patched for analyzing the
key exchange.

SSH-Weak-DH v1.1
Fabian Foerg <ffoerg@gdssecurity.com>
Ron Gutierrez <rgutierrez@gdssecurity.com>
Blog: https://blog.gdssecurity.com/labs/2015/8/3/ssh-weak-diffie-hellman-group-identification-tool.html
Copyright 2015-2017 Gotham Digital Science
"""

from __future__ import print_function

import sys
from os import listdir
from os.path import isfile, isdir, join
import re
import textwrap

DH_BITS_WEAK = 768
DH_BITS_ACADEMIC = 1024
DH_BITS_NATION = 1536
KEX_ALGO = "KEX algorithm chosen: "
DH_GROUP_BIT_CLIENT = "KEX client group sizes: "
DH_GROUP_BIT_SERVER = "KEX server-chosen group size in bits: "
DH_GROUP1 = "diffie-hellman-group1-sha1"

"""
prints a security ranking for the given Diffie-Hellman group size
in bits
"""
def dh_sec_level(dh_algo, dh_bits_client, dh_bits_server):
    print("The client proposed the following group size parameters (in bits): ",
          "min=", dh_bits_client[0], ", nbits=", dh_bits_client[1], ", max=",
          dh_bits_client[2], ".", sep='')
    print("The client and server negotiated a group size of ",
          dh_bits_server, " using ", dh_algo, ".", sep='')
    print("The security level is ", end="")
    if dh_bits_server < DH_BITS_WEAK:
        print("WEAK.")
    elif dh_bits_server < DH_BITS_ACADEMIC:
        print("WEAK-INTERMEDIATE (might be feasible to break for academic teams).")
    elif dh_bits_server < DH_BITS_NATION:
        print("INTERMEDIATE (might be feasible to break for nation-states).")
    else:
        print("STRONG.")
    print()

"""
analyze the given file, looking for Diffie-Hellman group sizes and
algorithm
"""
def analyze(f):
    lines = []
    with open(f, "r") as fb:
        lines = [line.rstrip("\n") for line in fb]
    lineno = 0
    dh_algo = ""
    dh_bits_client = (0, 0, 0)
    dh_bits_server = 0

    while lineno < len(lines):
        line = lines[lineno]
        if line.startswith(KEX_ALGO):
            dh_algo = line[len(KEX_ALGO):].strip()
            # Treat DH group1 (Oakley Group 2) individually, since it is
            # negotiated via the diffie-hellman-group1-sha1 method and not the
            # DH GEX methods (the client does not propose group sizes, since
            # the group is fixed).
            if dh_algo == DH_GROUP1:
                dh_sec_level(dh_algo, [1024, 1024, 1024], 1024)
        elif (lineno + 2) <= len(lines):
            parse_group_exchange(lines[lineno:lineno + 2], dh_algo)
        lineno += 1

"""
parses the two given lines for Diffie-Hellman group exchange parameters
"""
def parse_group_exchange(lines, dh_algo):
    assert(len(lines) == 2)

    fst = lines[0]
    snd = lines[1]

    if fst.startswith(DH_GROUP_BIT_CLIENT) and snd.startswith(DH_GROUP_BIT_SERVER):
        dh_bits_client = [int(s) for s in re.split("\s+|\s*,\s*", fst) if s.isdigit()]
        dh_bits_server = [int(s) for s in snd.split() if s.isdigit()]

        if len(dh_bits_client) == 3 and len(dh_bits_server) == 1:
            dh_sec_level(dh_algo, dh_bits_client, dh_bits_server[0])
        else:
            print("Error: Cannot parse client parameters or server group size!")

"""
analyze all files in the given directory
"""
def walk_dir(d):
    subdirs = sorted(listdir(d))
    for f in subdirs:
        path = join(d, f)
        if isfile(path):
            analyze(path)

"""
parse command-line parameters and start analysis
"""
def main():
    args = sys.argv

    if len(args) != 2:
        print("Syntax: python -u", args[0], "directory")
        exit(1)
    else:
       directory = args[1]

    if not isdir(directory):
        print("The given parameter is not a directory: ", directory)
        exit(1)

    walk_dir(directory)

    print("\n".join(textwrap.wrap("WARNING: This tool tests a limited number of configurations and therefore potentially fails to detect some weak configurations. Moreover, the server possibly blocks connections before the scan completes.")))

if  __name__ =="__main__":
    main()

