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
        self.setWindowTitle("Submit to FarmSoup")
        self.setMinimumWidth(400)

        outerLayout = Q.VBoxLayout()
        self.setLayout(outerLayout)

        layout = Q.FormLayout()
        outerLayout.addLayout(layout)

        layout.addRow("Renderer:", Q.Label(self._job.renderer))

        self._name = Q.LineEdit(self._job.name)
        layout.addRow("Name:", self._name)

        self._camera = Q.ComboBox()
        layout.addRow("Camera:", self._camera)
        for cam in self._job.cameras:
            self._camera.addItem(cam)

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
        rangeLayout.addWidget(Q.Label("in chunks of"))
        rangeLayout.addWidget(self._frameChunk)

        

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


        buttonLayout = Q.HBoxLayout()
        outerLayout.addLayout(buttonLayout)
        buttonLayout.addStretch()

        self._submit = Q.PushButton("Submit")
        self._submit.clicked.connect(self._on_submit_clicked)
        buttonLayout.addWidget(self._submit)
        buttonLayout.addStretch()

    def _on_resMode_changed(self, x):
        isOther = self._resMode.currentText() == 'other'
        self._width.setEnabled(isOther)
        self._height.setEnabled(isOther)

        data = self._resMode.itemData(self._resMode.currentIndex())
        if data:
            self._width.setValue(data[0])
            self._height.setValue(data[1])

    def _on_submit_clicked(self):

        self._job.name = self._name.text()
        self._job.camera = self._camera.currentText()
        for layer in self._layers:
            self._job.layers[layer.text()] = layer.isChecked()
        self._job.start_frame = self._startFrame.value()
        self._job.end_frame = self._endFrame.value()
        self._job.frame_chunk = self._frameChunk.value()
        self._job.width = self._width.value()
        self._job.height = self._height.value()

        try:
            self._job.validate()
        except ValueError as e:
            Q.MessageBox.critical(self, "Validation Error", e.args[0])
            return

        # TODO: Save a copy of the scene.

        group = self._job.submit()
        
        self.close()
        Q.MessageBox.information(self, "Job Submitted", "Job submitted as group {}.".format(group.id))



def open_window():
    global _dialog
    _dialog = SubmitDialog()
    _dialog.show()
    _dialog.raise_()
