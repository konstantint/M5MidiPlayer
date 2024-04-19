import keypad
import time


class ButtonHandler:
    """Recognizes clicks, long presses and doubleclicks."""

    def __init__(
        self,
        handler,  # Callable[[double_click: bool, long_press: bool], None]
        button,  # e.g. board.BTN
        double_click_ns: int = 300_000_000,
        long_press_ns: int = 300_000_000,
    ):
        self.keys = keypad.Keys((button,), value_when_pressed=False, pull=True)
        self.long_press_ns = long_press_ns
        self.double_click_ns = double_click_ns
        self.last_pressed = 0
        self.last_released = 0
        self.double_click_started = False
        self.handler = handler

    def __call__(self):
        event = self.keys.events.get()
        if event:
            now = time.monotonic_ns()
            if event.pressed:
                self.double_click_started = (
                    now - self.last_pressed <= self.double_click_ns
                )
                self.last_pressed = now
            elif event.released:
                self.last_released = now
                if self.handler:
                    self.handler(
                        double_click=self.double_click_started,
                        long_press=now - self.last_pressed >= self.long_press_ns,
                    )
