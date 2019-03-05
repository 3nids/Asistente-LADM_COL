from .db_admin import DbAdmin
from .gpkg_config_panel import GpkgConfigPanel
from ..lib.dbconnector.gpkg_connector import GPKGConnector
from .enum_action_type import EnumActionType
from QgisModelBaker.libili2db.ili2dbconfig import (SchemaImportConfiguration,
                                                   ImportDataConfiguration,
                                                   ExportConfiguration,
                                                   BaseConfiguration)

class GpkgAdmin(DbAdmin):

    def __init__(self):
        self._mode = "gpkg"

    def get_id(self):
        return 'gpkg'

    def get_name(self):
        return 'GeoPackage'

    def get_model_baker_tool_name(self):
        return "ili2gpkg"

    def get_config_panel(self):
        return GpkgConfigPanel()

    def get_db_connector(self, parameters):
        return GPKGConnector(None, conn_dict=parameters)

    def get_schema_import_configuration(self, params):
        configuration = SchemaImportConfiguration()
        configuration.tool_name = 'gpkg'
        configuration.dbfile = params['dbfile']

        return configuration

    def get_import_configuration(self, params):
        configuration = ImportDataConfiguration()
        configuration.dbfile = params['dbfile']
        return configuration

    def get_export_configuration(self, params):
        configuration = ExportConfiguration()
        configuration.dbfile = params['dbfile']
        return configuration
