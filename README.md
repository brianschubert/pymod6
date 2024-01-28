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

# Documentation

Build local HTML documentation:
```shell
$ cd docs
$ make html

# Open in browser (Linux) 
$ xdg-open ./html/index.html

# Open in browser (MacOS)
$ open ./html/index.html

# Open in browser (Windows)
> Invoke-Item .\html\index.html
```
Browse HTML documentation in local web server:
```shell
$ cd docs
$ make server
```


# Tests
Tests can be run using pytest:

```shell
$ pytest
```

[MODTRAN]: http://modtran.spectral.com/
