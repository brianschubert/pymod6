PACKAGES    := pymod6
PYTHON_EXE  := python3
PDOC_EXE    := ${PYTHON_EXE} -m pdoc
PDOC_HOST   := localhost
PDOC_PORT   := 8080

.PHONY: html http install_deps clean

html: install_deps
	${PDOC_EXE} --docformat=numpy --output-directory=html ${PACKAGES}

server: install_deps
	${PDOC_EXE} --docformat=numpy --host ${PDOC_HOST} --port ${PDOC_PORT} --no-browser ${PACKAGES}

install_deps:
	${PYTHON_EXE} -m pip install pdoc

clean:
	rm -r ./html
