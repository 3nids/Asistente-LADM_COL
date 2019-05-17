# -*- coding: utf-8 -*-
"""
/***************************************************************************
                              Asistente LADM_COL
                             --------------------
        begin                : 2019-04-11
        git sha              : :%H$
        copyright            : (C) 2017 by Jhon Galindo
        email                : jhonsigpjc@gmail.com
 ***************************************************************************/
/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License v3.0 as          *
 *   published by the Free Software Foundation.                            *
 *                                                                         *
 ***************************************************************************/
"""
import os
import stat

from asistente_ladm_col.utils.qt_utils import make_file_selector

from qgis.PyQt.QtCore import (Qt,
                              QSettings,
                              QCoreApplication,
                              QFile)
from qgis.PyQt.QtWidgets import (QDialog,
                                 QFileDialog,
                                 QSizePolicy,
                                 QGridLayout)
from qgis.core import (Qgis,
                       QgsMapLayerProxyModel,
                       QgsApplication,
                       QgsCoordinateReferenceSystem,
                       QgsWkbTypes)
from qgis.gui import QgsMessageBar

from ..config.help_strings import HelpStrings

from ..utils import get_ui_class

WIZARD_UI = get_ui_class('wiz_input_load_field_data_capture.ui')


class InputLoadFieldDataCaptureDialog(QDialog, WIZARD_UI):
    def __init__(self, iface, db, qgis_utils, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.iface = iface
        self.log = QgsApplication.messageLog()
        self._db = db
        self.qgis_utils = qgis_utils
        self.help_strings = HelpStrings()


        self.btn_browse_file_gdb.clicked.connect(
            make_file_selector(self.gdb_path, QCoreApplication.translate("DialogImportFromExcel",
                                  "Select the Excel file with data in the intermediate structure"),
                                   QCoreApplication.translate("DialogImportFromExcel",
                                                                      'Excel File (*.xlsx *.xls)')))

        self.btn_browse_file_gdb.clicked.connect(
            make_file_selector(self.gdb_path, QCoreApplication.translate("DialogImportFromExcel",
                                  "Select the Excel file with data in the intermediate structure"),
                                   QCoreApplication.translate("DialogImportFromExcel",
                                                                      'Excel File (*.xlsx *.xls)')))

    def show_help(self):
        self.qgis_utils.show_help("create_points")
