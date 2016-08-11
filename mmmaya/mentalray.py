from maya import cmds


def scrub_scene():

    print 'Deleting MentalRay nodes...'
    count = 0
    for name in '''
        mentalrayFramebuffer
        mentalrayOptions
        mentalRayGlobals
        mentalrayItemsList
        PreviewCaustics
        PreviewGlobalIllum
        PreviewFinalgather
        Production
        ProductionMotionblur
        Window
        NTSC
        PAL
        Draft
        DraftMotionBlur
        Preview
        PreviewMotionblur
    '''.strip().split():
        if cmds.ls(name):
            print '   ', name
            cmds.delete(name)
            count += 1

    cmds.confirmDialog(
        title='Scrub MentalRay',
        message='Deleted %d MentalRay node%s.' % (count, '' if count == 1 else 's'),
        button=['OK'],
    )

