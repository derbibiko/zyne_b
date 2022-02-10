#!/usr/bin/env python3
"""
Send MIDI message on output port.
Run with (for example):
    ./send_midi_message.py '{message}' {channel} '{midi interface name}'


Examples:
    control message as string:
    "cc 21 60" := sends control_change controller 21 value 60 on channel {channel}


"""
import sys
import mido
from mido import MidiFile

channel = 0
midi_port = None

msg = sys.argv[1].split()
if len(sys.argv) == 3:
    channel = int(sys.argv[2]) - 1
elif len(sys.argv) == 4:
    midi_port = sys.argv[3]
    channel = int(sys.argv[2]) - 1

if midi_port is None:
    pn = mido.get_output_names()
    if len(pn) > 0:
        midi_port = pn[0]

outport_port = mido.open_output(midi_port)

if msg[0] == "cc":
    message = mido.Message('control_change', channel=channel,
                           control=int(msg[1]), value=int(msg[2]))

if message:
    outport_port.send(message)