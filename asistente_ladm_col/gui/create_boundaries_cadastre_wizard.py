# -*- coding: utf-8 -*-
"""
/***************************************************************************
                              Asistente LADM_COL
                             --------------------
        begin                : 2017-11-14
        git sha              : :%H$
        copyright            : (C) 2017 by Germán Carrillo (BSF Swissphoto)
        email                : gcarrillo@linuxmail.org
 ***************************************************************************/
/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License v3.0 as          *
 *   published by the Free Software Foundation.                            *
 *                                                                         *
 ***************************************************************************/
"""
from qgis.core import (QgsProject, QgsVectorLayer, QgsEditFormConfig,
                       QgsSnappingConfig, QgsTolerance, QgsFeature, Qgis,
                       QgsMapLayerProxyModel, QgsWkbTypes)
from qgis.PyQt.QtCore import Qt, QPoint, QCoreApplication, QSettings
from qgis.PyQt.QtWidgets import QAction, QWizard

from ..utils import get_ui_class
from ..config.table_mapping_config import BOUNDARY_TABLE, BOUNDARY_POINT_TABLE
from ..config.help_strings import HelpStrings
from ..config.general_config import FIELD_MAPPING_PATH

WIZARD_UI = get_ui_class('wiz_create_boundaries_cadastre.ui')

class CreateBoundariesCadastreWizard(QWizard, WIZARD_UI):
    def __init__(self, iface, db, qgis_utils, parent=None):
        QWizard.__init__(self, parent)
        self.setupUi(self)
        self.iface = iface
        self._db = db
        self.qgis_utils = qgis_utils
        self.help_strings = HelpStrings()

        self.restore_settings()

        self.rad_digitizing.toggled.connect(self.adjust_page_1_controls)
        self.adjust_page_1_controls()
        self.button(QWizard.FinishButton).clicked.connect(self.finished_dialog)
        self.button(QWizard.HelpButton).clicked.connect(self.show_help)

        self.mMapLayerComboBox.setFilters(QgsMapLayerProxyModel.LineLayer)

    def adjust_page_1_controls(self):

        combox_data = self.qgis_utils.fields_mapping(BOUNDARY_TABLE)

        self.cbo_mapping.clear()
        self.cbo_mapping.addItem("")

        self.cbo_mapping.addItems(combox_data)

        if self.rad_refactor.isChecked():
            self.lbl_refactor_source.setEnabled(True)
            self.mMapLayerComboBox.setEnabled(True)
            self.lbl_field_mapping.setEnabled(True)
            self.cbo_mapping.setEnabled(True)
            finish_button_text = QCoreApplication.translate("CreateBoundariesCadastreWizard", "Import")
            self.txt_help_page_1.setHtml(self.help_strings.get_refactor_help_string(BOUNDARY_TABLE, False))

        elif self.rad_digitizing.isChecked():
            self.lbl_refactor_source.setEnabled(False)
            self.mMapLayerComboBox.setEnabled(False)
            self.lbl_field_mapping.setEnabled(False)
            self.cbo_mapping.setEnabled(False)
            finish_button_text = QCoreApplication.translate("CreateBoundariesCadastreWizard", "Start")
            self.txt_help_page_1.setHtml(self.help_strings.WIZ_DEFINE_BOUNDARIES_CADASTRE_PAGE_1_OPTION_DIGITIZE)

        self.wizardPage1.setButtonText(QWizard.FinishButton,
                                       QCoreApplication.translate("CreateBoundariesCadastreWizard",
                                       finish_button_text))

    def finished_dialog(self):
        self.save_settings()

        if self.rad_refactor.isChecked():

            if self.cbo_mapping.currentText() is not "":
                save_field_mapping = self.cbo_mapping.currentText()
            else:
                save_field_mapping = None

            if self.mMapLayerComboBox.currentLayer() is not None:
                etl_model_feature_count = self.qgis_utils.show_etl_model(self._db,
                                               self.mMapLayerComboBox.currentLayer(),
                                               BOUNDARY_TABLE,
                                               save_field_mapping)

                if etl_model_feature_count[0] != etl_model_feature_count[1]:
                    self.qgis_utils.func_save_field_mapping(BOUNDARY_TABLE)
                    if save_field_mapping != None:
                        self.qgis_utils.replace_field_mapping(save_field_mapping, BOUNDARY_TABLE)

            else:
                self.iface.messageBar().pushMessage("Asistente LADM_COL",
                    QCoreApplication.translate("CreateBoundariesCadastreWizard",
                                               "Select a source layer to set the field mapping to '{}'.").format(BOUNDARY_TABLE),
                    Qgis.Warning)

        elif self.rad_digitizing.isChecked():
            self.prepare_boundary_creation()

    def prepare_boundary_creation(self):
        # Load layers
        res_layers = self.qgis_utils.get_layers(self._db, {
            BOUNDARY_TABLE: {'name': BOUNDARY_TABLE, 'geometry': QgsWkbTypes.LineGeometry},
            BOUNDARY_POINT_TABLE: {'name': BOUNDARY_POINT_TABLE, 'geometry': QgsWkbTypes.PointGeometry}}, load=True)

        boundary_layer = res_layers[BOUNDARY_TABLE]
        if boundary_layer is None:
            self.iface.messageBar().pushMessage("Asistente LADM_COL",
                QCoreApplication.translate("CreateBoundariesCadastreWizard",
                                           "Boundary layer couldn't be found... {}").format(self._db.get_description()),
                Qgis.Warning)
            return

        boundary_point_layer = res_layers[BOUNDARY_POINT_TABLE]
        if boundary_point_layer is None:
            self.iface.messageBar().pushMessage("Asistente LADM_COL",
                QCoreApplication.translate("CreateBoundariesCadastreWizard",
                                           "Boundary point layer couldn't be found... {}").format(self._db.get_description()),
                Qgis.Warning)
            return

        # Disable transactions groups
        QgsProject.instance().setAutoTransaction(False)

        # Configure Snapping
        snapping = QgsProject.instance().snappingConfig()
        snapping.setEnabled(True)
        snapping.setMode(QgsSnappingConfig.AdvancedConfiguration)
        snapping.setIndividualLayerSettings(boundary_point_layer,
                                            QgsSnappingConfig.IndividualLayerSettings(True,
                                                QgsSnappingConfig.Vertex, 15, QgsTolerance.Pixels))
        snapping.setIndividualLayerSettings(boundary_layer,
                                            QgsSnappingConfig.IndividualLayerSettings(True,
                                                QgsSnappingConfig.Vertex, 15, QgsTolerance.Pixels))

        QgsProject.instance().setSnappingConfig(snapping)

        # Suppress feature form
        form_config = boundary_layer.editFormConfig()
        form_config.setSuppress(QgsEditFormConfig.SuppressOn)
        boundary_layer.setEditFormConfig(form_config)

        # Enable edition mode
        self.iface.layerTreeView().setCurrentLayer(boundary_layer)
        boundary_layer.startEditing()
        self.iface.actionAddFeature().trigger()

        self.iface.messageBar().pushMessage("Asistente LADM_COL",
            QCoreApplication.translate("CreateBoundariesCadastreWizard",
                                       "You can now start capturing boundaries clicking on the map..."),
            Qgis.Info)

    def save_settings(self):
        settings = QSettings()
        settings.setValue('Asistente-LADM_COL/wizards/boundary_load_data_type', 'digitizing' if self.rad_digitizing.isChecked() else 'refactor')

    def restore_settings(self):
        settings = QSettings()

        load_data_type = settings.value('Asistente-LADM_COL/wizards/boundary_load_data_type') or 'digitizing'
        if load_data_type == 'refactor':
            self.rad_refactor.setChecked(True)
        else:
            self.rad_digitizing.setChecked(True)

    def show_help(self):
        self.qgis_utils.show_help("create_boundaries")
