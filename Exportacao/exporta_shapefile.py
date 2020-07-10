# -*- coding: utf-8 -*-
'''
Created on 29 de jul de 2019

@author: marcel.rotunno
'''

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





class ExportaShapefile(QgsProcessingAlgorithm):
    DATABASE = 'DATABASE'
    SCHEMA = 'SCHEMA'
    SHAPEFILE_FOLDER = 'SHAPEFILE_FOLDER'
    SHAPEFILE_CLIP = 'SHAPEFILE_CLIP'


    def createInstance(self):
        return ExportaShapefile()

    def name(self):
        return 'exporta_shapefile'

    def displayName(self):
        return 'Exporta Shapefile'

    def group(self):
        return 'Exportacao'

    def groupId(self):
        return 'exportacao'

    def shortHelpString(self):
        return """O algoritmo busca exportar um esquema para shapefiles. Usuário e senha do banco precisam estar salvos no QGIS."""

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
            'Schema (schema name)', 'bc250_base', False, False)
        schema_param.setMetadata({
            'widget_wrapper': {
                'class': 'processing.gui.wrappers_postgis.SchemaWidgetWrapper',
                'connection_param': self.DATABASE}})
        self.addParameter(schema_param)     
     
        # Diretório de Shapefiles
        self.addParameter(QgsProcessingParameterFile(self.SHAPEFILE_FOLDER, "Shapefile Folder", 1, 'shp', optional=False))
        
        # Shapefile de recorte
        self.addParameter(QgsProcessingParameterFile(self.SHAPEFILE_CLIP, 'Shapefile to clip', 0, 'shp', optional=True))
 
        
    def processAlgorithm(self, parameters, context, feedback):
        # Retrieving parameters
        connection = self.parameterAsString(parameters, self.DATABASE, context)
        db = postgis.GeoDB.from_name(connection)
        uri = db.uri
        schema = self.parameterAsString(parameters, self.SCHEMA, context)
        shapef = parameters[self.SHAPEFILE_FOLDER]
        shapec = parameters[self.SHAPEFILE_CLIP]
        feedback.pushInfo("shp folder = " + str(shapef))
        feedback.pushInfo("shp clip = " + str(shapec))
        feedback.pushInfo("uri = " + str(uri))


        # Execute ogr2ogr only in case the clip shape is Valid or no shape was provided
        # If no shape is passed, there is no clip
        shapev = QgsVectorLayer(shapec, 'testando', 'ogr')
        if shapev.isValid() or shapec == '':
            feedback.pushInfo("Valid shape")
        else:
            raise QgsProcessingException("Invalid shape")

        # Text to ogr2ogr
        if shapec == '':
            string_ogr = "ogr2ogr  -fieldTypeToString IntegerList,Integer64List,RealList,StringList -lco ENCODING=UTF-8 -f \"ESRI Shapefile\" {} -overwrite ".format(shapef)
        else:
            string_ogr = "ogr2ogr  -fieldTypeToString IntegerList,Integer64List,RealList,StringList -lco ENCODING=UTF-8 -f \"ESRI Shapefile\" {} -clipsrc {} -overwrite ".format(shapef, shapec)    
            
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