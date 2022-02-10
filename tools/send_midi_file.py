#!/usr/bin/env python3
"""
Play MIDI file on output port.
Run with (for example):
    ./send_midi_file.py '{file}.mid' {channel} '{midi interface name}'
"""
import sys
import mido
import time
from mido import MidiFile

channel = 0
midi_port = None

filename = sys.argv[1]
if len(sys.argv) == 3:
    channel = int(sys.argv[2]) - 1
elif len(sys.argv) == 4:
    midi_port = sys.argv[3]
    channel = int(sys.argv[2]) - 1

if midi_port is None:
    pn = mido.get_output_names()
    if len(pn) > 0:
        midi_port = pn[0]

midifile = MidiFile(filename)
print(f'Type: {midifile.type} - Ticks per Beat: {midifile.ticks_per_beat} - {len(midifile.tracks)} tracks')
for i, track in enumerate(midifile.tracks):
    print('Track {}: {}'.format(i, track.name))

with mido.open_output(midi_port) as output:
    try:
        t0 = time.time()
        for m in midifile.play():
            m.channel = channel
            m_ = vars(m)
            for k, v in m_.items():
                if k == 'channel':
                    v = v + 1
                elif k == 'type':
                    k = ''
                elif k == 'time':
                    v = f'{v:.5f}'
                print(f'{k}: {v}  ', end = '')
            print()
            output.send(m)
        print(f'play time: {(time.time() - t0):.2f}s (expected {midifile.length:.2f}s)')

    except KeyboardInterrupt:
        print()
        output.reset()