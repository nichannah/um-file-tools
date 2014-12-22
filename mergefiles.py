#!/usr/bin/env python

# Merge two UM fieldsfiles
# All fields are merged, so for finer control subset the files separately
# first. Basic header information is taken from the first file.
# Duplicate fields are also from the first file.

# Martin Dix martin.dix@csiro.au

import numpy as np
import getopt, sys
import umfile
from um_fileheaders import *

def usage():
    print "Usage: mergefiles.py -file1 file2 outputfile"
    sys.exit(2)

vlist = []
xlist = []
nfields = 9999999999
prognostic = False

if len(sys.argv) != 4:
    print "Missing filename arguments"
    usage()

f1 = umfile.UMFile(sys.argv[1])

f2 = umfile.UMFile(sys.argv[2])

g = umfile.UMFile(sys.argv[3], "w")
g.copyheader(f)

print "Lookup sizes", f1.fixhd[FH_LookupSize2], f1.fixhd[FH_LookupSize1], \
    f2.fixhd[FH_LookupSize2], f2.fixhd[FH_LookupSize1]

g.ilookup[:] = -99 # Used as missing value

# Start of data is at fixhd[FH_DataStart], 
# This should be a multiple of 2048 + 1
# Start of lookup table fixhd[FH_LookupStart]
min_dstart = g.fixhd[FH_LookupStart] + np.prod(olookup.shape)
dstart = (min_dstart//2048 + 1)*2048 + 1
g.fixhd[FH_DataStart] = dstart

# # Should pad g up to the start?
# # Check space
# space = dstart - g.fixhd[FH_LookupStart]
# print "Offsets 1",  f1.fixhd[FH_LookupStart], f1.fixhd[FH_DataStart]
# print "Offsets 2",  f2.fixhd[FH_LookupStart], f2.fixhd[FH_DataStart]
# print space, (f1.fixhd[FH_LookupSize2] + f2.fixhd[FH_LookupSize2])*f1.fixhd[FH_LookupSize1]
                                                                    
k1=0
k2=0
kout = 0
kount = dstart-1 # dstart is index rather than offset
nprog = 0
ntracer = 0
end1 = False
end2 = False

while True:
    print "K", k1, k2, kout
    if k1 >= f1.fixhd[FH_LookupSize2] or f1.ilookup[k1][LBEGIN]==-99:
        end1 = True
    if k2 >= f2.fixhd[FH_LookupSize2] or f2.ilookup[k2][LBEGIN]==-99:
        end2 = True
    
    if end1 and end2:
        break
    if end1:
        f = f2
        k = k2
        k2 += 1
    elif end2:
        f = f1
        k = k1
        k1 += 1
    else:        
        if f1.ilookup[k1][ITEM_CODE] == f2.ilookup[k2][ITEM_CODE]:
            print "Warning - duplicate", f1.ilookup[k1][ITEM_CODE]
            f = f1
            k = k1
            k1 += 1
            k2 += 1
        elif f1.ilookup[k1][ITEM_CODE] < f2.ilookup[k2][ITEM_CODE]:
            f = f1
            k = k1
            k1 += 1
        else:
            f = f2
            k = k2
            k2 += 1

    g.ilookup[kout] = f.ilookup[k]
    g.rlookup[kout] = f.rlookup[k]

    data = f.readfld(k,raw=True)
    g.writefld(data,kout,raw=True)
    kout += 1
    if umfile.isprog(ilookup):
        nprog += 1
        if umfile.istracer(ilookup):
            ntracer += 1

# This sort of correction should be in a new function?

# To get correct number of tracer fields need to divide by number of levels
ntracer /= g.inthead[IC_TracerLevs]

g.fixhd[FH_LookupSize2] = kout
g.fixhd[FH_NumProgFields] = nprog
g.inthead[IC_TracerVars] = ntracer
if ntracer > 0 and g.inthead[IC_TracerLevs] != g.inthead[IC_PLevels]:
    g.inthead[IC_TracerLevs] = g.inthead[IC_PLevels]

g.close()
