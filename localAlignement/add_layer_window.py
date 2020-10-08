from localAlignement._version import __version__
import os
import sys
from functools import partial
from qtpy import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import QSettings
import warnings
import re
warnings.simplefilter(action='ignore', category=RuntimeWarning)
from localAlignement.helper_functions import *
from collections import defaultdict
# todo implement Qsettings




class FileDialog_advanced(QtWidgets.QFileDialog):
    files_opened = pyqtSignal()  # this is shared between all classes where as the stuff with self. is instance specific

    def __init__(self, *args):

        QtWidgets.QFileDialog.__init__(self, *args)
        self.setOption(self.DontUseNativeDialog, True)
        self.setFileMode(self.ExistingFiles)
        btns = self.findChildren(QtWidgets.QPushButton)
        self.openBtn = [x for x in btns if 'open' in str(x.text()).lower()][0]
        self.openBtn.clicked.disconnect()
        self.openBtn.clicked.connect(self.openClicked)
        self.tree = self.findChild(QtWidgets.QTreeView)
        # self.files_opened = files_opened
        self.show()

    def openClicked(self):

        inds = self.tree.selectionModel().selectedIndexes()
        files = []
        for i in inds:
            if i.column() == 0:
                files.append(os.path.join(str(self.directory().absolutePath()), str(i.data())))
        self.selectedFiles = files
        self.files_opened.emit()
        # self.hide()

    def filesSelected(self):
        return self.selectedFiles


class FileSelectWindow(QtWidgets.QWidget):
    _fromFolderField = 0
    _fromFileDialog = 1
    _fromRegexField = 2

    def __init__(self, main_window):
        super(FileSelectWindow, self).__init__()
        self._new_window = None
        self.folder = os.getcwd()
        self.files_flat = []
        self.sort_id = []

        self.setWindowTitle("image selection")
        # self.setMinimumWidth(600)
        # self.setMinimumHeight(200)
        self.resize(600, 150)
        self.main_window = main_window
        self.main_window.outfile_path = os.path.join(os.getcwd(), "out.txt")

        # the layouts
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setSpacing(20)
        self.layout.setContentsMargins(10, 20, 10, 20)
        self.layout_choose = QtWidgets.QHBoxLayout(self)
        self.layout_display_files = QtWidgets.QHBoxLayout(self)
        self.layout_layer_actions = QtWidgets.QHBoxLayout(self)

        # buttons and text fields t choose files
        self.choose_file_edit = QtWidgets.QLineEdit(self.folder)
        self.choose_file_edit.textEdited.connect(partial(self.find_files, source=self._fromFolderField))
        self.layout_choose.addWidget(self.choose_file_edit, stretch=6)

        self.choose_file_button = QtWidgets.QPushButton("choose directory")
        self.choose_file_button.clicked.connect(self.file_dialog)
        self.layout_choose.addWidget(self.choose_file_button, stretch=1)

        self.choose_regex = QtWidgets.QLineEdit("(\d{2})")
        self.choose_regex.textChanged.connect(partial(self.find_files, source=self._fromRegexField))
        self.layout_choose.addWidget(self.choose_regex, stretch=3)

        # main field displaying the files
        self.display_files = QtWidgets.QTextEdit()  # add default content here
        # self.display_files.textChanged.connect() # other funtction
        self.layout_display_files.addWidget(self.display_files)

        # text field to define layer
        layer_names = [l.name for l in self.main_window.db.getLayers()]
        self.layer_name_field = QtWidgets.QComboBox()
        self.layer_name_field.setEditable(True)
        self.layer_name_field.addItems(layer_names)
        self.layout_layer_actions.addWidget(self.layer_name_field, stretch=2)
        # button to add layer
        self.add_layer_button = QtWidgets.QPushButton("add layer")
        self.add_layer_button.clicked.connect(self.add_layers)
        self.layout_layer_actions.addWidget(self.add_layer_button, stretch=1)
        # button to delete layer
        self.delete_layer_button = QtWidgets.QPushButton("remove layer")
        self.delete_layer_button.clicked.connect(self.remove_layers)
        self.layout_layer_actions.addWidget(self.delete_layer_button, stretch=1)

        # checkbox to overwrite
        self.overwrite_default_box = QtWidgets.QCheckBox("overwrite default layer")
        self.overwrite_default_box.setChecked(True)
        self.layout_layer_actions.addWidget(self.overwrite_default_box, stretch=1)

        self.layout.addLayout(self.layout_choose, stretch=2)
        self.layout.addLayout(self.layout_display_files, stretch=6)
        self.layout.addLayout(self.layout_layer_actions, stretch=2)

        # initial displayed files
        self.find_files(source=self._fromFolderField)

    # define enter key press event
    def keyPressEvent(self, e):
        # print(e.key())
        if e.key() == QtCore.Qt.Key_Enter or e.key() == QtCore.Qt.Key_Return:
            self.find_files()

    def remove_layers(self):

        layer = self.layer_name_field.currentText()
        l_names = [l.name for l in self.main_window.db.getLayers()]
        if layer in l_names:
            self.main_window.db.deleteLayers(layer)
            self.layer_name_field.removeItem(self.layer_name_field.findText(layer, QtCore.Qt.MatchFixedString))
        else:
            print("layer %s not found" % layer)
        self.main_window.reload_all()
        self.main_window.cp.updateImageCount()
        self.main_window.add_eddit()

    def add_layers(self):

        layer = self.layer_name_field.currentText()
        l_names = [l.name for l in self.main_window.db.getLayers()]
        if len(l_names) == 1 and "default" in l_names:
            self.main_window.db.deleteLayers("default")  # TODOthis should remove the image entry right?
            self.layer_name_field.removeItem(self.layer_name_field.findText("default", QtCore.Qt.MatchFixedString))
        if layer in l_names:
            self.main_window.db.deleteLayers(layer)
            self.layer_name_field.removeItem(self.layer_name_field.findText(layer, QtCore.Qt.MatchFixedString))
        current_layers = self.main_window.db.getLayers()
        if len(current_layers) > 0:
            base_layer = current_layers[0].base_layer
        else:
            base_layer = None
        new_layer = self.main_window.db.setLayer(layer, base_layer=base_layer)
        for frame, im in zip(self.sort_id, self.files_flat):
            self.main_window.db.setImage(filename=im, sort_index=frame, layer=new_layer)
        self.layer_name_field.addItem(layer)
        self.main_window.reload_all()
        self.main_window.cp.updateImageCount()
        self.main_window.add_eddit()

    def file_dialog(self):
        # self.dialog = FileDialog_advanced()
        # self.dialog.files_opened.connect(partial(self.find_files, source=self._fromFileDialog))
        dialog = QtWidgets.QFileDialog()
        dialog.setFileMode(QtWidgets.QFileDialog.DirectoryOnly)
        dialog.setDirectory(os.path.split(self.folder)[0])
        if dialog.exec_():
            dirname = dialog.selectedFiles()
            print(dirname)
            self.select_folder = dirname[0]
            self.find_files(source=self._fromFileDialog)

    def find_files(self, source=0):
        try:
            regex = re.compile(self.choose_regex.text())
        except re.error as e:
            print(e)
            self.display_files.setText("")
            return
        if source == self._fromFolderField or source == self._fromRegexField:
            folder = self.choose_file_edit.text()
        else:
            # folder = self.dialog.selectedFiles
            folder = self.select_folder
            self.choose_file_edit.setText(folder)
        if not os.path.exists(folder):
            return
        self.files_flat = [os.path.join(folder, x) for x in os.listdir(folder) if re.search(regex, x)]

        # sorting:
        # group was provided in the regex try to identfy the frame and sort according to this group
        if regex.groups == 1:
            frame_groups = {x: re.search(regex, os.path.split(x)[1]).group(1) for x in self.files_flat}
            self.sort_id, sort_id_dict = make_rank_list(list(frame_groups.values()))
            warn_non_unique(self.sort_id, sort_id_dict, frame_groups)
            self.files_flat = [x for _,x in sorted(zip(self.sort_id, self.files_flat))]
        # else use simple natsorting
        else:
            print("No regular expression group to identify the frame")
            self.files_flat = natsort.natsorted(self.files_flat, key=lambda x: os.path.split(x)[1])
            self.sort_id = list(range(len(self.files_flat)))

        # writing to textbox
        write_str = ""
        for si, f in zip(self.sort_id, self.files_flat):
            write_str += str(si) + "\t" + f + "\n"
        self.display_files.setText(write_str)

    ##### todo: designe better file selction
    '''
    def file_dialog(self):
        self.dialog = QtWidgets.QFileDialog()
        #dialog = FileDialog()
        self.dialog.setFileMode(QtWidgets.QFileDialog.ExistingFiles)
        self.dialog.selectFile("/home/user/Desktop/results")
       # self.dialog.currentChanged.connect(self.print_files) # emmitt selected files
        self.dialog.setDirectory(self.folder)

        print(self.dialog.signals())
        split = self.dialog.findChild(QtWidgets.QSplitter)
        frame = split.findChild(QtWidgets.QFrame)
        stack = frame.findChild(QtWidgets.QStackedWidget)
        nw = stack.count()
        w1 = stack.widget(0)
        w2 =stack.widget(1)
        #w1.hide()
        tree = w2.findChild(QtWidgets.QTreeView)
        main_widget = tree.children()[0]
        #main_widget.mouseMoveEvent().connect(self.print_files)

        # maybe define some own events hereß??
        print(main_widget.children())
        print(dir(main_widget))
        #tree.hide()
        #widget.hide()
        #frame.children()[1].hide()

        #for btn in self.dialog.findChildren(QtWidgets.QAction):
        #    btn.hide()
        for obj in stack.children():
            try:
                if not obj.isHidden():
                    print(obj)
            except:
                print("err", obj)
                pass
       # print(self.dialog.children())

        if self.dialog.exec_():
            dirname = self.dialog.selectedFiles()
            self.choose_file_edit.setText(dirname[0])
            self.folder = os.path.split(dirname[0])[0]
        self.update_dirs()

    def print_files(self,s):
        new_file = [s]
        previous_files = self.dialog.selectedFiles()
        all_files = list(np.unique(new_file + previous_files))
        self.dialog.selectFile(",".join(all_files))
    def update_dirs(self):
        pass
    def find_files(self):
        pass
    '''



