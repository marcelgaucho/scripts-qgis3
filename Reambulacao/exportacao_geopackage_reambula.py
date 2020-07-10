# -*- coding: utf-8 -*-

"""
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

import sqlite3 as lite

from qgis.core import (QgsVectorLayer,
                       Qgis,
                       QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterString,
                       QgsProcessingParameterVectorLayer,
                       QgsDataSourceUri,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterRasterLayer,
                       QgsPointXY,
                       QgsProcessingParameterExtent,
                       QgsProcessingParameterVectorDestination,
                       QgsProcessingParameterRasterDestination,
                       QgsProcessingParameterFile,
                       QgsProcessingParameterFileDestination)

#from processing.algs.qgis.QgisAlgorithm import QgisAlgorithm
from processing.tools import postgis
import psycopg2
import subprocess 
from PyQt5.QtCore import QVariant





class ExportaGeopackageReambula(QgsProcessingAlgorithm):
    """
    This is an example algorithm that takes a vector layer and
    creates a new identical one.

    It is meant to be used as an example of how to create your own
    algorithms and explain methods and variables used to do it. An
    algorithm like this will be available in all elements, and there
    is not need for additional work.

    All Processing algorithms should extend the QgsProcessingAlgorithm
    class.
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.


    DATABASE = 'DATABASE'
    SCHEMA = 'SCHEMA'
    SHAPEFILE = 'SHAPEFILE'
    GEOPACKAGE = 'GEOPACKAGE'


    def createInstance(self):
        return ExportaGeopackageReambula()

    def name(self):
        return 'exportacao_geopackage_reambula'

    def displayName(self):
        return 'Exportacao Geopackage Reambula'

    def group(self):
        return 'Reambulacao'

    def groupId(self):
        return 'reambulacao'

    def shortHelpString(self):
        return """O algoritmo exporta um esquema para geopackage, com a opção de recorte pelo retângulo envolvente de uma camada. Usuário e senha do banco precisam estar salvos no QGIS."""

    def initAlgorithm(self, config=None):
        # Banco
        db_param = QgsProcessingParameterString(
            self.DATABASE,
            'Database (connection name)')
        db_param.setMetadata({
            'widget_wrapper': {
                'class': 'processing.gui.wrappers_postgis.ConnectionWidgetWrapper'}})
        self.addParameter(db_param)
        
        # Esquema
        schema_param = QgsProcessingParameterString(
            self.SCHEMA,
            'Schema (schema name)', '', False, False)
        schema_param.setMetadata({
            'widget_wrapper': {
                'class': 'processing.gui.wrappers_postgis.SchemaWidgetWrapper',
                'connection_param': self.DATABASE}})
        self.addParameter(schema_param)     
     
        # Shapefile
        self.addParameter(QgsProcessingParameterFile(self.SHAPEFILE, 'Shapefile de recorte', 0, 'shp', optional=True))
        
        # Geopackage
        self.addParameter(QgsProcessingParameterFileDestination(self.GEOPACKAGE, 'Geopackage', '*.gpkg'))
        
        
        
    def processAlgorithm(self, parameters, context, feedback):
        # Retrieving parameters
        connection = self.parameterAsString(parameters, self.DATABASE, context)
        db = postgis.GeoDB.from_name(connection)
        uri = db.uri
        schema = self.parameterAsString(parameters, self.SCHEMA, context)
        shape = parameters[self.SHAPEFILE]
        geopackage = parameters[self.GEOPACKAGE]
        feedback.pushInfo("shp = " + str(shape) + ' tipo = ' + str(type(shape)))
        


        # Execute ogr2ogr only in case the shape is Valid or no shape was provided
        # If no shape is passed, there is no clip
        shapev = QgsVectorLayer(shape, 'testando', 'ogr')
        if shapev.isValid() or shape == '':
            feedback.pushInfo("Valid shape")
        else:
            raise QgsProcessingException("Invalid shape")

        # Text to ogr2ogr
        extensao = shapev.extent()
        if shape == '':
            string_ogr = "ogr2ogr -f GPKG {} -overwrite -forceNullable {} ".format(geopackage, shape)
        else:
            string_ogr = "ogr2ogr -f GPKG {} -overwrite -forceNullable -spat {} {} {} {} ".format(geopackage, str(extensao.xMinimum()), str(extensao.yMinimum()), str(extensao.xMaximum()), str(extensao.yMaximum()))    
            
        input_ogr = "PG:\"host={} dbname={} schemas={} port={} user={} password={}\" ".format(uri.host(), uri.database(), schema, uri.port(), uri.username(), uri.password())
        total = string_ogr + input_ogr
        feedback.pushInfo('texto ogr = ' + total)

        # Export schema to geopackage
        try:
            processo = subprocess.run(total, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.DEVNULL)
        except subprocess.CalledProcessError as e:
            #feedback.pushInfo('output type = ' + str(type(e.stdout)))
            #feedback.pushInfo('erro type = ' + str(type(e.stderr)))
            #feedback.pushInfo('output = ' + str(e.stdout)) 
            #feedback.pushInfo('output = ' + str(e.stdout.decode('utf-8')))
            #feedback.pushInfo('erro = ' + str(e.stderr)) 
            #feedback.pushInfo('erro = ' + str(e.stderr.decode('utf-8')))
            raise QgsProcessingException(str(e.stderr.decode('utf-8')))



        # Connect with PostGIS database
        con = psycopg2.connect(user = uri.username(), password = uri.password(), 
                                       host = uri.host(), port = uri.port(), database = uri.database())

        feedback.pushInfo('Uri = ' + str(uri))
        feedback.pushInfo('Uri text = ' + uri.uri())         
        feedback.pushInfo('Connection = ' + str(con))
        feedback.pushInfo('')

        # Query columns with array type
        with con:
            select_schema_tables = "SELECT table_name FROM information_schema.tables " \
                                   "WHERE table_type = '{}' AND table_schema = '{}'".format('BASE TABLE', schema)
            
            feedback.pushInfo('consulta = ' + select_schema_tables)

                                    
            cur = con.cursor()
             
            cur.execute(select_schema_tables)
             
            rows = cur.fetchall()
 
            schema_tables = [table[0] for table in rows]
            feedback.pushInfo('schema tables = ' + str(schema_tables))
            feedback.pushInfo('')
            
            dict_table_arrcolumns = dict()
            
            feedback.pushInfo('Loop para gerar dicionário. Uma lista contendo nome das colunas ARRAY para cada tabela')
            for table in schema_tables:
                select_columns = "SELECT column_name FROM information_schema.columns " \
                                 "WHERE data_type = 'ARRAY' AND table_schema = '{}' AND table_name = '{}'".format(schema, table)
                
                feedback.pushInfo('consulta para tabela ' + table + ': ' + select_columns)
                        
                
                cur.execute(select_columns)
                
                rows = cur.fetchall()
                
                table_arrcolumns = [table[0] for table in rows]

                if table_arrcolumns != []:
                    dict_table_arrcolumns[table] = table_arrcolumns
                
            feedback.pushInfo('dicionario tabelas - colunas tipo array = ' + str(dict_table_arrcolumns))
            feedback.pushInfo('')
                        
        cur.close()
        con.close()


# =============================================================================
#         # Connect with Geopackage to UPDATE columns of array type 
#         feedback.pushInfo('Connecting to Geopackage to update array columns')
#         with lite.connect(geopackage) as con:
#             feedback.pushInfo('Con = ' + str(con))
#             
#             # Create cursor
#             cur = con.cursor()
#             
#             # Loop in dictionary of table:array columns
#             for table, arrcolumn in dict_table_arrcolumns.items():
#                 for column in arrcolumn:
#                     # Select query = """SELECT tipoproduto, '{' || substr(replace(tipoproduto, ')', '}'), 4) FROM {}""".format(table)
#                     update_query = """UPDATE {} SET {} = '{{' || substr(replace({}, ')', '}}'), 4)""".format(table, column, column)
#                     feedback.pushInfo('Update query = ' + update_query)
#                     cur.execute(update_query)
#                     con.commit()
# =============================================================================
                    
                    
        # UPDATE columns of array type inside Geopackage using PyQGIS
        for table, arrcolumn in dict_table_arrcolumns.items():
            uri_geopackage = geopackage + '|layername=' + table
            source = QgsVectorLayer(uri_geopackage, 'geopackage_layer', 'ogr')
            if not source.isValid():
                raise QgsProcessingException('Source layer not valid') 
            
            features = source.getFeatures()

            for f in features:
                fid = f.id()
                for column in arrcolumn:
                    fvalue = f[column]
                    if isinstance(fvalue, QVariant):
                        continue
                    mfvalue = '{' + fvalue.replace(')', '}')[3:]
                    findex = source.fields().indexFromName(column)
                    attr = {findex:mfvalue}
                    source.dataProvider().changeAttributeValues({ fid : attr })

                
                





        return {'resultado': 'exportado'}
    
    
