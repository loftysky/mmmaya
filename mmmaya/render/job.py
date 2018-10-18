import errno
import os
from pipes import quote as sh_quote


import farmsoup.client
from sgfs import SGFS
import sgpublish

from maya import cmds
import pymel.core as pm

class RenderJob(object):

    def __init__(self):

        self.renderer = cmds.getAttr('defaultRenderGlobals.currentRenderer')

        path = cmds.file(q=True, sceneName=True) or 'Untitled'
        name = os.path.splitext(os.path.basename(path))[0]
        self.name = 'Maya Render ({}): {}'.format(self.renderer, name)

        self.camera_names = []
        self.cameras = {}
        for cam in cmds.listCameras(): # This returns transforms if they uniquely ID cameras.
            if cmds.getAttr(cam + '.renderable'):
                self.camera_names.append(cam)
                self.cameras[cam] = 0 if self.cameras else 1

        self.layer_names = []
        self.layers = {}
        for layer in sorted(cmds.ls(type='renderLayer'), key=lambda l: cmds.getAttr(l + '.displayOrder')):

            # Don't even bother presenting anything that is referenced.
            if ':' in layer:
                continue
            
            # Use a name that matches the UI and token replacement behaviour of
            # the Render command.
            layer_name = 'masterLayer' if layer == 'defaultRenderLayer' else layer

            self.layer_names.append(layer_name)
            self.layers[layer_name] = cmds.getAttr(layer + '.renderable')

        self.renderers = {}
        connections = pm.PyNode('defaultRenderGlobals.currentRenderer').listConnections(source=True, plugs=True)
        if connections:
            for con in connections:
                node = str(con.node())
                node = 'masterLayer' if node == 'defaultRenderLayer' else node # Gross.
                if not node in self.layers:
                    continue
                value = con.parent().attr('value').get()
                self.renderers[node] = value
        else:
            self.renderers['masterLayer'] = cmds.getAttr('defaultRenderGlobals.currentRenderer')

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

        if is_farmsoup:
            client = farmsoup.client.Client()
            group = client.group(
                name=self.name,
            )

            base_resv = {
                'maya{}.install'.format(maya_version): 1,
                'maya{}.license'.format(maya_version): 1,
            }


        for camera, include_camera in sorted(self.cameras.items()):
            if not include_camera:
                continue
            for layer, include_layer in sorted(self.layers.items()):
                if not include_layer:
                    continue

                renderer = self.renderers.get(layer) or self.renderers['masterLayer']
                
                args = [

                    'Render',
                    '-V', maya_version,

                ]
                reservations = base_resv.copy()

                if self.reserve_renderer and renderer not in (
                    # Don't bother reserving the built-in ones.
                    'mayaSoftware',
                    'mayaHardware2',
                ):
                    # These look like "arnold" and "redshift".
                    reservations['maya{}-{}.install'.format(maya_version, renderer)] = 1
                    reservations['{}.install'.format(renderer)] = 1
                    reservations['{}.license'.format(renderer)] = 1

                if renderer == 'redshift':
                    args.extend((
                        '-r', 'redshift',
                        # This must not be escaped!
                        '-gpu', '{$FARMSOUP_RESERVED_GPUS_TOKENS}'
                    ))
                    reservations['cpus'] = 1
                    reservations['gpus'] = 1

                else:
                    args.extend((
                        # Redshift doesn't understand -fnc.
                        # Nothing really depends on this, so it isn't a big deal.
                        '-fnc', 'name.#.ext',
                    ))

                args.extend((

                    '-s', '$F' if is_farmsoup else str(self.start_frame),
                    '-e', '$F_end' if is_farmsoup else str(self.end_frame),

                    '-x', str(int(self.width)),
                    '-y', str(int(self.height)),

                    '-pad', '4',

                ))

                if self.skip_existing:
                    args.extend(('-skipExistingFrames', 'true'))

                # We need to ask Maya to do the templating for us, because
                # otherwise it will decide that because there are multiple
                # render layers that there will be a naming collision, and so
                # it automatically adds directories for us.
                template_name = self.filename_pattern.format(
                    scene=scene_name,
                    layer='<RenderLayer>',
                    camera='<Camera>',
                )
                display_name = self.filename_pattern.format(
                    scene=scene_name,
                    layer=layer,
                    camera=camera,
                ).replace(':', '_')

                args.extend((
                    '-cam', camera,
                    '-rl', layer,

                    # We're only escaping the ones that we need to, because
                    # Redshift relies upon the envvars to pick GPUs at
                    # render time.
                    '-rd', sh_quote(self.output_directory),
                    '-im', sh_quote(template_name),
                    sh_quote(scene_path)
                ))
                
                command = ' '.join(args)

                if is_farmsoup:
                    job = group.job(
                        name=display_name,
                        reservations=reservations,
                    ).setup_as_subprocess(command, shell=True)
                    job.expand_via_range('F={}-{}/{}'.format(self.start_frame, self.end_frame, self.frame_chunk))
                else:
                    print ' '.join(args)


        # TODO: Add a job to set the Shotgun status on each once they are done.

        if is_farmsoup:
            client.submit(group)
            return group



