# pymod6

[![Code style: black](https://img.shields.io/badge/code%20style-black-black.svg)](https://github.com/psf/black)

3rd-party, file-I/O-based Python interface to [MODTRAN<sup>&reg;</sup> 6][MODTRAN].

This package provides a functional wrapper to MODTRAN's command line interface. 
It allows users to run MODTRAN with a chosen input file and then read the generated output
files into Python.

Using this package requires an active MODTRAN 6 license.

# Install
Install from local source tree:
```shell
$ pip install .
```

# Tests
Tests can be run using pytest:

```shell
$ pytest
```

[MODTRAN]: http://modtran.spectral.com/
