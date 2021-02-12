#!/usr/bin/env python

# Analyze results from the ITC as returned by itcselenium_tests.py

from __future__ import print_function
import os
import numpy as np
import matplotlib.pylab as plt
from astropy.io import ascii
# from lxml import html
# from bs4 import BeautifulSoup
import re

home = os.environ['HOME']

# The root directory for the output files.
# This much match the path given to SetLog and the Testing flag => Prod or Test
rootdir = home + '/tmp/Prod/'


# Print total required program time
def itcprogtime(rootdir, itchtml):
    # Total time required
    with open(rootdir+itchtml) as fp:
        itcresults = fp.read()

    itottime = itcresults.find('Program time')
    # print(itottime, itcresults[itottime:itottime+50])
    istart = itcresults[itottime:itottime+100].find('<b>') + 3
    iend = itcresults[itottime+istart:itottime+istart+100].find('</b>')
    print('Program Time:', itcresults[itottime+istart:itottime+istart+iend])


# Print imaging SNR
def imagingsnr(rootdir, itchtml):
    with open(rootdir + itchtml) as fp:
        itcresults = fp.read()

    # Single exposure
    exp_snrs = []
    regpattern = re.compile('Intermediate S/N for one exposure = ')
    matches = re.finditer(regpattern, itcresults)
    for match in matches:
        ii = itcresults[match.end():match.end() + 20].find('<')
        # print(itcresults[match.end():match.end()+ii-1])
        exp_snrs.append(float(itcresults[match.end():match.end() + ii - 1]))
    print('S/N ratios per exposure: ', exp_snrs)
    print('Mean S/N per exposure: {:7.2f}'.format(np.mean(exp_snrs)))

    # Total SNR for sequence
    tot_snrs = []
    regpattern = re.compile('S/N for the whole observation = ')
    matches = re.finditer(regpattern, itcresults)
    for match in matches:
        ii = itcresults[match.end():match.end() + 100].find('(')
        # print(itcresults[match.end():match.end()+ii-1])
        tot_snrs.append(float(itcresults[match.end():match.end() + ii - 1]))
    print('Total S/N ratios: ', tot_snrs)
    print('Mean Total S/N: {:7.2f}'.format(np.mean(tot_snrs)))


# Test 1 - spectroscopy
print('Test 1 - GMOS spectroscopy')
filename = 'Test1-final.dat'

final = ascii.read(rootdir+filename, names=['wav', 'snrtot'], guess=False, format='tab',
                   data_start=2, comment='#')

# Where to calculate the mean and total S/N
wavmin = 640.
wavmax = 680.
ii = np.where(np.logical_and(np.logical_and(final['wav'] >= wavmin, final['wav'] < wavmax), final['snrtot'] > 0.0))[0]
# print(ii)

print('Average S/N: {:7.2f}'.format(np.average(final['snrtot'][ii])))
print('Sum S/N: {:7.2f}'.format(np.sum(final['snrtot'][ii])))

itcprogtime(rootdir, 'Test1-output.html')

plt.plot(final['wav'], final['snrtot'])
plt.xlim(500,850)
plt.plot(final['wav'][ii], final['snrtot'][ii], 'red')
plt.show()


# Test 3 - imaging
print('')
print('Test 3 - GMOS imaging')
filename = 'Test3-output.html'

imagingsnr(rootdir, filename)

itcprogtime(rootdir, filename)


# Test 6 - imaging
print('')
print('Test 6 - GSAOI imaging')
filename = 'Test6-output.html'

imagingsnr(rootdir, filename)

itcprogtime(rootdir, filename)







