import os

from mayatools.shelf import load as _load

from maya import cmds


def setup_gui():
    load_shelf()

def load_shelf():
    cmds.scriptJob(runOnce=True, idleEvent=_load_shelf)

def _load_shelf():
    shelf_dir = os.path.abspath(os.path.join(__file__, '..'))
    image_dir = os.path.abspath(os.path.join(__file__, '..', '..', 'art', 'icons'))
    print 'Loading shelves from', shelf_dir
    _load(shelf_dir, image_roots=[image_dir])







# === BUTTONS ===

def bomb_button():
	raise ValueError("This is a test.")

def refresh_button():
	load_shelf()
