.. _installation:

Installation instructions
=========================

Non-python dependencies
-----------------------
Scaper has two non-python dependencies:

- SoX: http://sox.sourceforge.net/
- FFmpeg: https://ffmpeg.org/

On macOS these can be installed using `homebrew <https://brew.sh/>`_:

>>> brew install sox
>>> install ffmpeg

On linux you can use your distribution's package manager, e.g. on Ubuntu (15.04 "Vivid Vervet" or newer):

>>> sudo apt-get install sox
>>> sudo apt-get install ffmpeg

NOTE: on earlier versions of Ubuntu `ffmpeg may point to a Libav binary <http://stackoverflow.com/a/9477756/2007700>`_
which is not the correct binary. If you are using anaconda, you can install the correct version by calling:

>>> conda install -c conda-forge ffmpeg

Otherwise, you can `obtain a static binary from the ffmpeg website <https://ffmpeg.org/download.html>`_.

On windows you can use the provided installation binaries:

- SoX: https://sourceforge.net/projects/sox/files/sox/
- FFmpeg: https://ffmpeg.org/download.html#build-windows

Installing Scaper
-----------------
The simplest way to install ``scaper`` is by using ``pip``, which will also install the required dependencies if needed.
To install ``scaper`` using ``pip``, simply run

>>> pip install scaper

To install the latest version of scaper from source:

1. Clone or pull the lastest version:

>>> git clone git@github.com:justinsalamon/scaper.git

2. Install using pip to handle python dependencies:

>>> cd scaper
>>> pip install -e .

Generating documentation
------------------------
You need three additional packages to generate the documentation:

>>> pip install sphinx sphinx_rtd_theme sphinx_issues
>>> cd docs/
>>> make html

The docs are now in the ``docs/_build/html`` directory.
