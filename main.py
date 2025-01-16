#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys
from PyQt5 import QtCore,QtGui,QtWidgets

from window import Window

print(QtCore.QT_VERSION_STR)

app=QtWidgets.QApplication(sys.argv)

position=0,0
dimension=600,400
mw=Window(position,dimension)
mw.show()

sys.exit(app.exec_())
