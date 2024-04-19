import board
import busio
import time

import adafruit_midi
from adafruit_midi.note_on import NoteOn
from adafruit_midi.note_off import NoteOff
from adafruit_midi.pitch_bend import PitchBend
from adafruit_midi.control_change import ControlChange
from adafruit_midi.program_change import ProgramChange
from adafruit_midi.system_exclusive import SystemExclusive
from adafruit_midi.polyphonic_key_pressure import PolyphonicKeyPressure
from adafruit_midi.pitch_bend import PitchBend

import umidiparser

time_now_us = umidiparser.time_now_us

class MidiUnit:
    def __init__(self, uart=None):
        self.uart = uart or busio.UART(tx=board.D2, baudrate=31250, bits=8, parity=None, stop=1)
        self.midi = adafruit_midi.MIDI(midi_out=self.uart, out_channel=0)

    def reset(self):
        self.midi.send(SystemExclusive([0x7e, 0x7f], [0x09, 0x01])) # Reset
        # Assign part 0 (drums) to channel 15 (simply to move it further down from the default 9)
        self.midi.send(SystemExclusive([0xf0, 0x41, 0x00], [0x42, 0x12, 0x40, 0x10, 0x02, 15, 0])) 
    
    def set_master_volume(self, value: int):
        """Set master volume 0..127."""
        self.midi.send(SystemExclusive([0x7f, 0x7f, 0x04], [0x01, 0x00, value & 0x7f]))

    def stop_all_notes(self):
        """Stop all notes on all channels"""
        for c in range(0, 16):
            self.midi.send(ControlChange(123, 0), channel=c)
    
    def play_umidiparser_event(self, event: umidiparser.MidiEvent) -> None:
        """Send an event from umidiparser to the device."""
        if event.status == umidiparser.NOTE_ON:
            self.midi.send(NoteOn(note=event.note, velocity=event.velocity), channel=event.channel)
        elif event.status == umidiparser.NOTE_OFF:
            self.midi.send(NoteOff(note=event.note, velocity=event.velocity), channel=event.channel)
        elif event.status == umidiparser.PROGRAM_CHANGE:
            self.midi.send(ProgramChange(patch=event.program), channel=event.channel)
            #print("PROGRAM_CHANGE", event)
        elif event.status == umidiparser.CONTROL_CHANGE:
            self.midi.send(ControlChange(control=event.control, value=event.value), channel=event.channel)
            #print("CONTROL_CHANGE", event)
        elif event.status == umidiparser.POLYTOUCH:
            self.midi.send(PolyphonicKeyPressure(note=event.note, pressure=event.value), channel=event.channel)
        elif event.status == umidiparser.PITCHWHEEL:
            self.midi.send(PitchBend(event.pitch + 8192), channel=event.channel)
        elif event.status in [umidiparser.LYRICS, umidiparser.TEXT, umidiparser.COPYRIGHT, umidiparser.MARKER]:
            n = event._get_event_name().upper()
            print(n, " "*(15-len(n)), event.text)
        elif event.status in [umidiparser.TRACK_NAME, umidiparser.INSTRUMENT_NAME, umidiparser.PROGRAM_NAME, umidiparser.DEVICE_NAME]:
            n = event._get_event_name().upper()
            print(n, " "*(15-len(n)), event.name)
        else:
            print("OTHER", event)

class MidiPlayback:
    def __init__(self, midi_unit: MidiUnit, event_callback: 'Callable' = None):
        self.midi_unit = midi_unit
        self.current_song_iter = None
        self.song_time_offset_us = None
        self.song_midi_time_us = None
        self.last_frame_callback_us = umidiparser.time_now_us()
        self.event_callback = event_callback
        self.song_ended = False
        self.scheduled_event = None
        self.scheduled_event_time_us = None
        self.paused = False
        self.pause_started_us = None

    def _schedule_next_song_event(self) -> bool:
        try:
            event = next(self.current_song_iter)
        except StopIteration:
            self.song_ended = True
            return False
        self.song_midi_time_us += event.delta_us
        self.scheduled_event_time_us = self.song_midi_time_us + self.song_time_offset_us
        self.scheduled_event = event
        return True

    def __call__(self):
        """To be invoked in the loop.
        If an event is pending, plays it when time comes. Otherwise dequeues and plays. 
        """
        if self.paused: return
        if not self.current_song_iter: return
        if not self.scheduled_event:
            if not self._schedule_next_song_event(): return
        now = time_now_us()
        if now < self.scheduled_event_time_us:
            return
        else:
            if self.event_callback: self.event_callback(self.scheduled_event)
            self.midi_unit.play_umidiparser_event(self.scheduled_event)
            self.scheduled_event = None

    def play_song(self, filename: str):
        self.current_song_iter = iter(umidiparser.MidiFile(filename, reuse_event_object=True))
        self.song_time_offset_us = umidiparser.time_now_us()
        self.song_midi_time_us = 0
        self.song_ended = False

    def pause(self):
        self.paused = True
        self.pause_started_us = time_now_us()
        self.midi_unit.stop_all_notes()
    
    def resume(self):
        self.paused = False
        self.song_time_offset_us += (time_now_us() - self.pause_started_us)
    
    def toggle_pause(self):
        if self.paused:
            self.resume()
        else:
            self.pause()