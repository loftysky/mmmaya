import os

from uitools.qt import Q

from maya import cmds

from .job import RenderJob


class SubmitDialog(Q.Widgets.Dialog):

    def __init__(self):
        super(SubmitDialog, self).__init__()
        self._job = RenderJob()
        self._setupUI()

    def _setupUI(self):


        self._nameExample = Q.Label()


        self.setWindowTitle("Submit to FarmSoup")
        self.setMinimumWidth(400)

        outerLayout = Q.VBoxLayout()
        self.setLayout(outerLayout)

        layout = Q.FormLayout()
        outerLayout.addLayout(layout)

        layout.addRow("Renderer:", Q.Label(self._job.renderer))

        self._name = Q.LineEdit(self._job.name)
        layout.addRow("Job Name:", self._name)

        scrollArea = Q.ScrollArea()
        scrollWidget = Q.QWidget()
        scrollArea.setWidgetResizable(True)
        scrollArea.setWidget(scrollWidget)
        scrollLayout = Q.VBoxLayout()
        scrollWidget.setLayout(scrollLayout)
        layout.addRow("Cameras:", scrollArea)

        self._cameras = []
        for camera in self._job.camera_names:
            on = self._job.cameras[camera]
            box = Q.CheckBox(camera)
            if on:
                box.setChecked(True)
            scrollLayout.addWidget(box)
            self._cameras.append(box)



        scrollArea = Q.ScrollArea()
        scrollWidget = Q.QWidget()
        scrollArea.setWidgetResizable(True)
        scrollArea.setWidget(scrollWidget)
        layers = Q.VBoxLayout()
        scrollWidget.setLayout(layers)
        layout.addRow("Layers:", scrollArea)

        self._layers = []
        for layer in reversed(self._job.layer_names):
            on = self._job.layers[layer]
            box = Q.CheckBox(layer)
            if on:
                box.setChecked(True)
            layers.addWidget(box)
            self._layers.append(box)

        self._startFrame = Q.SpinBox(
            minimum=-1e6,
            maximum=1e6,
            value=self._job.start_frame,
            minimumWidth=75,
        )
        self._endFrame = Q.SpinBox(
            minimum=-1e6,
            maximum=1e6,
            value=self._job.end_frame,
            minimumWidth=75,
        )
        self._frameChunk = Q.SpinBox(
            minimum=1,
            maximum=100,
            value=self._job.frame_chunk,
            minimumWidth=50,
        )

        rangeLayout = Q.HBoxLayout()
        layout.addRow("Frame:", rangeLayout)
        rangeLayout.addWidget(self._startFrame)
        rangeLayout.addWidget(Q.Label("to"))
        rangeLayout.addWidget(self._endFrame)

        

        self._resMode = Q.ComboBox()

        width = self._job.width
        height = self._job.height

        self._width = Q.SpinBox(
            value=width,
            minimum=1,
            maximum=1e6,
            minimumWidth=75,
            enabled=False,
        )
        self._height = Q.SpinBox(
            value=height,
            minimum=1,
            maximum=1e6,
            minimumWidth=75,
            enabled=False,
        )

        for label, scale in (
            ('full', 1),
            ('half', 2),
            ('quarter', 4),
        ):
            sWidth = width / scale
            sHeight = height / scale
            self._resMode.addItem(label, (sWidth, sHeight))
        self._resMode.addItem("other")
        self._resMode.currentIndexChanged.connect(self._on_resMode_changed)

        resLayout = Q.HBoxLayout()
        layout.addRow("Resolution:", resLayout)
        resLayout.addWidget(self._resMode)
        resLayout.addWidget(self._width)
        resLayout.addWidget(Q.Label('x'))
        resLayout.addWidget(self._height)

        self._namePattern = Q.ComboBox()
        self._namePattern.currentIndexChanged.connect(self._on_nameFormat_changed)
        self._namePattern.addItem('{layer},{camera}/{scene},{layer},{camera}')
        self._namePattern.addItem('{layer}/{scene}.{layer}')
        self._namePattern.addItem('{scene}')
        self._namePattern.addItem('< ADD FORMAT >')

        nameLayout = Q.VBoxLayout()
        
        layout.addRow("File naming:", nameLayout)
        nameLayout.addWidget(self._namePattern)
        nameLayout.addWidget(self._nameExample)

        self._skipExisting = Q.CheckBox("Skip Existing Frames", checked=True)
        layout.addRow("", self._skipExisting)

        self._locationTabs = Q.TabWidget()
        layout.addRow("Location:", self._locationTabs)

        publishTab = Q.Widgets.Widget()
        self._locationTabs.addTab(publishTab, "Publish")
        publishLayout = Q.VBoxLayout()
        publishTab.setLayout(publishLayout)
        publishLayout.addWidget(Q.Label("<i>No publish controls at this time.</i>"))

        manualTab = Q.Widgets.Widget()
        self._locationTabs.addTab(manualTab, "Manual")
        manualLayout = Q.FormLayout()
        manualTab.setLayout(manualLayout)

        self._outputDirectory = Q.LineEdit(text=self._job.output_directory)
        self._outputDirectoryBrowse = Q.PushButton("Browse")
        self._outputDirectoryBrowse.clicked.connect(self._on_outputDirectoryBrowse_clicked)
        outputDirectoryLayout = Q.HBoxLayout()
        outputDirectoryLayout.addWidget(self._outputDirectory)
        outputDirectoryLayout.addWidget(self._outputDirectoryBrowse)
        manualLayout.addRow("", outputDirectoryLayout)

        self._driverTabs = Q.TabWidget()
        layout.addRow("Driver", self._driverTabs)

        farmsoupTab = Q.Widgets.Widget()
        self._driverTabs.addTab(farmsoupTab, "FarmSoup")
        farmsoupLayout = Q.FormLayout()
        farmsoupTab.setLayout(farmsoupLayout)

        farmsoupLayout.addRow("Chunk size:", self._frameChunk)

        self._maxWorkers = Q.SpinBox(
            value=self._job.max_workers,
            minimum=0,
            maximum=100,
            minimumWidth=50,
        )
        farmsoupLayout.addRow("Max workers:", self._maxWorkers)

        self._reserveRenderer = Q.CheckBox("Reserve Renderer", checked=True)
        farmsoupLayout.addRow("", self._reserveRenderer)

        commandLineTab = Q.Widgets.Widget()
        self._driverTabs.addTab(commandLineTab, "CLI")
        commandLineLayout = Q.VBoxLayout()
        commandLineTab.setLayout(commandLineLayout)
        commandLineLayout.addWidget(Q.Label('<i>Command line will be printed to Script Editor.</i>'))

        buttonLayout = Q.HBoxLayout()
        outerLayout.addLayout(buttonLayout)
        buttonLayout.addStretch()

        self._submit = Q.PushButton("Submit")
        self._submit.clicked.connect(self._on_submit_clicked)
        buttonLayout.addWidget(self._submit)
        buttonLayout.addStretch()

        self._updateExamples()

    def _updateExamples(self):

        scene_path = cmds.file(q=True, sceneName=True)
        scene_name = os.path.splitext(os.path.basename(scene_path))[0] or 'untitled'

        for camera in self._cameras:
            if camera.isChecked():
                camera = camera.text()
                break
        else:
            camera = 'NOCAMERA'
        
        for layer in self._layers:
            if layer.isChecked():
                layer = layer.text()
                break
        else:
            layer = 'NOLAYER'

        pattern = self._namePattern.currentText()
        example = pattern.format(
            scene=scene_name,
            camera=camera,
            layer=layer,
        )
        example = example.replace(':', '_') # This is what Maya will do.
        
        self._nameExample.setText('<i><code><small>{}.####.ext</small></code></i>'.format(example))

    def _on_outputDirectoryBrowse_clicked(self):
        dir_ = Q.FileDialog.getExistingDirectory(self, "Output Directory",
            self._outputDirectory.text() or os.getcwd())
        if dir_:
            self._outputDirectory.setText(dir_)

    def _on_resMode_changed(self, x):
        isOther = self._resMode.currentText() == 'other'
        self._width.setEnabled(isOther)
        self._height.setEnabled(isOther)

        data = self._resMode.itemData(self._resMode.currentIndex())
        if data:
            self._width.setValue(data[0])
            self._height.setValue(data[1])

    def _on_nameFormat_changed(self, x):

        if self._namePattern.currentText() != '< ADD FORMAT >':
            self._updateExamples()
            return

        self._namePattern.setCurrentIndex(0) # Move off of ADD FORMAT.

        format_, ok = Q.InputDialog.getText(self,
            "Add Name Format",
            """
                Enter a name format using tokens<br>
                <code>{scene}</code>,
                <code>{camera}</code>, and
                <code>{layer}</code>.
            """,
            text="{scene},{layer},{camera}"
        )
        format_ = format_.strip()
        if not format_ or not ok:
            return

        i = self._namePattern.findText(format_)
        if i >= 0:
            self._namePattern.setCurrentIndex(i)
        else:
            i = self._namePattern.count() - 1
            self._namePattern.insertItem(i, format_)
            self._namePattern.setCurrentIndex(i)


    def _on_submit_clicked(self):

        self._job.name = self._name.text()
        for camera in self._cameras:
            self._job.cameras[camera.text()] = camera.isChecked()
        for layer in self._layers:
            self._job.layers[layer.text()] = layer.isChecked()
        self._job.start_frame = self._startFrame.value()
        self._job.end_frame = self._endFrame.value()
        self._job.frame_chunk = self._frameChunk.value()
        self._job.width = self._width.value()
        self._job.height = self._height.value()

        self._job.filename_pattern = self._namePattern.currentText()
        self._job.skip_existing = self._skipExisting.isChecked()

        self._job.location_method = self._locationTabs.tabText(self._locationTabs.currentIndex())
        self._job.output_directory = self._outputDirectory.text()

        self._job.driver = self._driverTabs.tabText(self._driverTabs.currentIndex())
        self._job.reserve_renderer = self._reserveRenderer.isChecked()
        self._job.max_workers = self._maxWorkers.value()

        try:
            self._job.validate()
        except ValueError as e:
            Q.MessageBox.critical(self, "Validation Error", e.args[0])
            return

        # TODO: Save a copy of the scene.

        group = self._job.submit()
        
        self.close()
        
        if group is not None:
            Q.MessageBox.information(self, "Job Submitted", "Job submitted as group {}.".format(group.id))



def open_window():
    global _dialog
    _dialog = SubmitDialog()
    _dialog.show()
    _dialog.raise_()
