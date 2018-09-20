import os
import sys


def setup_env(env, version):

    if sys.platform == 'darwin':
        core_dir = '/Applications/redshift'
    else:
        core_dir = '/usr/redshift'

    module_dir = os.path.join(core_dir, 'redshift4maya')
    version_dir = os.path.join(module_dir, version)

    if not os.path.exists(version_dir):
        return

    # These variables are based off of the `redshift4maya.mod.template`
    # installed by the 2.6 versions::
    #
    #     + MAYAVERSION:2018 redshift4maya any /Applications/redshift/redshift4maya
    #     scripts: common/scripts
    #     icons: common/icons
    #     plug-ins: 2018
    #     REDSHIFT_COREDATAPATH = /Applications/redshift
    #     MAYA_CUSTOM_TEMPLATE_PATH +:= common/scripts/NETemplates
    #     REDSHIFT_MAYAEXTENSIONSPATH +:= 2018/extensions
    #     REDSHIFT_PROCEDURALSPATH += $REDSHIFT_COREDATAPATH/procedurals

    # See: http://help.autodesk.com/view/MAYAUL/2017/ENU/?guid=__files_GUID_130A3F57_2A5D_4E56_B066_6B86F68EEA22_htm

    env.append('MAYA_SCRIPT_PATH', os.path.join(module_dir, 'common/scripts'))
    env.append('XBMLANGPATH', os.path.join(module_dir, 'common/icons'))
    env.append('MAYA_PLUG_IN_PATH', version_dir)

    env['REDSHIFT_COREDATAPATH'] = core_dir
    env.append('MAYA_CUSTOM_TEMPLATE_PATH', os.path.join(module_dir, 'common/scripts/NETemplates'))
    env.append('REDSHIFT_MAYAEXTENSIONSPATH', os.path.join(version_dir, 'extensions'))
    env.append('REDSHIFT_PROCEDURALSPATH', os.path.join(core_dir, 'procedurals'))
