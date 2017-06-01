
import argparse
import json

from maya import cmds, standalone

from mayatools.units import get_fps


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('scene')
    args = parser.parse_args()

    standalone.initialize()

    cmds.file(args.scene, open=True)

    out = {}

    file_info = [x.encode('utf8') for x in cmds.fileInfo(q=True)]
    out['file_info'] = dict(zip(file_info[0::2], file_info[1::2]))

    out['max_time'] = cmds.playbackOptions(query=True, maxTime=True)
    out['min_time'] = cmds.playbackOptions(query=True, minTime=True)
    out['fps'] = get_fps()
    
    out['references'] = [str(x) for x in cmds.file(query=True, reference=True) or []]

    print json.dumps(out, sort_keys=True, indent=4)

