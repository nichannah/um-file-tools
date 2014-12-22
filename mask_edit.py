# Plot a land mask and interactively flip points. Output a list
# of changes.

# For a global grid need to work around quirks of iris treating 
# longitude range as -180 to 180

import iris
import iris.plot as iplt
import matplotlib
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import argparse, sys

parser = argparse.ArgumentParser(description="Interactvely edit a UM lans-sea mask")
parser.add_argument('-v', '--verbose', dest='verbose', action='store_true', 
                    default=False, help='verbose output')

parser.add_argument('-i', dest='maskfile', required=True, help='Input mask file')
parser.add_argument('-m', dest='mapres', required=False, default='m', help='Map resolution (l, m, h)')
parser.add_argument('-o', dest='outfile', help='Output file for corrections (default is standard out)')

args = parser.parse_args()

mask = iris.load_cube(args.maskfile)

global fmask, lon, lat, nlon, nlat, cyclic, changed
# Global files have latitude, longitude, 
# LAMs have grid_latitude, grid_longitude
lat, lon = mask.dim_coords
nlat, nlon = mask.shape
cyclic = lon.points[0] == 0 and abs(lon.points[-1] + lon.points[1] - 360.) < 1e-4

if mask.data.min() < 0:
    # Plots better when flipped
    mask.data = -1*mask.data

cmap = matplotlib.colors.ListedColormap(((0.7,0.7,1),(0,0.5,0)))

changed = False

if cyclic:
    ax = plt.axes(projection=ccrs.PlateCarree(central_longitude=180))
global PM
PM = iplt.pcolormesh(mask,cmap=cmap)

if args.mapres == 'l':
    plt.gca().coastlines(resolution='110m')
elif args.mapres == 'h':
    plt.gca().coastlines(resolution='10m')
else:
    plt.gca().coastlines(resolution='50m')

# Make a copy so can see what's changed later
# (PM.set_array alters mask.data for LAMs)
origmask = np.array(mask.data[:])

# From the image_zcoord example
def format_coord(x, y):

    global lon, lat, cyclic
    if cyclic:
        x += 180.
    i = lon.nearest_neighbour_index(x)
    j = lat.nearest_neighbour_index(y)
    return 'lon=%1.4f, lat=%1.4f, [%d,%d]'%(x, y, j, i)

plt.gca().format_coord = format_coord

# http://matplotlib.org/1.3.1/users/event_handling.html
def onclick(event):
    # Disable click events if using the zoom & pan modes.
    # Need to turn off zoom to restore the clicking
    if plt.gcf().canvas.widgetlock.locked():
        return
    if args.verbose:
        print 'button=%d, x=%d, y=%d, xdata=%f, ydata=%f' % (
            event.button, event.x, event.y, event.xdata, event.ydata)
    global fmask, lon, lat, PM, nlon, nlat, changed
    if cyclic:
        # Underlying plot still starts at -180, so fix the coordinate offset
        i = lon.nearest_neighbour_index(event.xdata+180)
    else:
        i = lon.nearest_neighbour_index(event.xdata)
    j = lat.nearest_neighbour_index(event.ydata)
    changed = True
    fmask = PM.get_array()
    if cyclic:
        fmask.shape = (nlat,nlon+1)
    else:
        fmask.shape = (nlat,nlon)
    if fmask[j,i] == 1:
        fmask[j,i] = 0
    else:
        fmask[j,i] = 1
#   http://wiki.scipy.org/Cookbook/Matplotlib/Animations
    PM.set_array(fmask[:,:].ravel())
    plt.draw()
    
cid = plt.gcf().canvas.mpl_connect('button_press_event', onclick)
plt.show()

if changed:

    if cyclic:
        # Remove the extra longitude
        fmask = fmask[:,:-1]

    # Now save a list of the changed points for CAP
    print "Number of points changed", np.sum(fmask != origmask)

    # Need to flip the order here to N-S.
    orig = origmask[::-1].ravel()
    new = fmask[::-1].ravel()

    if args.outfile:
        outfile = open(args.outfile,'w')
    else:
        outfile=sys.stdout
    for k in range(len(orig)):
        if orig[k] != new[k]:
            if new[k] == 0:
                status = ".FALSE."
            else:
                status = ".TRUE."
            outfile.write("&DATAC FIELD_NO=1, POINT_NO=%d, DATA_NEW=%s /\n" % \
                     (k+1, status))
