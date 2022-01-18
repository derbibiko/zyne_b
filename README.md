# Zyne (à la Bibiko) #

Zyne (à la Bibiko) version 1.0.1 is a Python modular synthesizer using pyo as its audio engine.

Zyne (à la Bibiko) is a git fork of the **extremely outstanding** work of **Olivier Bélanger**.
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

Zyne (à la Bibiko) should run on each OS with Python >=3.6 and wxpython installed. It uses Olivier Bélanger's
pyo audio engine which has to be installed as well.

One possibl installation scenario:

- install wxpython (version 4) if not yet installed

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

- go inside the folder "zyne" and execute the Python script "Zyne.py"

`python3 Zyne.py`


## Why did I fork the original Zyne App (and pyo)##

The main reason is that I would like to add more functions that can be useful for live performances on stage.
By myself I am using macos computers (but I'm also trying to keep the other OS in mind).
Modern MIDI equipment allow to use different MIDI channels. Some ideas which should be implemented are:

- each module or set of modules listen to a specific MIDI channel

a good example if you to split your keyboard(s) or if you run more instances of Zyne

- add the possibilty to make usage of other devices (tablets, smartphone, ...) as a remote control for module parameters

as running a http server in the same network which can be reached by any device to send MIDI control commands


Another reason for forking is to update the code for Python >= 3.6 and wxPython 4.


## Contact ##

For questions and comments please mail to `mail (at) bibiko.de`
