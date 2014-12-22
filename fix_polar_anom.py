#!/usr/bin/env python

# Fix anomalies in polar fields

# Martin Dix martin.dix@csiro.au

import numpy as np
import getopt, sys
from um_fileheaders import *
import umfile, stashvar

verbose = False
try:
    optlist, args = getopt.getopt(sys.argv[1:], 'v')
    for opt in optlist:
        if opt[0] == '-v':
            verbose = True
except getopt.error:
    print "Usage: fix_polar_anom [-v] ifile "
    sys.exit(2)

if args:
    ifile = args[0]
    
f = umfile.UMFile(ifile, 'r+')

if not f.fieldsfile:
    print "Not a UM fieldsfile"
    sys.exit(1)

if f.fixhd[FH_HorizGrid] != 0:
    print "Error - not a global grid"
    sys.exit(1)

for k in range(f.fixhd[FH_LookupSize2]):
    ilookup = f.ilookup[k]
    rlookup = f.rlookup[k]
    lbegin = ilookup[LBEGIN] # lbegin is offset from start
    if lbegin == -99:
        break

    # Determine the grid from the zeroth latitude and longitude
    if not ( np.allclose(rlookup[BZY] + rlookup[BDY], -90.) and
             np.allclose(rlookup[BZX] + rlookup[BDX], 0.) ):
        if verbose:
            print "Skipping grid", ilookup[ITEM_CODE]
        continue
    
    data = f.readfld(k)

    anom_sp = data[0,:].max() - data[0,:].min()
    anom_np = data[-1,:].max() - data[-1,:].min()
    # Reset polar values
    reset = False
    if anom_sp > 0:
        reset = True
        # With dump files using 32 bit packing, using 64 bit mean helps
        # maintain precision.
        data[0,:] = data[0,:].mean(dtype=np.float64)
    if anom_np > 0:
        reset = True
        data[-1,:] = data[-1,:].mean(dtype=np.float64)

    if reset:
        f.writefld(data,k)
        if verbose:
            print "Fixed", ilookup[ITEM_CODE], ilookup[LBLEV]

f.close()
