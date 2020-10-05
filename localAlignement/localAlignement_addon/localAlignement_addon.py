from localAlignement._version import __version__
import os
import sys
from functools import partial
from qtpy import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import QSettings
import qtawesome as qta
import clickpoints
import traceback
import asyncio
import warnings
warnings.simplefilter(action='ignore', category=RuntimeWarning)
from localAlignement.database_functions import *
from localAlignement.parameters_and_strings import *
from localAlignement.helper_functions import *
from collections import defaultdict
from localAlignement.plotting import add_plot, display_selections

class Addon(clickpoints.Addon):

    def __init__(self, *args, **kwargs):

        clickpoints.Addon.__init__(self, *args, **kwargs)

        # add mask type and markers
        setup_lines(self.db)
        self.cp.reloadTypes()
        if not all(["ROI" in m.name for m in self.db.getMaskTypes()]) :
            choice = QtWidgets.QMessageBox.question(self, 'continue',
                                                    "All exisiting masks will be deleted",
                                                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            if choice == QtWidgets.QMessageBox.No:
                return
            else:
                setup_masks(self.db)
                self.cp.reloadMaskTypes()
                self.cp.reloadMaskTypes()
        self.folder = os.getcwd()
        self.vector_fields = defaultdict(lambda: [[], []])
        """ GUI Widgets"""
        # set the title and layout
        self.setWindowTitle("localAlignement" + "-" + __version__)
        self.setWindowIcon(qta.icon("fa.compress"))
        self.setMinimumWidth(400)
        self.setMinimumHeight(200)
        self.layout = QtWidgets.QGridLayout(self)
        self.layout.setColumnMinimumWidth(0, 150)

        # enter distance to line in pixels # TODO change to micrometer
        self.sublayout1 = QtWidgets.QVBoxLayout()

        self.dist_input = QtWidgets.QLineEdit()
        self.dist_input.setText("3")
        self.dist_input.setValidator(QtGui.QIntValidator()) # restrict input to integers
        self.dist_input_lable =  QtWidgets.QLabel("ROI distance to fibre [pixel]")
        self.sublayout1.addWidget(self.dist_input)
        self.sublayout1.addWidget(self.dist_input_lable)

        self.layout.addLayout(self.sublayout1, 0, 0)

        # button to mark region around lines
        self.button_add_roi = QtWidgets.QPushButton("start")
        #self.button_add_roi.clicked.connect(partial(self.start_thread,run_function=self.add_roi))
        self.button_add_roi.clicked.connect(self.add_roi)
        self.button_add_roi.setToolTip(tooltips["button_add_roi"])
        self.layout.addWidget(self.button_add_roi, 0, 1)

        self.load_vectors = QtWidgets.QPushButton("load vector field")
        # self.button_add_roi.clicked.connect(partial(self.start_thread,run_function=self.add_roi))
        #self.load_vectors.clicked.connect(self.add_roi)
        self.load_vectors.clicked.connect(self.load_vector_fields)
        self.load_vectors.setToolTip(tooltips["button_add_roi"])
        self.layout.addWidget(self.load_vectors, 1, 1)


        self.display_selections_button = QtWidgets.QPushButton("display_selections")
        # self.button_add_roi.clicked.connect(partial(self.start_thread,run_function=self.add_roi))
        #self.load_vectors.clicked.connect(self.add_roi)
        self.display_selections_button.clicked.connect(self.display_selections)
        self.display_selections_button.setToolTip(tooltips["display_selections"])
        self.layout.addWidget(self.display_selections_button, 2, 1)




        self.export_button = QtWidgets.QPushButton("export alignement data")
        # self.button_add_roi.clicked.connect(partial(self.start_thread,run_function=self.add_roi))
        # self.load_vectors.clicked.connect(self.add_roi)
        self.export_button.clicked.connect(self.export_local_alignement)
        self.export_button.setToolTip(tooltips["button_add_roi"])
        self.layout.addWidget(self.export_button, 3, 1)


        # vector location layout
        self.browse_layout = QtWidgets.QHBoxLayout(self)

        self.line_edit_folder = QtWidgets.QLineEdit(self.folder)
        self.line_edit_folder.textChanged.connect(self.do_nothing)
        self.open_folder_button = QtWidgets.QPushButton("browse")
        self.open_folder_button.clicked.connect(self.file_dialog)
        self.regex_x_field = QtWidgets.QLineEdit("x")
        self.regex_y_field = QtWidgets.QLineEdit("y")
        self.search_vectors_button = QtWidgets.QPushButton("apply")
        self.search_vectors_button.clicked.connect(self.search_vectors)
        # self.apply_regex_button = QtWidgets.QPushButton("apply")
        # self.apply_regex_button.clicked.connect(self.search_vectors)

        self.browse_layout.addWidget(self.line_edit_folder)
        self.browse_layout.addWidget(self.open_folder_button)
        self.browse_layout.addWidget(self.regex_x_field)
        self.browse_layout.addWidget(self.regex_y_field)
        self.browse_layout.addWidget(self.search_vectors_button)
        # self.vl_layout.addWidget(self.apply_regex_button, 0, 3)

        self.layout.addLayout(self.browse_layout, 2, 0)

        self.vl_layout = QtWidgets.QGridLayout(self)
        self.vl_layout.setRowStretch(3,3) # this not beautiful but it works
        # self.vl_layout.setColumnStretch(3,3)

        label1 = QtWidgets.QLabel("Frame")
        label2 = QtWidgets.QLabel("vector x component")
        label3 = QtWidgets.QLabel("vector y component")
        label1.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.vl_layout.addWidget(label1, 1, 0)
        self.vl_layout.addWidget(label2,1, 1)
        self.vl_layout.addWidget(label3, 1, 2)
        self.edits = {}
        for i in range(self.db.getImageCount()):
            edit1 = QtWidgets.QLineEdit()
            edit2 = QtWidgets.QLineEdit()
            self.edits[(i, 1)] = edit1
            self.edits[(i, 2)] = edit2
            frame_label = QtWidgets.QLabel("Frame %s"%str(i))
            self.vl_layout.addWidget(frame_label, i + 2, 0)
            self.vl_layout.addWidget(edit1, i + 2, 1)
            self.vl_layout.addWidget(edit2, i + 2, 2)

        self.layout.addLayout(self.vl_layout, 3, 0)


    def search_vectors(self):
        self.files_x, self.files_y = search_vectors(self.folder, self.regex_x_field.text(), self.regex_x_field.text())
        self.update_name_fields()


    def update_name_fields(self):
        for i in self.files_x.keys():
            xf = self.files_x[i]
            yf = self.files_y[i]
            self.edits[i, 1].setText(xf)
            self.edits[i, 2].setText(yf)

    def display_selections(self):
        frame  = self.cp.getCurrentFrame()
        x = self.vector_fields[frame][0]
        y = self.vector_fields[frame][0]
        display_selections(x, y, frame, self.db)

    def load_vector_fields(self):
        for (frame,j),edit in self.edits.items():
            # ignores folder if this is already an abslute path
            path = edit.text()
            if not os.path.isabs(path):
                path = os.path.join(self.folder, path)

            if os.path.exists(path):
                # load x_component
                if j == 1:
                    self.vector_fields[frame][0] = np.load(os.path.join(self.folder,edit.text()))
                # load y_component
                if j == 2:
                    self.vector_fields[frame][1] = np.load(os.path.join(self.folder, edit.text()))
                # setting field green if loading was successful
                edit_palette =edit.palette()
                edit_palette.setColor(edit.backgroundRole(), QtGui.QColor("green"))
                edit.setPalette(edit_palette)
            else:
                # if not field red
                edit_palette = edit.palette()
                edit_palette.setColor(edit.backgroundRole(), QtGui.QColor("red"))
                edit.setPalette(edit_palette)
        #self.add_vector_fields()

    def add_vector_fields(self):
        # ToDO: implement this
        for frame, values in self.vector_fields.items():
            add_plot(self.db, values, frame)

    def export_local_alignement(self):
        frame = self.cp.getCurrentFrame()
        x = self.vector_fields[frame][0]
        y = self.vector_fields[frame][1]
        export_local_alignement(x,y, frame, self.db)
    def do_nothing(self):
        pass

    def file_dialog(self):
        dialog = QtWidgets.QFileDialog()
        dialog.setFileMode(QtWidgets.QFileDialog.DirectoryOnly)
        dialog.setDirectory(self.folder)
        if dialog.exec_():
            dirname = dialog.selectedFiles()
            self.line_edit_folder.setText(dirname[0])
            self.folder = dirname[0]
            #self.search_vectors()

    def add_roi(self):
        frame = self.cp.getCurrentFrame()
        add_roi(self.db, int(self.dist_input.text()), mask_name, line_name, frame)
        add_line_numbers(self.db, frame)
        self.cp.reloadMask() # maybe for all frames?
        self.cp.reloadMarker(frame=frame)  # maybe for all frames??

    def display(self):
        add_roi(self.db, int(self.dist_input.text()), mask_name, line_name, self.cp.getCurrentFrame())
        self.cp.reloadMask() # maybe for all frames??


    def start(self):
        print ("########", "started")
    # run in a separate thread to keep clickpoints gui responsive // now using QThread and stuff
    def start_thread(self, run_function=None):
        self.thread = Worker(self, run_function=run_function)
        self.thread.start()  # starting thread
        self.thread.finished.connect(self.reload_all)  # connecting function on thread finish

        # x.join()

    def buttonPressedEvent(self):
        # show the addon window when the button in ClickPoints is pressed
        self.show()

    # disable running in other thread other wise "figsize" is somehow overloaded
    async def run(self):
        pass


class Worker(QtCore.QThread):
    output = pyqtSignal()

    def __init__(self, main, parent=None, run_function=None):
        QtCore.QThread.__init__(self, parent)
        self.main = main
        if run_function is None:
            self.run_function = self.main.start
        else:
            self.run_function = run_function

    def run(self):
        self.run_function()

