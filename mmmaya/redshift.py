from Queue import Queue
import argparse
import os
import subprocess
import threading
import traceback

from farmsoup.range import Range
from farmsoup.utils import shell_quote
from sgfs import SGFS



def get_command(args, start, end, gpu, shell=False):

    cmd = ['Render',
        '-r', 'redshift',
        # These are purposefully not shell_quote-ed!
        '-gpu', '{%s}' % gpu,
        '-s', start,
        '-e', end,
    ]

    for name in 'rd', 'proj', 'x', 'y', 'im', 'cam', 'rl', 'skipExistingFrames':
        value = getattr(args, name, None)
        if value is not None:
            if shell:
                value = shell_quote(str(value))
            cmd.extend(('-' + name, value))

    cmd.append(shell_quote(args.scene) if shell else args.scene)

    cmd = [str(x) for x in cmd]

    return cmd


def target(args, gpu, queue):

    if args.verbose:
        print 'Starting GPU thread {}'.format(gpu)

    try:
        while True:
            x = queue.get()
            if x is None: # We're done here.
                return
            start, end = x

            cmd = get_command(args, start, end, gpu)

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

    parser.add_argument('-V', '--version', type=int, default=2016,
        help="Maya version; 2016 or 2018.")

    parser.add_argument('-s', '--start', type=int, required=True, help="Start frame")
    parser.add_argument('-e', '--end', type=int, required=True, help="End frame")

    local_group = parser.add_argument_group('Local settings')
    local_group.add_argument('-c', '--chunk', type=int, default=5, help="Chunk size")
    local_group.add_argument('-g', '--gpus', metavar='N_GPUS', type=int, default=8, help="Number of local GPUs")

    farm_group = parser.add_argument_group('Farm settings')
    farm_group.add_argument('-f', '--farm', action='store_true', help="Render on Farmsoup")

    parser.add_argument('-rd')
    parser.add_argument('-proj')

    parser.add_argument('-b', help=argparse.SUPPRESS)
    parser.add_argument('-x', type=int, default=1920, help="Width")
    parser.add_argument('-y', type=int, default=1080, help="Height")
    parser.add_argument('-im', default="<Scene>/<RenderLayer>")
    parser.add_argument('-cam', help="Camera")
    parser.add_argument('-rl', help="Render Layer")
    parser.add_argument('-skipExistingFrames', metavar='0_or_1')

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

    if args.farm:
        main_farm(args)
    else:
        main_local(args)


def main_farm(args):

    render_cmd = get_command(args, '$F', '$F_end', '$FARMSOUP_RESERVED_GPUS_TOKENS', shell=True)

    name = [
        'mmmaya-redshift',
        os.path.splitext(os.path.basename(args.scene))[0],
    ]
    for attr in 'cam', 'rl':
        value = getattr(args, attr, None)
        if value:
            name.append(value)
    name = ' :: '.join(name)

    cmd = [
        'farmsoup',
        'submit',
        '--name', name,
        '--reservations', ','.join((
            'cpus=1',
            'gpus=1',
            'maya{}.install=1'.format(args.version),
            'maya{}.license=1'.format(args.version),
            'maya{}-redshift.install=1',format(args.version),
            'redshift.install=1',
            'redshift.license=1',
        )),
        '--priority', '99', # Just to be a little higher than the normal Maya jobs.
        '--range', 'F={}-{}/{}'.format(args.start, args.end, args.chunk),
        '--shell',
        'hostname\nenv | grep FARMSOUP | sort\n' + ' '.join(render_cmd),
    ]

    if args.verbose:
        print '$', ' '.join(cmd)
    if not args.dry_run:
        os.execvp(cmd[0], cmd)


def main_local(args):

    range_ = Range('{}-{}/{}'.format(args.s, args.e, args.c))

    queue = Queue()
    threads = []
    for gpu in xrange(args.gpus):
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

