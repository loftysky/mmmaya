import os

import farmsoup.client
from sgfs import SGFS
import sgpublish

from maya import cmds


class RenderJob(object):

    def __init__(self):

        renderer_node = cmds.getAttr('defaultRenderGlobals.currentRenderer')
        self.renderer = cmds.renderer(renderer_node, q=True, rendererUIName=True)

        path = cmds.file(q=True, sceneName=True) or 'Untitled'
        name = os.path.splitext(os.path.basename(path))[0]
        self.name = 'Maya Render ({}): {}'.format(self.renderer, name)

        self.cameras = []
        for cam in cmds.ls(type='camera'):
            if cmds.getAttr(cam + '.renderable'):
                self.cameras.append(cam)
        self.camera = self.cameras[-1]

        self.layers = {}
        for layer in cmds.ls(type='renderLayer'):
            self.layers[layer] = cmds.getAttr(layer + '.renderable')

        self.start_frame = cmds.getAttr('defaultRenderGlobals.startFrame')
        self.end_frame = cmds.getAttr('defaultRenderGlobals.endFrame')
        self.frame_chunk = 5

        self.width = cmds.getAttr('defaultResolution.width')
        self.height = cmds.getAttr('defaultResolution.height')

        self.output_directory = None

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

    def submit(self):

        scene_path = cmds.file(q=True, sceneName=True)
        scene_name = os.path.splitext(os.path.basename(scene_path))[0]

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
            publish_directory = publisher.directory

            maya_version = cmds.about(version=True)
            base_args = [

                'Render',
                '-V', maya_version,

                '-s', '@F',
                '-e', '@F_end',

                '-cam', self.camera,

                '-x', str(int(self.width)),
                '-y', str(int(self.height)),

                '-fnc', 'name.#.ext',
                '-pad', '4',


            ]

            client = farmsoup.client.Client()
            group = client.group(
                name=self.name,
            )

            for layer, include in sorted(self.layers.items()):
                if not include:
                    continue

                render_directory = os.path.join(publish_directory, layer)
                os.makedirs(render_directory)

                args = base_args[:]
                args.extend((
                    '-im', '{}.{}'.format(scene_name, layer),
                    '-rl', layer,
                    '-rd', render_directory,
                    scene_path
                ))
                
                job = group.job(
                    name=layer,
                    reservations={'maya{}'.format(maya_version): 1},
                ).setup_as_subprocess(args)
                job.expand_via_range('F={}-{}/{}'.format(self.start_frame, self.end_frame, self.frame_chunk))

            # TODO: Add a job to set the Shotgun status on each once they are done.

            client.submit(group)
            return group


