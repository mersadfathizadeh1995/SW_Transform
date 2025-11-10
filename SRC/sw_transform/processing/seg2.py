"""SEG-2 reader (native).

Implements the logic previously in Step1seg2loadAR.py so the package no
longer depends on the legacy script.
"""

from __future__ import annotations

import struct
import numpy as np
import re


def parse_float(s: str) -> float:
    s_clean = s.replace('\x00', '').strip()
    match = re.findall(r"-?\d+\.?\d*(?:[eE][-+]?\d+)?", s_clean)
    if match:
        return float(match[0])
    return 0.0


def parse_int(s: str) -> int:
    s_clean = s.replace('\x00', '').strip()
    match = re.findall(r"-?\d+", s_clean)
    if match:
        return int(match[0])
    return 0


def load_seg2_ar(filename: str):
    with open(filename, 'rb') as f:
        def read_short():
            return struct.unpack('<h', f.read(2))[0]
        def read_ushort():
            return struct.unpack('<H', f.read(2))[0]
        def read_long():
            return struct.unpack('<l', f.read(4))[0]
        def read_ulong():
            return struct.unpack('<L', f.read(4))[0]
        def read_char():
            return struct.unpack('<b', f.read(1))[0]
        def read_uchar():
            return struct.unpack('<B', f.read(1))[0]

        fileType = read_short()
        if fileType != 14933:
            raise ValueError("Not a SEG-2 file! (fileType != 14933)")

        revNumber = read_short()
        sizeOfTracePointer = read_ushort()
        nbOfTraces = read_ushort()
        sizeOfST = read_uchar(); firstST = read_char(); secondST = read_char()
        sizeOfLT = read_uchar(); firstLT = read_char(); secondLT = read_char()
        reserved = f.read(18)
        tracePointers = [read_ulong() for _ in range(nbOfTraces)]

        f.seek(32 + sizeOfTracePointer, 0)
        offset = read_ushort()
        while offset > 0:
            f.read(offset - 2)
            offset = read_ushort()

        channel_list = np.zeros(nbOfTraces, dtype=int)
        delay_list = np.zeros(nbOfTraces, dtype=float)
        desc_list = np.zeros(nbOfTraces, dtype=float)
        gain_list = np.zeros(nbOfTraces, dtype=float)
        receiver_list = np.zeros(nbOfTraces, dtype=float)
        sampling_list = np.zeros(nbOfTraces, dtype=float)
        skew_list = np.zeros(nbOfTraces, dtype=float)
        source_list = np.zeros(nbOfTraces, dtype=float)

        trace_data = []
        for i in range(nbOfTraces):
            f.seek(tracePointers[i], 0)
            traceId = read_ushort(); sizeOfBlock = read_ushort()
            sizeOfData = read_ulong(); nbOfSamples = read_ulong()
            dataCode = read_uchar(); reserved_ = f.read(19)
            offset = read_ushort()
            while offset > 0:
                freeString = f.read(offset - 2).decode('ascii', errors='ignore')
                if "CHANNEL_NUMBER" in freeString:
                    channel_list[i] = parse_int(freeString.replace("CHANNEL_NUMBER ", ""))
                if "DELAY" in freeString:
                    delay_list[i] = parse_float(freeString.replace("DELAY ", ""))
                if "DESCALING_FACTOR" in freeString:
                    desc_list[i] = parse_float(freeString.replace("DESCALING_FACTOR ", ""))
                if "FIXED_GAIN" in freeString:
                    gain_list[i] = parse_float(freeString.replace("FIXED_GAIN ", ""))
                if "RECEIVER_LOCATION" in freeString:
                    receiver_list[i] = parse_float(freeString.replace("RECEIVER_LOCATION ", ""))
                if "SAMPLE_INTERVAL" in freeString:
                    sampling_list[i] = parse_float(freeString.replace("SAMPLE_INTERVAL ", ""))
                if "SKEW" in freeString:
                    skew_list[i] = parse_float(freeString.replace("SKEW ", ""))
                if "SOURCE_LOCATION" in freeString:
                    source_list[i] = parse_float(freeString.replace("SOURCE_LOCATION ", ""))
                offset = read_ushort()

            f.seek(tracePointers[i], 0)
            f.read(sizeOfBlock)
            raw_samples = f.read(nbOfSamples * 4)
            samples_array = np.frombuffer(raw_samples, dtype='<f4')
            trace_data.append(samples_array)

        lengths = [arr.size for arr in trace_data]
        if len(set(lengths)) != 1:
            raise ValueError("Not all traces have the same number of samples!")
        num_samples = lengths[0]
        Timematrix = np.column_stack(trace_data)
        deltat = sampling_list[0]
        delay = delay_list[0]
        TL = num_samples * deltat
        endT = TL + delay
        time = np.arange(delay, endT, deltat, dtype=float)
        if time.size > num_samples:
            time = time[:num_samples]
        Shotpoint = -source_list[0] if nbOfTraces > 0 else 0.0
        Spacing = 0.0
        if nbOfTraces >= 2:
            Spacing = abs(receiver_list[1] - receiver_list[0])
    return time, Timematrix, Shotpoint, Spacing, deltat, delay


