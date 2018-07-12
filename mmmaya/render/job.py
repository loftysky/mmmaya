import errno
import os

import farmsoup.client
from sgfs import SGFS
import sgpublish

from maya import cmds


class RenderJob(object):

    def __init__(self):

        self.renderer_node = cmds.getAttr('defaultRenderGlobals.currentRenderer')
        self.renderer = cmds.renderer(self.renderer_node, q=True, rendererUIName=True)

        path = cmds.file(q=True, sceneName=True) or 'Untitled'
        name = os.path.splitext(os.path.basename(path))[0]
        self.name = 'Maya Render ({}): {}'.format(self.renderer_node, name)

        self.camera_names = []
        self.cameras = {}
        for cam in cmds.ls(type='camera'):
            if cmds.getAttr(cam + '.renderable'):
                self.camera_names.append(cam)
                self.cameras[cam] = 0 if self.cameras else 1

        self.layer_names = sorted(cmds.ls(type='renderLayer'), key=lambda l: cmds.getAttr(l + '.displayOrder'))
        self.layers = {}
        for layer in self.layer_names:
            self.layers[layer] = cmds.getAttr(layer + '.renderable')

        self.start_frame = cmds.getAttr('defaultRenderGlobals.startFrame')
        self.end_frame = cmds.getAttr('defaultRenderGlobals.endFrame')
        self.frame_chunk = 5

        self.width = cmds.getAttr('defaultResolution.width')
        self.height = cmds.getAttr('defaultResolution.height')

        self.filename_pattern = '{layer},{camera}/{scene},{layer},{camera}'
        self.skip_existing = True

        self.location_method = 'publish'
        self.output_directory = ''

        self.driver = 'farmsoup'

        # Farmsoup options.
        self.reserve_renderer = True
        self.max_workers = 0

    def validate(self):

        path = cmds.file(q=True, sceneName=True)
        if not path:
            raise ValueError("File has not been saved.")

        if not self.name:
            raise ValueError("Job name is required.")

        if self.width < 0 or self.height < 0:
            raise ValueError("Invalid resolution.")

        if self.start_frame > self.end_frame:
            raise ValueError("End frame must be after start frame.")

        if not any(self.layers.values()):
            raise ValueError("At least one layer must be selected.")

        self.driver = self.driver.lower()
        if self.driver not in ('farmsoup', 'cli'):
            raise ValueError("Unknown driver.")

        self.location_method = self.location_method.lower()
        if self.location_method not in ('publish', 'manual'):
            raise ValueError("Unknown location method.")

        if self.driver == 'cli' and self.location_method != 'manual':
            raise ValueError("CLI driver can only use manual location.")

        if self.location_method == 'manual' and not self.output_directory:
            raise ValueError("No output directory given.")

    def submit(self):

        scene_path = cmds.file(q=True, sceneName=True)
        scene_name = os.path.splitext(os.path.basename(scene_path))[0]

        if self.location_method == 'publish':

            sgfs = SGFS()
            tasks = sgfs.entities_from_path(scene_path, ['Task'])
            if not tasks:
                raise ValueError("Scene is not saved under a Shotgun Task.")
            task = tasks[0]

            # TODO: Set a status.
            # TODO: Pull code, link, description, etc, from user.
            # TODO: Add metadata about the layers rendered.
            with sgpublish.Publisher(
                link=task,
                type='maya_render',
                name='Render',
                lock_permissions=False,
            ) as publisher:
                self.output_directory = publisher.directory


        maya_version = cmds.about(version=True)
        is_farmsoup = self.driver == 'farmsoup'

        base_args = [

            'Render',
            '-V', maya_version,

            '-s', '@F' if is_farmsoup else str(self.start_frame),
            '-e', '@F_end' if is_farmsoup else str(self.end_frame),

            '-x', str(int(self.width)),
            '-y', str(int(self.height)),

            '-fnc', 'name.#.ext',
            '-pad', '4',

        ]

        if self.skip_existing:
            base_args.extend(('-skipExistingFrames', 'true'))

        if is_farmsoup:
            client = farmsoup.client.Client()
            group = client.group(
                name=self.name,
            )

            reservations = {
                'maya': 1,
                'maya{}'.format(maya_version): 1,
            }
            if self.reserve_renderer and self.renderer_node not in (
                # Don't bother reserving the built-in ones.
                'mayaSoftware',
                'mayaHardware2',
            ):
                reservations[self.renderer_node] = 1

        for camera, include_camera in sorted(self.cameras.items()):
            if not include_camera:
                continue
            for layer, include_layer in sorted(self.layers.items()):
                if not include_layer:
                    continue

                fullname = self.filename_pattern.format(
                    scene=scene_name,
                    layer=layer,
                    camera=camera,
                )
                dir_, basename = os.path.split(fullname)

                dir_ = os.path.join(self.output_directory, dir_) if dir_ else self.output_directory
                
                if is_farmsoup:
                    try:
                        os.makedirs(dir_)
                    except OSError as e:
                        if e.errno != errno.EEXIST:
                            raise

                args = base_args[:]
                args.extend((
                    '-cam', camera,
                    '-rl', layer,
                    '-rd', dir_,
                    '-im', basename,
                    scene_path
                ))
                
                if is_farmsoup:
                    job = group.job(
                        name=fullname,
                        reservations=reservations,
                    ).setup_as_subprocess(args)
                    job.expand_via_range('F={}-{}/{}'.format(self.start_frame, self.end_frame, self.frame_chunk))
                else:
                    print ' '.join(args)


        # TODO: Add a job to set the Shotgun status on each once they are done.

        if is_farmsoup:
            client.submit(group)
            return group



