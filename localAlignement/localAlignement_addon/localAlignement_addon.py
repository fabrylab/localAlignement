import sys
import warnings

import qtawesome as qta
from PyQt5.QtCore import pyqtSignal
from qtpy import QtCore, QtGui, QtWidgets

from localAlignement._version import __version__

warnings.simplefilter(action='ignore', category=RuntimeWarning)
from localAlignement.database_functions import *
from localAlignement.plotting import add_plot, display_selections
from localAlignement.helper_functions import *
from localAlignement.add_layer_window import FileSelectWindow
from collections import defaultdict
from localAlignement.scripts.get_angles import get_angles_from_file

# todo implement Qsettings
# self.settings = QSettings("pyTFM", "pyTFM")
# for key in self.parameter_dict.keys():
#    if not self.settings.value(key) is None:
#        self.parameter_dict[key] = self.settings.value(key)


class Addon(clickpoints.Addon):

    def __init__(self, *args, **kwargs):

        clickpoints.Addon.__init__(self, *args, **kwargs)

        # add mask type and markers
        setup_lines(self.db)
        self.cp.reloadTypes()
        if not all(["ROI" in m.name for m in self.db.getMaskTypes()]):
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

        # layouts
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setSpacing(20)
        self.layout.setContentsMargins(10, 20, 10, 20)

        self.layout_roi = QtWidgets.QHBoxLayout()
        self.layout_exp = QtWidgets.QHBoxLayout()
        self.layout_find_vectors = QtWidgets.QHBoxLayout()
        # self.layout_vector_files = QtWidgets.QHBoxLayout()
        self.layout_layers = QtWidgets.QHBoxLayout()

        # Roi selection
        self.dist_input = QtWidgets.QLineEdit()
        self.dist_input.setText("30")  # TODO: maybe change to micrometer
        self.dist_input.setValidator(QtGui.QIntValidator())  # restrict input to integers
        self.layout_roi.addWidget(self.dist_input, stretch=2)



        # Roi label
        self.dist_input_lable = QtWidgets.QLabel("ROI distance to fibre [pixel]")
        self.layout_roi.addWidget(self.dist_input_lable, stretch=6)

        # Tickbox to decide if all frames should be processed
        self.all_frames_checkbox = QtWidgets.QCheckBox("all_frames")
        self.layout_roi.addWidget(self.all_frames_checkbox, stretch=1)

        # button to mark region around lines
        self.button_add_roi = QtWidgets.QPushButton("mark ROI")
        self.button_add_roi.clicked.connect(self.add_roi)
        self.button_add_roi.setToolTip(tooltips["button_add_roi"])
        self.layout_roi.addWidget(self.button_add_roi, stretch=4)

        # button to display selected vector field
        self.display_selections_button = QtWidgets.QPushButton("display_selections")
        self.display_selections_button.clicked.connect(self.display_selections)
        self.display_selections_button.setToolTip(tooltips["display_selections"])
        self.layout_roi.addWidget(self.display_selections_button, stretch=4)

        self.box_roi = QtWidgets.QGroupBox("select an area of interest")
        self.box_roi.setLayout(self.layout_roi)

        # export button
        self.export_button = QtWidgets.QPushButton("export alignement data")
        self.export_button.clicked.connect(self.export_local_alignement)
        self.export_button.setToolTip(tooltips["export button"])

        self.display_angles_button = QtWidgets.QPushButton("display angles")
        self.display_angles_button.clicked.connect(self.display_angles)
        self.display_angles_button.setToolTip(tooltips["display_angles"])

        self.filename_field = QtWidgets.QLineEdit(os.path.join(os.getcwd(), "out.txt"))

        self.layout_exp.addStretch(stretch=2)
        self.layout_exp.addWidget(self.export_button, stretch=2)
        self.layout_exp.addWidget(self.filename_field, stretch=3)
        self.layout_exp.addWidget(self.display_angles_button, stretch=1)
        self.layout_exp.addStretch(stretch=2)

        # finding and loading vectors
        # line dit holding the currently selected folder
        self.line_edit_folder = QtWidgets.QLineEdit(self.folder)
        self.layout_find_vectors.addWidget(self.line_edit_folder, stretch=4)

        # button to browse folders
        self.open_folder_button = QtWidgets.QPushButton("choose directory")
        self.open_folder_button.clicked.connect(self.file_dialog)
        self.layout_find_vectors.addWidget(self.open_folder_button, stretch=2)

        # fields for regular expressions to identify vector files
        self.regex_x_field = QtWidgets.QLineEdit("tx")
        self.regex_x_field.textChanged.connect(self.search_vectors)
        self.layout_find_vectors.addWidget(self.regex_x_field, stretch=1)
        self.regex_y_field = QtWidgets.QLineEdit("ty")
        self.regex_y_field.textChanged.connect(self.search_vectors)
        self.layout_find_vectors.addWidget(self.regex_y_field, stretch=1)

        # loading the vector fields and marking if the loading was succesfull
        self.load_vectors_button = QtWidgets.QPushButton("load vector field")
        self.load_vectors_button.clicked.connect(self.load_vector_fields)
        self.load_vectors_button.setToolTip(tooltips["button_add_roi"])
        self.layout_find_vectors.addWidget(self.load_vectors_button, stretch=2)

        # displaying the vector files
        self.scrollAreaWidgetContents = QtWidgets.QWidget()  # adding grid layout to extra widget to allow for scrolling
        self.vector_file_layout = QtWidgets.QGridLayout(self.scrollAreaWidgetContents)
        self.vector_file_layout.setRowStretch(3, 3)  # this not beautiful but it works
        # self.vl_layout.setColumnStretch(3,3)
        label1 = QtWidgets.QLabel("Frame")
        label2 = QtWidgets.QLabel("vector x component")
        label3 = QtWidgets.QLabel("vector y component")
        label1.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.vector_file_layout.addWidget(label1, 1, 0)
        self.vector_file_layout.addWidget(label2, 1, 1)
        self.vector_file_layout.addWidget(label3, 1, 2)
        self.edits = {}
        self.add_eddit()

        self.scroll = QtWidgets.QScrollArea()
        self.scroll.setWidget(self.scrollAreaWidgetContents)

        self.vectors_layout = QtWidgets.QVBoxLayout()
        self.vectors_layout.addLayout(self.layout_find_vectors)
        self.vectors_layout.addWidget(self.scroll)

        self.box_vectors = QtWidgets.QGroupBox("load vector fields")
        self.box_vectors.setLayout(self.vectors_layout)

        # button to manage layers
        self.layers_button = QtWidgets.QPushButton("manage layers")
        self.layers_button.clicked.connect(self.add_layers)
        self.layers_button.setToolTip(tooltips["manage layers"])
        self.layout_layers.addStretch()
        self.layout_layers.addWidget(self.layers_button)
        self.layout_layers.addStretch()
        # adding sub layouts to main layout

        self.layout.addWidget(self.box_roi)
        self.layout.addLayout(self.layout_exp)
        self.layout.addWidget(self.box_vectors)
        self.layout.addLayout(self.layout_layers)

        # initial vectors
        self.search_vectors()
        self.update_name_fields()
        # automatically load the vector field if it is not to big
        if len(self.files_x.keys()) < 20:
            self.load_vector_fields()

    def add_eddit(self):
        self.edits = {}
        for i in range(self.db.getImageCount()):
            edit1 = QtWidgets.QLineEdit()
            edit2 = QtWidgets.QLineEdit()
            frame_label = QtWidgets.QLabel("Frame %s" % str(i))
            self.vector_file_layout.addWidget(frame_label, i + 2, 0)
            self.vector_file_layout.addWidget(edit1, i + 2, 1)
            self.vector_file_layout.addWidget(edit2, i + 2, 2)
            self.edits[i] = [frame_label, edit1, edit2]

    def add_layers(self):
        self._new_window = FileSelectWindow(self)
        self._new_window.show()

    def update_name_fields(self):
        for i in self.files_x.keys():
            xf = self.files_x[i]
            yf = self.files_y[i]
            self.edits[i][1].setText(xf)
            self.edits[i][2].setText(yf)

    def display_selections(self):
        frame = self.cp.getCurrentFrame()
        x = self.vector_fields[frame][0]
        y = self.vector_fields[frame][1]
        display_selections(x, y, frame, self.db)

    def display_angles(self):
        file = self.filename_field.text()
        get_angles_from_file(file, self.db)
        self.cp.reloadMaskTypes()
       #self.cp.reloadMarker() #TODO: reimplement that


    def check_text_field(self, edit):
        path = edit.text()
        if not os.path.isabs(path):
            path = os.path.join(self.folder, path)
        path_exists = os.path.isfile(path) and os.path.exists(path)

        if path_exists:
            edit_palette = edit.palette()
            edit_palette.setColor(edit.backgroundRole(), QtGui.QColor("green"))
            edit.setPalette(edit_palette)
        else:
            edit_palette = edit.palette()
            edit_palette.setColor(edit.backgroundRole(), QtGui.QColor("red"))
            edit.setPalette(edit_palette)

        return path_exists

    def load_vector_fields(self):
        self.search_vectors()
        self.update_name_fields()

        for frame, (l, e1, e2) in self.edits.items():
            # ignores folder if this is already an abslute path
            # load x_component
            exists_x = self.check_text_field(e1)
            if exists_x:
                self.vector_fields[frame][0] = np.load(os.path.join(self.folder, e1.text()))
            # load y_component
            exists_y = self.check_text_field(e2)
            if exists_y:
                self.vector_fields[frame][1] = np.load(os.path.join(self.folder, e2.text()))
            # setting field green if loading was successful

    def search_vectors(self):
        self.files_x, self.files_y = search_vectors(self.folder, self.regex_x_field.text(), self.regex_y_field.text())
        self.update_name_fields()

    # def add_vector_fields(self):
    #    # ToDO: implement this
    #    for frame, values in self.vector_fields.items():
    #        add_plot(self.db, values, frame)

    def export_local_alignement(self):
        file_name = self.filename_field.text()
        export_local_alignement(self.vector_fields,  self.db, file_name)

    def do_nothing(self):
        pass

    def file_dialog(self):  # TODO make this emit a signal
        dialog = QtWidgets.QFileDialog()
        dialog.setFileMode(QtWidgets.QFileDialog.DirectoryOnly)
        dialog.setDirectory(os.path.split(self.folder)[0])
        if dialog.exec_():
            dirname = dialog.selectedFiles()
            self.line_edit_folder.setText(dirname[0])
            self.folder = dirname[0]
            self.search_vectors()
            # self.search_vectors()

    def add_roi(self):
        self.cp.save()
        all_frames = self.all_frames_checkbox.isChecked()
        frame = self.cp.getCurrentFrame()
        add_roi(self.db, int(self.dist_input.text()), mask_name, line_name, frame, all_frames=all_frames)
        add_line_numbers(self.db, frame)
        self.cp.reloadMask()  # maybe for all frames? --> there is no such option??

    def display(self):
        add_roi(self.db, int(self.dist_input.text()), mask_name, line_name, self.cp.getCurrentFrame())
        self.cp.reloadMask()  # maybe for all frames??

    def reload_all(self):  # reloading entire display ## could be optimized
        sys.stdout = open(os.devnull, 'w')
        for frame in range(self.db.getImageCount()):
            for layer in self.db.getLayers():
                self.cp.reloadImage(frame_index=frame, layer_id=layer.id)
        sys.stdout = sys.__stdout__

    def start(self):
        print("########", "started")

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
