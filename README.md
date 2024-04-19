# Midi player for M5Stack [AtomS3](https://shop.m5stack.com/products/atoms3-dev-kit-w-0-85-inch-screen) + [Synth Unit](https://docs.m5stack.com/en/unit/Unit-Synth)


## Usage
* Install [CircuitPython 9 firmware](https://circuitpython.org/board/m5stack_atoms3_lite/) onto the AtomS3.
* Copy the contents of this directory to the MCU's filesystem.
* Populate the `/mid` directory with MIDI files.
* Attach the Synth unit to the MCU with a Grove cable & power the MCU.
* The result should look somewhat [like that](https://www.youtube.com/watch?v=JEpDJCvkeEI).
* You may want to tune the `set_master_volume` line in `midi_player_app.py` - so far there's no UI way of changing it.


## License
* The project's original code is MIT Licensed (Copyright 2024, Konstantin Tretyakov)
* The project incorporates code from the [umidiparser](https://github.com/bixb922/umidiparser) project by Hermann Paul von Borries, which is MIT-licensed. 
* The project relies on [CircuitPython](https://circuitpython.org/) and several Adafruit's CircuitPython libraries (bundled in the repository). These are all are MIT-licensed.
