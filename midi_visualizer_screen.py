import displayio
import terminalio
import time
import colorsys

import umidiparser

from adafruit_display_text import label


class MidiVisualizerScreen(displayio.Group):
    def __init__(self, height=96, width=128):
        super().__init__()
        self.height = height
        self.width = width
        self.min_note = 20
        self.n_channels = 10
        self.max_age = 10
        # The color palette will depict channel & age
        self.frame = displayio.Bitmap(
            128, height, self.n_channels * self.max_age + self.max_age
        )
        color_palette = displayio.Palette(self.n_channels * self.max_age + self.max_age)
        color_palette[0] = 0
        color_palette[1] = 0x888888  # Grey line
        for c in range(1, self.n_channels + 1):
            for a in range(self.max_age):
                color_palette[c * self.max_age + a] = colorsys.hsv_to_rgb(
                    c / self.n_channels, 1.0, a / self.max_age
                )
        self.append(
            displayio.TileGrid(self.frame, pixel_shader=color_palette, x=0, y=0)
        )
        self.text = label.Label(
            font=terminalio.FONT, text="", x=0, y=(height + 128) // 2 - 8
        )
        self.append(self.text)
        self.subtext = label.Label(
            font=terminalio.FONT,
            text="",
            x=0,
            y=(height + 128) // 2 + 8,
            color=0x555555,
        )
        self.append(self.subtext)
        # Track the status of notes via this running line
        self.cur_line = [0] * self.height
        self.cur_line_age = [0] * self.height
        # X-position of the line being shown on bitmap
        self.cur_line_pos = 0

        self.frame_updater = CallEvery(self.update_frame)

    def set_text(self, text):
        self.text.text = text

    def append_text(self, text):
        new_text = self.text.text + text
        if len(new_text) > 21:
            new_text = text
        self.text.text = new_text.replace("\n", " ")

    def set_subtext(self, text):
        self.subtext.text = text

    def handle_umidiparser_event(self, event: umidiparser.MidiEvent):
        if event.status == umidiparser.NOTE_ON:
            row = max(min(event.note - self.min_note, self.height), 0)
            self.cur_line[row] = min(event.channel + 1, self.n_channels)
            self.cur_line_age[row] = self.max_age - 1
        elif event.status == umidiparser.NOTE_OFF:
            row = max(min(event.note - self.min_note, self.height), 0)
            self.cur_line[row] = 0

    def update_frame(self):
        next_line_pos = (self.cur_line_pos + 1) % self.width
        next_line2_pos = (next_line_pos + 1) % self.width
        for i in range(self.height):
            self.frame[next_line_pos, i] = 0
            self.frame[next_line2_pos, i] = 1
            self.frame[self.cur_line_pos, self.height - 1 - i] = (
                self.cur_line[i] * self.max_age + self.cur_line_age[i]
            )
            if self.cur_line_age[i] > 0:
                self.cur_line_age[i] -= 1
                if self.cur_line_age[i] == 0:
                    self.cur_line[i] = 0
        self.cur_line_pos = (self.cur_line_pos + 1) % self.width

    def __call__(self):
        self.frame_updater()

    def toggle_pause(self):
        self.frame_updater.toggle_pause()


class CallEvery:
    """Calls a given function every x nanoseconds."""

    def __init__(self, callback, interval_ns: int = 50_000_000):
        self.interval_ns = interval_ns
        self.last_call_ns = time.monotonic_ns()
        self.callback = callback
        self.paused = False

    def __call__(self):
        if self.paused:
            return
        now = time.monotonic_ns()
        if now - self.last_call_ns > self.interval_ns:
            self.callback()
            self.last_call_ns = now

    def toggle_pause(self):
        self.paused = not self.paused
