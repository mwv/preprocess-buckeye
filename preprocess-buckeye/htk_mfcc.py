#!/usr/bin/python
# -*- coding: utf-8 -*-

# ------------------------------------
# file: htk_mfcc.py
# date: Thu February 13 16:35 2014
# author:
# Maarten Versteegh
# github.com/mwv
# maartenversteegh AT gmail DOT com
#
# Licensed under GPLv3
# ------------------------------------
"""htk_mfcc:

"""

from __future__ import division

import os
import os.path as path
import fnmatch
import numpy as np
from subprocess import call
import tempfile
import shutil

import htkio


def rglob(rootdir, pattern):
    for root, _, files in os.walk(rootdir):
        for basename in files:
            if fnmatch.fnmatch(basename, pattern):
                yield path.join(root, basename)


def convert(infolder, outfolder, sildir=None, frate=10, verbose=None):
    if sildir is None:
        sildir = path.join(infolder, 'sil')
    tmpdir = tempfile.mkdtemp()
    if verbose:
        print 'Converting to mfcc from', infolder, 'to', outfolder
    mfc_extension = '.mfc'
    for wavfile in rglob(infolder, '*.wav'):
        basename = path.splitext(path.basename(wavfile))[0]
        if basename.startswith('._'):
            continue
        if verbose:
            print '  ', basename
        tmpwav = path.join(tmpdir, basename + '.wav')
        tmpmfc = path.join(tmpdir, basename + mfc_extension)
        outmfc = path.join(outfolder, basename + mfc_extension)
        call(['sox', wavfile, tmpwav])
        call(['HCopy', '-C', 'htk_mfcc_config', tmpwav, tmpmfc])
        reader = htkio.HTKFeat_read(tmpmfc)
        arr = reader.getall()

        silfile = path.join(sildir, basename + '.sil')
        sil_frames = np.loadtxt(silfile)
        sil_frames = 1000*np.rint(sil_frames/frate).astype(int)
        silmask = np.ones(arr.shape[0], dtype=np.bool)
        silmask[np.hstack(np.arange(sil_frames[i][0],
                                    min(arr.shape[0], sil_frames[i][1]+1),
                                    dtype=np.int)
                          for i in range(sil_frames.shape[0]))] = False
        means = np.mean(arr[silmask], axis=0)
        stds = np.std(arr[silmask], axis=0)
        arr = (arr-means) / stds
        writer = htkio.HTKFeat_write(outmfc, veclen=39,
                                     paramKind=(htkio.MFCC |
                                                htkio._O |
                                                htkio._A |
                                                htkio._D |
                                                htkio._Z))
        writer.writeall(arr)
        os.unlink(tmpwav)
        os.unlink(tmpmfc)
    shutil.rmtree(tmpdir)


if __name__ == '__main__':
    infolder = path.join(os.environ['HOME'], 'data', 'BUCKEYE')
    outfolder = path.join(os.environ['HOME'],
                          'data/output/lrec_buckeye/mfc_norm/')
    try:
        os.makedirs(outfolder)
    except OSError:
        pass
    convert(infolder, outfolder, verbose=True)
