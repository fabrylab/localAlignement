# -*- coding: utf-8 -*-
"""
Created on Sun Mar 05 June 2020
@author: Ben Fabry
"""
# this program reads an image file, performs a bandpass filter and gamma correction
# and stores the filtered image in the same directory as the original image
# with the extenseion _bandpass.tif
# the user can set the values for gamma, highpass and lowpass according to the
# properties of the input image

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from skimage.filters import gaussian
from tkinter import Tk
from tkinter import filedialog
import sys
import os
import imageio
import PyQt5

gamma = 0.5  # gamma for improving contrast
highpass = 0.5  # sigma of high pass filter
lowpass = 20  # sigma of low pass filter

import sys


def apply_band_passfilter(imagefile, display=True):
    name_ex = os.path.basename(imagefile)
    filename_base, file_extension = os.path.splitext(name_ex)
    output_path = os.path.dirname(imagefile)

    im = imageio.imread(imagefile)
    im = im - np.min(im)  # remove background
    im_bp = gaussian(im, sigma=highpass) - 1.0 * gaussian(im, sigma=lowpass)  # band pass filter
    im_bp[im_bp < 0] = 0  # clamp all negative pixels to zero
    if display:
        plt.close('all')
        plt.ion()
        fig1 = plt.figure(1, (17, 7))
        spec = gridspec.GridSpec(ncols=2, nrows=1)  # , figure=fig1
        ax1 = fig1.add_subplot(spec[0, 0])
        ax2 = fig1.add_subplot(spec[0, 1], sharex=ax1, sharey=ax1)

        ax1.clear()
        ax1.set_axis_off()
        ax1.set_title('original')
        ax1.imshow(im ** gamma, cmap='hot')

        ax2.clear()
        ax2.set_axis_off()
        ax2.set_title('bandpass filtered')
        ax2.imshow(im_bp ** gamma, cmap='hot')
        plt.show()

    output_file = output_path + '/' + filename_base + '_bandpass.tif'
    im_bp = im_bp ** gamma
    im_bp = 256 * im_bp / np.max(im_bp)
    imageio.imsave(output_file, im_bp.astype('uint8'))


class FileDialog(PyQt5.QtWidgets.QFileDialog):
    def __init__(self, *args):
        PyQt5.QtWidgets.QFileDialog.__init__(self, *args)
        self.setOption(self.DontUseNativeDialog, True)
        self.setFileMode(self.ExistingFiles)
        btns = self.findChildren(PyQt5.QtWidgets.QPushButton)
        self.openBtn = [x for x in btns if 'open' in str(x.text()).lower()][0]
        self.openBtn.clicked.disconnect()
        self.openBtn.clicked.connect(self.openClicked)
        self.tree = self.findChild(PyQt5.QtWidgets.QTreeView)

    def openClicked(self):
        inds = self.tree.selectionModel().selectedIndexes()
        files = []
        for i in inds:
            if i.column() == 0:
                files.append(os.path.join(str(self.directory().absolutePath()), str(i.data())))
        self.selectedFiles = files
        print(self.selectedFiles)
        for file in self.selectedFiles:
            # if selection is a directory walk through all subdirectories and analyse all images therein
            if os.path.isdir(file):
                for root, subdir, files in os.walk(file):
                    for f in files:
                        if any([f.endswith(x) for x in [".tif", ".jpg"]]):
                            print("analysing", f)
                            apply_band_passfilter(os.path.join(root,f), display=False)

            else:
                if any([file.endswith(x) for x in [".tif", ".jpg"]]):
                    print("analysing", file)
                    apply_band_passfilter(file)
        self.hide()

        #PyQt5.QtCore.QCoreApplication.instance().quit() # exiting the program when calculation is done

    def filesSelected(self):
        return self.selectedFiles



app = PyQt5.QtWidgets.QApplication(sys.argv)
dialog = FileDialog()
# dialog.setFileMode(PyQt5.QtWidgets.QFileDialog.DirectoryOnly)
dialog.show()
# Start the event loop.
app.exec_()
sys.exit()




