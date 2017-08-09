from Queue import Queue
import argparse
import os
import subprocess
import threading
import traceback

from farmsoup.range import Range
from sgfs import SGFS


NUM_GPUS = 8

def target(args, gpu, queue):

    if args.verbose:
        print 'Starting GPU thread {}'.format(gpu)

    try:
        while True:
            x = queue.get()
            if x is None: # We're done here.
                return
            start, end = x

            cmd = ['Render',
                '-r', 'redshift',
                '-gpu', '{%d}' % gpu,
                '-s', start,
                '-e', end,
            ]
            for name in 'rd', 'proj', 'x', 'y', 'im', 'cam':
                value = getattr(args, name, None)
                if value is not None:
                    cmd.extend(('-' + name, value))

            cmd.append(args.scene)

            cmd = [str(x) for x in cmd]
            if args.verbose:
                print 'Starting {}-{} on GPU {}: {}'.format(start, end, gpu, ' '.join(cmd))
            if not args.dry_run:
                code = subprocess.call(cmd)
                if args.verbose or code:
                    print 'Done {}-{} on GPU {} with code {}'.format(start, end, gpu, code)

    except:
        print 'EXCEPTION IN GPU THREAD {}'.format(gpu)
        traceback.print_tb()


def main():

    '''
    Render -r redshift -x 1920 -y 1080 -gpu {0} -rl defaultRenderLayer  -s 65 -e 72 -b 1
        -rd "/Volumes/CGroot/Projects/Shuyan/sequences/Sq04/shots/Sq04_Sh12/light/maya/images"
        -im "<Scene>/<RenderLayer>" -cam "import:cam:MainCAM"
        -proj "/Volumes/CGroot/Projects/Shuyan/sequences/Sq04/shots/Sq04_Sh12/light/maya/scenes"
        "/Volumes/CGroot/Projects/Shuyan/sequences/Sq04/shots/Sq04_Sh12/light/maya/scenes/Sq04_Sh12,light,v0000,r0004.ma"
    '''

    parser = argparse.ArgumentParser()

    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('-n', '--dry-run', action='store_true')

    parser.add_argument('-s', type=int, required=True, help="Start frame")
    parser.add_argument('-e', type=int, required=True, help="End frame")
    parser.add_argument('-c', type=int, default=5, help="Chunk size")

    parser.add_argument('-rd')
    parser.add_argument('-proj')

    parser.add_argument('-b', help=argparse.SUPPRESS)
    parser.add_argument('-x', type=int, default=1920, help="Width")
    parser.add_argument('-y', type=int, default=1080, help="Height")
    parser.add_argument('-im', default="<Scene>/<RenderLayer>")
    parser.add_argument('-cam', help="Camera")
    parser.add_argument('-rl', help="Render Layer")

    parser.add_argument('scene')
    args = parser.parse_args()


    if args.b:
        print '-b does not work with this script!'
        exit(1)

    if not (args.rd and args.proj):
        sgfs = SGFS()
        tasks = sgfs.entities_from_path(args.scene, ['Task'])
        if len(tasks) != 1:
            print 'Cannot pick single task from scene.'
            exit(2)
        task = tasks[0]
        task_dir = sgfs.path_for_entity(task)
        args.rd = args.rd or os.path.join(task_dir, 'maya', 'images')
        args.proj = args.proj or os.path.join(task_dir, 'maya', 'scenes')

    range_ = Range('{}-{}/{}'.format(args.s, args.e, args.c))

    queue = Queue()
    threads = []
    for gpu in xrange(NUM_GPUS):
        thread = threading.Thread(target=target, args=(args, gpu, queue))
        thread.start()
        threads.append(thread)

    for chunk in range_.iter_chunks():
        start = chunk[0]
        end = chunk[-1]
        queue.put((start, end))

    if args.verbose:
        print 'Waiting for threads...'

    for thread in threads:
        queue.put(None)
    for thread in threads:
        thread.join()

    if args.verbose:
        print 'Done.'

