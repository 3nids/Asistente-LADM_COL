# -*- coding: utf-8 -*-
"""
/***************************************************************************
                              Asistente LADM_COL
                             --------------------
        begin                : 2018-03-06
        git sha              : :%H$
        copyright            : (C) 2018 by Sergio Ramírez (Incige SAS)
        email                : seralra96@gmail.com
 ***************************************************************************/
/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License v3.0 as          *
 *   published by the Free Software Foundation.                            *
 *                                                                         *
 ***************************************************************************/
"""
from functools import partial

from qgis.PyQt.QtCore import (QCoreApplication,
                              QSettings)
from qgis.PyQt.QtWidgets import QWizard
from qgis.core import (QgsVectorLayerUtils,
                       Qgis,
                       QgsMapLayerProxyModel,
                       QgsApplication)
from qgis.gui import QgsExpressionSelectionDialog

from .....config.general_config import PLUGIN_NAME
from .....config.help_strings import HelpStrings
from .....config.table_mapping_config import (ID_FIELD,
                                              RIGHT_TABLE,
                                              ADMINISTRATIVE_SOURCE_TABLE,
                                              RRR_SOURCE_RELATION_TABLE,
                                              RRR_SOURCE_RIGHT_FIELD,
                                              RRR_SOURCE_SOURCE_FIELD)
from .....utils import get_ui_class
from .....utils.qt_utils import (enable_next_wizard,
                                 disable_next_wizard)

WIZARD_UI = get_ui_class('wiz_create_right_cadastre.ui')


class CreateRightCadastreWizard(QWizard, WIZARD_UI):
    WIZARD_CREATES_SPATIAL_FEATURE = False
    WIZARD_NAME = "CreateRightCadastreWizard"
    WIZARD_TOOL_NAME = QCoreApplication.translate(WIZARD_NAME, "Create Right")

    def __init__(self, iface, db, qgis_utils, parent=None):
        QWizard.__init__(self, parent)
        self.setupUi(self)
        self.iface = iface
        self.log = QgsApplication.messageLog()
        self._db = db
        self.qgis_utils = qgis_utils
        self.help_strings = HelpStrings()

        self._layers = {
            RIGHT_TABLE: {'name': RIGHT_TABLE, 'geometry': None, 'layer': None},
            ADMINISTRATIVE_SOURCE_TABLE: {'name': ADMINISTRATIVE_SOURCE_TABLE, 'geometry': None, 'layer': None},
            RRR_SOURCE_RELATION_TABLE: {'name': RRR_SOURCE_RELATION_TABLE, 'geometry': None, 'layer': None}
        }

        self.restore_settings()
        self.rad_create_manually.toggled.connect(self.adjust_page_1_controls)
        self.adjust_page_1_controls()

        self.button(QWizard.NextButton).clicked.connect(self.adjust_page_2_controls)
        self.button(QWizard.FinishButton).clicked.connect(self.finished_dialog)
        self.button(QWizard.HelpButton).clicked.connect(self.show_help)
        self.rejected.connect(self.close_wizard)
        self.mMapLayerComboBox.setFilters(QgsMapLayerProxyModel.NoGeometry)

    def adjust_page_1_controls(self):
        self.cbo_mapping.clear()
        self.cbo_mapping.addItem("")
        self.cbo_mapping.addItems(self.qgis_utils.get_field_mappings_file_names(RIGHT_TABLE))

        if self.rad_refactor.isChecked():
            self.lbl_refactor_source.setEnabled(True)
            self.mMapLayerComboBox.setEnabled(True)
            self.lbl_field_mapping.setEnabled(True)
            self.cbo_mapping.setEnabled(True)
            disable_next_wizard(self)
            self.wizardPage1.setFinalPage(True)
            finish_button_text = QCoreApplication.translate(self.WIZARD_NAME, "Import")
            self.txt_help_page_1.setHtml(self.help_strings.get_refactor_help_string(RIGHT_TABLE, False))
            self.wizardPage1.setButtonText(QWizard.FinishButton, finish_button_text)
        elif self.rad_create_manually.isChecked():
            self.lbl_refactor_source.setEnabled(False)
            self.mMapLayerComboBox.setEnabled(False)
            self.lbl_field_mapping.setEnabled(False)
            self.cbo_mapping.setEnabled(False)
            enable_next_wizard(self)
            self.wizardPage1.setFinalPage(False)
            finish_button_text = QCoreApplication.translate(self.WIZARD_NAME, "Create")
            self.txt_help_page_1.setHtml(self.help_strings.WIZ_CREATE_RIGHT_CADASTRE_PAGE_1_OPTION_FORM)

        self.wizardPage2.setButtonText(QWizard.FinishButton,finish_button_text)

    def adjust_page_2_controls(self):
        self.button(self.FinishButton).setDisabled(True)
        self.disconnect_signals()
        self.txt_help_page_2.setHtml(self.help_strings.WIZ_CREATE_RIGHT_CADASTRE_PAGE_2)

        # Load layers
        result = self.prepare_feature_creation_layers()
        if result is None:
            # if there was a problem loading the layers
            message = QCoreApplication.translate(self.WIZARD_NAME,
                                                 "'{}' tool has been closed because there was a problem loading the requeries layers.").format(self.WIZARD_TOOL_NAME)
            self.close_wizard(message)
            return

        # Check if a previous features are selected
        self.check_selected_features()
        self.btn_admin_source_expression.clicked.connect(partial(self.select_features_by_expression, self._layers[ADMINISTRATIVE_SOURCE_TABLE]['layer']))

    def select_features_by_expression(self, layer):
        self.iface.setActiveLayer(layer)
        dlg_expression_selection = QgsExpressionSelectionDialog(layer)
        layer.selectionChanged.connect(self.check_selected_features)
        dlg_expression_selection.exec()
        layer.selectionChanged.disconnect(self.check_selected_features)

    def check_selected_features(self):
        # Check selected features in administrative source layer
        if self._layers[ADMINISTRATIVE_SOURCE_TABLE]['layer'].selectedFeatureCount():
            self.lb_admin_source.setText(QCoreApplication.translate(self.WIZARD_NAME, "<b>Administrative Source(s)</b>: {count} Feature Selected").format(count=self._layers[ADMINISTRATIVE_SOURCE_TABLE]['layer'].selectedFeatureCount()))
            self.button(self.FinishButton).setDisabled(False)
        else:
            self.lb_admin_source.setText(QCoreApplication.translate(self.WIZARD_NAME, "<b>Administrative Source(s)</b>: 0 Features Selected"))
            self.button(self.FinishButton).setDisabled(True)

    def finished_dialog(self):
        self.save_settings()

        if self.rad_refactor.isChecked():
            if self.mMapLayerComboBox.currentLayer() is not None:
                field_mapping = self.cbo_mapping.currentText()
                res_etl_model = self.qgis_utils.show_etl_model(self._db,
                                                               self.mMapLayerComboBox.currentLayer(),
                                                               RIGHT_TABLE,
                                                               field_mapping=field_mapping)

                if res_etl_model:
                    if field_mapping:
                        self.qgis_utils.delete_old_field_mapping(field_mapping)

                    self.qgis_utils.save_field_mapping(RIGHT_TABLE)
            else:
                self.iface.messageBar().pushMessage("Asistente LADM_COL",
                    QCoreApplication.translate(self.WIZARD_NAME,
                                               "Select a source layer to set the field mapping to '{}'.").format(RIGHT_TABLE),
                    Qgis.Warning)

        elif self.rad_create_manually.isChecked():
            self.prepare_feature_creation()

    def prepare_feature_creation(self):
        result = self.prepare_feature_creation_layers()
        if result is None:
            return
        self.edit_feature()

    def prepare_feature_creation_layers(self):
        # Load layers
        res_layers = self.qgis_utils.get_layers(self._db, self._layers, load=True)
        if res_layers is None:
            return

        # All layers were successfully loaded
        return True

    def close_wizard(self, message=None):
        if message is None:
            message = QCoreApplication.translate(self.WIZARD_NAME, "'{}' tool has been closed.").format(self.WIZARD_TOOL_NAME)
        self.iface.messageBar().pushMessage("Asistente LADM_COL", message, Qgis.Info)

        self.disconnect_signals()
        self.close()

    def disconnect_signals(self):
        # GUI Wizard
        signals = [self.btn_admin_source_expression.clicked]

        for signal in signals:
            try:
                signal.disconnect()
            except:
                pass

        # QGIS APP
        try:
            self._layers[RIGHT_TABLE]['layer'].featureAdded.disconnect()
        except:
            pass

        try:
            self._layers[RIGHT_TABLE]['layer'].committedFeaturesAdded.disconnect(self.finish_feature_creation)
        except:
            pass

    def edit_feature(self):
        self.iface.layerTreeView().setCurrentLayer(self._layers[RIGHT_TABLE]['layer'])
        self._layers[RIGHT_TABLE]['layer'].committedFeaturesAdded.connect(self.finish_feature_creation)

        if self._layers[ADMINISTRATIVE_SOURCE_TABLE]['layer'].selectedFeatureCount() >= 1:
            self.open_form(self._layers[RIGHT_TABLE]['layer'])
        else:
            message = QCoreApplication.translate(self.WIZARD_NAME, "Please select an Administrative source")
            self.close_wizard(message)

    def finish_feature_creation(self, layerId, features):
        message = QCoreApplication.translate(self.WIZARD_NAME,
                                             "'{}' tool has been closed because an error occurred while trying to save the data.").format(self.WIZARD_TOOL_NAME)

        if len(features) != 1:
            message = QCoreApplication.translate(self.WIZARD_NAME,
                                                 "'{}' tool has been closed. We should have got only one right... We cannot do anything with {} rights").format(self.WIZARD_TOOL_NAME, len(features))
            self.log.logMessage("We should have got only one right... We cannot do anything with {} right".format(len(features)), PLUGIN_NAME, Qgis.Warning)
        else:
            fid = features[0].id()
            administrative_source_ids = [f['t_id'] for f in self._layers[ADMINISTRATIVE_SOURCE_TABLE]['layer'].selectedFeatures()]

            if not self._layers[RIGHT_TABLE]['layer'].getFeature(fid).isValid():
                self.log.logMessage("Feature not found in layer Right...", PLUGIN_NAME, Qgis.Warning)
            else:
                right_id = self._layers[RIGHT_TABLE]['layer'].getFeature(fid)[ID_FIELD]

                # Fill rrrfuente table
                new_features = []
                for administrative_source_id in administrative_source_ids:
                    new_feature = QgsVectorLayerUtils().createFeature(self._layers[RRR_SOURCE_RELATION_TABLE]['layer'])
                    new_feature.setAttribute(RRR_SOURCE_SOURCE_FIELD, administrative_source_id)
                    new_feature.setAttribute(RRR_SOURCE_RIGHT_FIELD, right_id)
                    self.log.logMessage("Saving Administrative_source-Right: {}-{}".format(administrative_source_id, right_id), PLUGIN_NAME, Qgis.Info)
                    new_features.append(new_feature)

                self._layers[RRR_SOURCE_RELATION_TABLE]['layer'].dataProvider().addFeatures(new_features)
                message = QCoreApplication.translate(self.WIZARD_NAME,
                                                     "The new right (t_id={}) was successfully created and associated with its corresponding administrative source (t_id={})!").format(right_id, ", ".join([str(b) for b in administrative_source_ids]))

        self._layers[RIGHT_TABLE]['layer'].committedFeaturesAdded.disconnect(self.finish_feature_creation)
        self.log.logMessage("Right's committedFeaturesAdded SIGNAL disconnected", PLUGIN_NAME, Qgis.Info)
        self.close_wizard(message)

    def open_form(self, layer):
        if not layer.isEditable():
            layer.startEditing()

        if self.WIZARD_CREATES_SPATIAL_FEATURE:
            # action add feature
            self.qgis_utils.suppress_form(layer, True)
            self.iface.actionAddFeature().trigger()

            # Shows the form when the feature is created
            layer.featureAdded.connect(partial(self.exec_form, layer))

        else:
            self.exec_form(layer)

    def exec_form(self, layer):
        try:
            # Disconnect signal to prevent add features
            layer.featureAdded.disconnect()
            self.log.logMessage("Feature added SIGNAL disconnected", PLUGIN_NAME, Qgis.Info)
        except:
            pass

        feature = self.qgis_utils.get_new_feature(layer)
        dialog = self.iface.getFeatureForm(layer, feature)
        dialog.rejected.connect(self.form_rejected)
        dialog.setModal(True)

        if dialog.exec_():
            saved = layer.commitChanges()

            if not saved:
                layer.rollBack()
                self.iface.messageBar().pushMessage("Asistente LADM_COL",
                                                    QCoreApplication.translate(self.WIZARD_NAME,
                                                                               "Error while saving changes. Right could not be created."),
                                                    Qgis.Warning)

                for e in layer.commitErrors():
                    self.log.logMessage("Commit error: {}".format(e), PLUGIN_NAME, Qgis.Warning)

            self.iface.mapCanvas().refresh()
        else:
            layer.rollBack()

    def form_rejected(self):
        message = QCoreApplication.translate(self.WIZARD_NAME,
                                             "'{}' tool has been closed because you just closed the form.").format(self.WIZARD_TOOL_NAME)
        self.close_wizard(message)

    def save_settings(self):
        settings = QSettings()
        settings.setValue('Asistente-LADM_COL/wizards/right_load_data_type', 'create_manually' if self.rad_create_manually.isChecked() else 'refactor')

    def restore_settings(self):
        settings = QSettings()

        load_data_type = settings.value('Asistente-LADM_COL/wizards/right_load_data_type') or 'create_manually'
        if load_data_type == 'refactor':
            self.rad_refactor.setChecked(True)
        else:
            self.rad_create_manually.setChecked(True)

    def show_help(self):
        self.qgis_utils.show_help("create_right")