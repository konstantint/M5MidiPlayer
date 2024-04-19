import board
import displayio
import umidiparser
from button_handler import ButtonHandler
from m5_midi_unit import MidiUnit, MidiPlayback
from midi_visualizer_screen import MidiVisualizerScreen
from playlist import MidiPlaylist


class MidiPlayerApp:
    def __init__(self, display=board.DISPLAY):
        self.midi_unit = MidiUnit()
        self.display = display
        self.display.root_group = SplashScreen()
        self.button_handler = ButtonHandler(self.on_click, board.BTN)
        self.state = "SPLASH"
        self.playlist = MidiPlaylist()
        self.visualizer = self.playback = None

    def __call__(self):
        self.button_handler()
        if self.state == "VISUALIZER":
            self.playback()
            self.visualizer()
            if self.playback.song_ended:
                self.next_song()

    def start_visualizer(self):
        self.visualizer = MidiVisualizerScreen()
        self.display.root_group = self.visualizer
        self.midi_unit.reset()
        self.midi_unit.set_master_volume(100)
        self.playback = MidiPlayback(
            midi_unit=self.midi_unit, event_callback=self.on_umidiparser_event
        )
        self.playback.play_song(self.playlist.get_current_file())
        self.visualizer.set_text(self.playlist.get_current_file_title() + " ")
        print(self.playlist.get_current_file_title())
        self.visualizer.set_subtext("Click | Double | Long")
        self.state = "VISUALIZER"

    def next_song(self):
        self.playlist.next_prev(1)
        self.start_visualizer()

    def prev_song(self):
        self.playlist.next_prev(-1)
        self.start_visualizer()
    
    def on_umidiparser_event(self, event):
        self.visualizer.handle_umidiparser_event(event)
        if event.status == umidiparser.LYRICS:
            self.visualizer.append_text(event.text)

    def on_click(self, double_click: bool, long_press: bool):
        if long_press:
            if self.state == "VISUALIZER":
                self.prev_song()
        else:
            if double_click:
                if self.state == "VISUALIZER":
                    self.next_song()
            else:
                if self.state == "SPLASH":
                    self.start_visualizer()
                else:
                    self.visualizer.toggle_pause()
                    self.playback.toggle_pause()


class SplashScreen(displayio.Group):
    def __init__(self, image="/splash.bmp"):
        super().__init__()
        bitmap = displayio.OnDiskBitmap(image)
        self.append(displayio.TileGrid(bitmap, pixel_shader=bitmap.pixel_shader))
