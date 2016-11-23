#! /usr/bin/env python
# This file is part of the Astrometry.net suite.
# Licensed under a 3-clause BSD style license - see LICENSE
from __future__ import print_function
from __future__ import absolute_import
import os
import sys
import logging
from optparse import OptionParser
import numpy
try:
    import pyfits
except ImportError:
    try:
        from astropy.io import fits as pyfits
    except ImportError:
        raise ImportError("Cannot import either pyfits or astropy.io.fits")
from numpy import *
from numpy.random import rand
from astrometry.util.fits import pyfits_writeto

# Returns a numpy array of booleans
def hist_remove_lines(x, binwidth, binoffset, logcut):
    bins = -binoffset + arange(0, max(x)+binwidth, binwidth)
    (counts, thebins) = histogram(x, bins)

    # We're ignoring empty bins.
    occupied = nonzero(counts > 0)[0]
    noccupied = len(occupied)
    k = (counts[occupied] - 1) 
    mean = sum(k) / float(noccupied)
    logpoisson = k*log(mean) - mean - array([sum(arange(kk)) for kk in k])
    badbins = occupied[logpoisson < logcut]
    if len(badbins) == 0:
        return array([True] * len(x))

    badleft = bins[badbins]
    badright = badleft + binwidth

    badpoints = sum(array([(x >= L)*(x < R) for (L,R) in zip(badleft, badright)]), 0)
    return (badpoints == 0)


def removelines(infile, outfile, xcol='X', ycol='Y', ext=1, cut=None, **kwargs):
    if cut is None:
        cut = 100
    p = pyfits.open(infile)
    xy = p[ext].data
    hdr = p[ext].header
    if xy is None:
        print('removelines.py: Input file contains no sources.')
        pyfits_writeto(p, outfile)
        return 0
    
    x = xy.field(xcol)
    y = xy.field(ycol)

    if len(x) == 0:
        print('removelines.py: Your FITS file contains 0 sources (rows)')
        pyfits_writeto(p, outfile)
        return 0
    
    ix = hist_remove_lines(x, 1, 0.5, logcut=-cut)
    iy = hist_remove_lines(y, 1, 0.5, logcut=-cut)
    I = ix * iy
    xc = x[I]
    yc = y[I]
    print('removelines.py: Removed %i sources' % (len(x) - len(xc)))

    p[ext].header.add_history('This xylist was filtered by the "removelines.py" program')
    p[ext].header.add_history('to remove horizontal and vertical lines of sources')
    p[ext].header['REMLINEN'] = (len(x) - len(xc), 'Number of sources removed by "removelines.py"')

    p[ext].data = p[ext].data[I]
    pyfits_writeto(p, outfile)

    return 0

def main():
    parser = OptionParser(usage='%prog [options] <input-xylist> <output-xylist>')

    parser.add_option('-X', dest='xcol', help='Name of X column in input table')
    parser.add_option('-Y', dest='ycol', help='Name of Y column in input table')
    parser.add_option('-s', dest='cut', type='float', help='Significance level to cut at (default 100)')
    parser.add_option('-e', dest='ext', type=int, help='FITS extension to read',
                      default=1)
    parser.set_defaults(xcol='X', ycol='Y', cut=None)

    (opt, args) = parser.parse_args()
    
    if len(args) != 2:
        parser.print_help()
        print()
        print('Got arguments:', args)
        sys.exit(-1)

    infile = args[0]
    outfile = args[1]
    return removelines(infile, outfile, xcol=opt.xcol, ycol=opt.ycol,
                       cut=opt.cut, ext=opt.ext)

if __name__ == '__main__':
    sys.exit(main())
