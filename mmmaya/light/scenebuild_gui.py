from concurrent.futures import ThreadPoolExecutor

from uitools.qt import Q
from sgfs import SGFS
from uitools.threads import defer_to_main_thread

import pymel.core as pm

from . import scenebuild


class Dialog(Q.Widgets.Dialog):

    def __init__(self):

        super(Dialog, self).__init__()

        self.setWindowFlags(Q.WindowStaysOnTopHint)

        self.show()

        self.progressDialog = Q.ProgressDialog(self,
            windowModality=Q.WindowModal,
            minimum=0,
            maximum=0,
        )
        self.progressDialog.canceled.connect(self.close)
        self.progressDialog.show()

        future = call_in_background(self._discoverCaches)
        @future.add_done_callback
        def _(f):
            print 'done1'
            if f.exception():
                print 'done2'
                self.close()

    def _discoverCaches(self):

        def progress(value=None, label=None, minimum=None, maximum=None):
            if minimum is not None:
                self.progressDialog.setMinimum(minimum)
            if maximum is not None:
                self.progressDialog.setMinimum(maximum)
            if value:
                self.progressDialog.setValue(value)
            if label:
                self.progressDialog.setLabelText(label)

        scenebuild.discover_caches(progress)



def run():
    scenebuild.run()
