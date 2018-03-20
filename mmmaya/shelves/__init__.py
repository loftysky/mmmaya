import os
import sys

import pkg_resources

from mayatools.shelf import load as _load

from maya import cmds


def setup_gui():
    load_shelf()

def load_shelf():
    cmds.scriptJob(runOnce=True, idleEvent=_load_shelf)

def _load_shelf():
    shelf_dir = os.path.abspath(os.path.join(__file__, '..'))
    image_dir = os.path.abspath(os.path.join(__file__, '..', '..', 'art', 'icons'))

    shelf_dirs = [shelf_dir]
    image_dirs = [image_dir]

    for ep in pkg_resources.iter_entry_points('mmmaya_shelves'):
        func = ep.load()
        func(shelf_dirs, image_dirs)

    print "Loading shelves from:"
    print '\n'.join('    ' + x for x in shelf_dirs)

    _load(shelf_dirs, image_dirs)







# === BUTTONS ===

def bomb_button():
	raise ValueError("This is a test.")

def refresh_button():
	load_shelf()
