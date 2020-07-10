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
import processing
import psycopg2
import subprocess 





class ExportaGeopackage(QgsProcessingAlgorithm):
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
        return ExportaGeopackage()

    def name(self):
        return 'exporta_geopackage'

    def displayName(self):
        return 'Exporta Geopackage'

    def group(self):
        return 'Exportacao'

    def groupId(self):
        return 'exportacao'

    def shortHelpString(self):
        return """O algoritmo busca exportar um esquema para geopackage. Usuário e senha do banco precisam estar salvos no QGIS."""

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
            'Schema (schema name)', 'bc250_base', False, True)
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
        feedback.pushInfo("shp = " + str(shape))


        # Execute ogr2ogr only in case the shape is Valid or no shape was provided
        # If no shape is passed, there is no clip
        shapev = QgsVectorLayer(shape, 'testando', 'ogr')
        if shapev.isValid() or shape == '':
            feedback.pushInfo("Valid shape")
        else:
            raise QgsProcessingException("Invalid shape")

        # Text to ogr2ogr
        if shape == '':
            string_ogr = "ogr2ogr -f GPKG {} -overwrite {} ".format(geopackage, shape)
        else:
            string_ogr = "ogr2ogr -f GPKG {} -overwrite -clipsrc {} ".format(geopackage, shape)    
            
        input_ogr = "PG:\"host={} dbname={} schemas={} port={} user={} password={}\" ".format(uri.host(), uri.database(), schema, uri.port(), uri.username(), uri.password())
        total = string_ogr + input_ogr
        feedback.pushInfo('texto ogr = ' + total)

        # Export schema to geopackage
        
        try:
            processo = subprocess.run(total, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError as e:
            #feedback.pushInfo('output type = ' + str(type(e.stdout)))
            #feedback.pushInfo('erro type = ' + str(type(e.stderr)))
            #feedback.pushInfo('output = ' + str(e.stdout)) 
            #feedback.pushInfo('output = ' + str(e.stdout.decode('utf-8')))
            #feedback.pushInfo('erro = ' + str(e.stderr)) 
            #feedback.pushInfo('erro = ' + str(e.stderr.decode('utf-8')))
            raise QgsProcessingException(str(e.stderr.decode('utf-8')))

        
        

        return {'resultado': 'exportado'}