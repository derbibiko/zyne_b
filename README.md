# Zyne_B #

Zyne_B version 1.0.1 is a Python modular synthesizer using pyo as its audio engine.

Zyne_B is a git fork of the **extremely outstanding** work of **Olivier Bélanger**.
The original Zyne code is hosted at [https://github.com/belangeo/zyne](https://github.com/belangeo/zyne) and
pyo code at [https://github.com/belangeo/pyo](https://github.com/belangeo/pyo).

Zyne comes with more than 10 builtin modules implementing different kind of 
synthesis engines and provides a simple API to create your own custom modules.

Tutorial on how to create a custom Zyne module:
[Tutorial](https://github.com/belangeo/zyne/blob/wiki/CustomModule.md)

A little sampler, written in pyo, that can be used to play exported soundfiles:
[SimpleSampler.py](https://github.com/belangeo/zyne/blob/master/scripts/SimpleSampler.py)

If you want to share your own modules with other users, send it by email to 
belangeo(at)gmail.com and it will be added to the download repository.


## Installation ##

Zyne_B should run on each OS with Python >= 3.6 and wxpython >= 4.1 installed. It uses Olivier Bélanger's
pyo audio engine which has to be installed as well.

One possibl installation scenario:

- install wxpython (version 4.1) if not yet installed

`pip3 install wxpython`

For Linux users (esp. Ubuntu) please refer to the [this site](https://extras.wxpython.org/wxPython4/extras/linux/gtk3/)
and pick a matching package URL, e.g. for Ubuntu 20.04 `https://extras.wxpython.org/wxPython4/extras/linux/gtk3/ubuntu-20.04/`

`python3 -m pip install -U -f https://extras.wxpython.org/wxPython4/extras/linux/gtk3/ubuntu-20.04 wxPython`

- make a new folder
- go inside that folder clone the following packages:

`git clone https://github.com/Bibiko/pyo.git`

`git clone https://github.com/Bibiko/zyne.git`

- go inside the folder "pyo" and build it

`python3 setup.py install --use-double`

For Linux users (esp. Ubuntu) install libsndfile1-dev, portaudio19-dev, libportmidi-dev, liblo-dev, and python3-pyaudio first, then run

`python3 setup.py install --use-double --user`

If building pyo fails one can try to install the original pyo package via

`pip3 install pyo`

- go inside the folder "zyne" and execute the Python script "Zyne.py"

`python3 Zyne.py`

### Linux notes ###

If Zyne.py cannot start due to audio settings it could be useful to install jackd2 and start it
via `jack_control start` first (but do not use it). In addition to set the Sample Rate 48kHz could fix an issue as well.


### How to create a macos App ###

- install `pyinstaller`

`pip3 install pyinstaller`

- execute the following command from Zyne's root directory

`./scripts/builder_pyinstaller_macos.sh`

- you find the app in folder "dist" as "Zyne_B.app"


## Why did I fork the original Zyne App (and pyo) ##

The main reason is that I would like to add more functions that can be useful for live performances on stage.
By myself I am using macos computers (but I'm also trying to keep the other OS in mind).
Modern MIDI equipment allow to use different MIDI channels. Some ideas which should be implemented are:

- each module or set of modules listen to a specific MIDI channel

a good example if you to split your keyboard(s) or if you run more instances of Zyne

- add the possibilty to make usage of other devices (tablets, smartphone, ...) as a remote control for module parameters

as running a http server in the same network which can be reached by any device to send MIDI control commands

- parameters controlled by played note velocity and frequency

e.g. longer release time for lower notes or change modulation based on MIDI note velocity


## Contact ##

For questions and comments please mail to `mail (at) bibiko.de`

