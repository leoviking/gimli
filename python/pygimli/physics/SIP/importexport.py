#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Import/Export for SIP data."""

import codecs

import numpy as np
import re


def fstring(fri):
    """Format frequency to human-readable (mHz or kHz)."""
    if fri > 1e3:
        fstr = '{:d} kHz'.format(int(np.round(fri/1e3)))
    elif fri < 1.:
        fstr = '{:d} mHz'.format(int(np.round(fri*1e3)))
    elif fri < 10.:
        fstr = '{:3.1f} Hz'.format(fri)
    elif fri < 100.:
        fstr = '{:4.1f} Hz'.format(fri)
    else:
        fstr = '{:d} Hz'.format(int(np.round(fri)))
    return fstr


def readTXTSpectrum(filename):
    """Read spectrum from ZEL device output (txt) data file."""
    fid = open(filename)
    lines = fid.readlines()
    fid.close()
    f, amp, phi = [], [], []
    for line in lines[1:]:
        snums = line.replace(';', ' ').split()
        if len(snums) > 3:
            f.append(float(snums[0]))
            amp.append(float(snums[1]))
            phi.append(-float(snums[3]))
        else:
            break

    return np.asarray(f), np.asarray(amp), np.asarray(phi)


def readFuchs3File(resfile):
    """Read Fuchs III (SIP spectrum) data file."""
    activeBlock = ''
    header = {}
    LINE = []
    dataAct = False
    with open(resfile, 'r') as f:
        for line in f:
            if dataAct:
                LINE.append(line)
                if len(line) < 2:
                    f, amp, phi = [], [], []
                    for li in LINE:
                        sline = li.split()
                        if len(sline) > 12:
                            fi = float(sline[11])
                            if np.isfinite(fi):
                                f.append(fi)
                                amp.append(float(sline[12]))
                                phi.append(float(sline[13]))

                    return np.array(f), np.array(amp), np.array(phi), header
            elif len(line):
                if line.rfind('Current') >= 0:
                    if dataAct:
                        break
                    else:
                        dataAct = True
                        print(line)
                if line[0] == '[':
                    token = line[1:line.rfind(']')].replace(' ', '_')
                    if token[:3] == 'End':
                        header[activeBlock] = np.array(header[activeBlock])
                        activeBlock = ''
                    elif token[:5] == 'Begin':
                        activeBlock = token[6:]
                        header[activeBlock] = []
                    else:
                        value = line[line.rfind(']') + 1:]
                        try:  # direct line information
                            if '.' in value:
                                num = float(value)
                            else:
                                num = int(value)
                            header[token] = num
                        except BaseException as e:
                            # maybe beginning or end of a block
                            print(e)

                else:
                    if activeBlock:
                        nums = np.array(line.split(), dtype=float)
                        header[activeBlock].append(nums)

def readRadicSIPFuchs(filename, readSecond=False, delLast=True):
    """Read SIP-Fuchs Software rev.: 070903

    Read Radic instrument res file containing a single spectrum.

    Please note the apparent resistivity value might be scaled with the
    real geometric factor. Default is 1.0.

    Parameters
    ----------
    filename : string

    readSecond: bool [False]
        Read the first data block[default] or read the second that
        consists in the file.

    delLast : bool [True]
        ??

    Returns
    -------
    fr : array [float]
        Measured frequencies

    rhoa : array [float]
        Measured apparent resistivties

    phi : array [float]
        Measured phases

    drhoa : array [float]
        Measured apparent resistivties error

    phi : array [float]
        Measured phase error
    """
    f = open(filename, 'r')
    line = f.readline()
    fr = []
    rhoa = []
    phi = []
    drhoa = []
    dphi = []
    while True:
        line = f.readline()
        if line.rfind('Freq') > -1:
            break

    if readSecond:
        while True:
            if f.readline().rfind('Freq') > -1:
                break

    while True:
        line = f.readline()
        b = line.split('\t')
        if len(b) < 5:
            break

        fr.append(float(b[0]))
        rhoa.append(float(b[1]))
        phi.append(-float(b[2]) * np.pi / 180.)
        drhoa.append(float(b[3]))
        dphi.append(float(b[4]) * np.pi / 180.)

    f.close()

    if delLast:
        fr.pop(0)
        rhoa.pop(0)
        phi.pop(0)
        drhoa.pop(0)
        dphi.pop(0)

    return np.array(fr), np.array(rhoa), np.array(phi), np.array(drhoa), np.array(dphi)


def readSIP256file(resfile, verbose=False):
    """Read SIP256 file (RES format) - mostly used for 2d SIP by pybert.sip.

    Read SIP256 file (RES format) - mostly used for 2d SIP by pybert.sip.

    Parameters
    ----------

    filename: str
        *.RES file (SIP256 raw output file)

    verbose:    bool
        do some output [False]

    Returns
    -------
        header - dictionary of measuring setup
        DATA - data AB-list of MN-list of matrices with f, Z, phi, dZ, dphi
        AB - list of current injection
        RU - list of remote units

    Examples
    --------
        header, DATA, AB, RU = readSIP256file('myfile.res', True)
    """
    activeBlock = ''
    header = {}
    LINE = []
    dataAct = False


#    with open(resfile, 'r', errors='replace') as f:
    with codecs.open(resfile, 'r', errors='replace') as f:
        for line in f:
            if dataAct:
                LINE.append(line)
            elif len(line):
                if line[0] == '[':
                    token = line[1:line.rfind(']')].replace(' ', '_')
                    if token.replace(' ', '_') == 'Messdaten_SIP256':
                        dataAct = True
                    elif 'Messdaten' in token:
                        # res format changed into SIP256D .. so we are a
                        # little bit more flexible with this.
                        dataAct = True
                    elif token[:3] == 'End':
                        header[activeBlock] = np.array(header[activeBlock])
                        activeBlock = ''
                    elif token[:5] == 'Begin':
                        activeBlock = token[6:]
                        header[activeBlock] = []
                    else:
                        value = line[line.rfind(']') + 1:]
                        try:  # direct line information
                            if '.' in value:
                                num = float(value)
                            else:
                                num = int(value)
                            header[token] = num
                        except BaseException as e:
                            # maybe beginning or end of a block
                            print(e)

                else:
                    if activeBlock:
                        nums = np.array(line.split(), dtype=float)
                        header[activeBlock].append(nums)

    # CR DATA, Data, data ?? really??
    # TG: yes, no better idea to handle blocks of blocks of data
    DATA, Data, data, AB, RU, ru = [], [], [], [], [], []
    for line in LINE:
        sline = line.split()
        if line.find('Reading') == 0:
            rdno = int(sline[1])
            if rdno:
                AB.append((int(sline[4]), int(sline[6])))
            if ru:
                RU.append(ru)
                ru = []
            if rdno > 1 and Data:
                Data.append(np.array(data))
                DATA.append(Data)
                Data, data = [], []
                if verbose:
                    print('Reading ' + str(rdno - 1) + ':' + str(len(Data)) +
                          ' RUs')
        elif line.find('Remote Unit') == 0:
            ru.append(int(sline[2]))
            if data:
                Data.append(np.array(data))
                data = []
        elif line.find('Freq') >= 0:
            pass
        elif len(sline) > 1 and rdno > 0:  # some data present
            if re.search('[0-9]-', line):  # missing whitespace before -
                sline = re.sub('[0-9]-', '5 -', line).split()

            for c in range(6):
                if len(sline[c]) > 15:  # too long line / missing space
                    if c == 0:
                        part1 = sline[c][:-15]
                        part2 = sline[c][-15:]   # [10:]
                    else:
                        part1 = sline[c][:-10]
                        part2 = sline[c][-10:]   # [11:]
                    sline = sline[:c] + [part1] + [part2] + sline[c + 1:]
            data.append(np.array(sline[:5], dtype=float))

    Data.append(np.array(data))
    DATA.append(Data)
    if verbose:
        print('Reading ' + str(rdno) + ':' + str(len(Data)) + ' RUs')

    return header, DATA, AB, RU


if __name__ == "__main__":
    pass
