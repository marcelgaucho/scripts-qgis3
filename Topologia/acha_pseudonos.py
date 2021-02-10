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

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterString,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterVectorDestination)
import processing


class FindPseudonodes(QgsProcessingAlgorithm):
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

    INPUT = 'INPUT'
    OUTPUT = 'OUTPUT'
    TABLE = 'TABLE'
    TOLERANCE = 'TOLERANCE'
    PRIMARY_KEY = 'PRIMARY_KEY'
    FIELD_EXCLUDED = 'FIELD_EXCLUDED'
    


    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return FindPseudonodes()

    def name(self):
        return 'findpseudonodesquery'

    def displayName(self):
        return self.tr('Find Pseudonodes')

    def group(self):
        return self.tr('Topology Scripts')

    def groupId(self):
        return 'topologyscripts'

    def shortHelpString(self):
        return self.tr("Find pseudonodes for a line layer. The gometry field must be named geom. \n"
                        "The Input layer is one layer with the connection to the database. The Table parameter is the table name. " 
                        "It must be qualified by the shema, e.g., foo.test."
                       )

    def initAlgorithm(self, config=None):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # We add the input vector features source. It can have any kind of
        # geometry.
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                self.tr('Input layer (connection)'),
                [QgsProcessing.TypeVectorLine]
            )
        )

        # Tolerance - Default is 0.000001 (11 cm in Equator)
        self.addParameter(QgsProcessingParameterNumber(
            self.TOLERANCE,
            'Tolerance',
            QgsProcessingParameterNumber.Double,
            0.000001
        ))
        
        
        
        # We add a feature sink in which to store our processed features (this
        # usually takes the form of a newly created vector layer when the
        # algorithm is run in QGIS).
        self.addParameter(
            QgsProcessingParameterVectorDestination(
                self.OUTPUT,
                self.tr('Output layer')
            )
        )

        self.addParameter(QgsProcessingParameterString(self.TABLE,
                                                       self.tr('Table'),
                                                       defaultValue=''))

        # Excluded Field from analysis. Adjacent features with the different field 
        # attributes won't be considered pseudonodes                                                 
        self.addParameter(QgsProcessingParameterString(self.FIELD_EXCLUDED,
                                                       self.tr('Exluded Field'),
                                                       defaultValue=''))
                                                       
        # Input Primary Key
        self.addParameter(QgsProcessingParameterString(self.PRIMARY_KEY,
                                                       self.tr('Primary Key'),
                                                       defaultValue='id'))

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        output = self.parameterAsOutputLayer(parameters, self.OUTPUT, context)

        # DO SOMETHING 

        # Tolerance and Excluded Field
        tolerance = parameters[self.TOLERANCE]
        field_excluded = parameters[self.FIELD_EXCLUDED]
        #tolerance = 0.0000001 # Doesn't work, the value is passed as 0
        
        if field_excluded: 
            sql = ('SELECT DISTINCT ST_StartPoint(ST_GeometryN(T1.geom, 1)) AS geom FROM '  
                        f'{parameters[self.TABLE]} AS T1, {parameters[self.TABLE]} AS T2 ' 
                  f'WHERE T1.{parameters[self.PRIMARY_KEY]} != T2.{parameters[self.PRIMARY_KEY]} '
                  f'AND ST_DWithin(ST_StartPoint(ST_GeometryN(T1.geom, 1)), T2.geom, {tolerance}) AND ' 
                   '(ST_Distance(ST_StartPoint(ST_GeometryN(T1.geom, 1)), ST_EndPoint(ST_GeometryN(T2.geom, 1))) < '
                  f'{tolerance} OR ST_Distance(ST_StartPoint(ST_GeometryN(T1.geom, 1)), '
                  f'ST_StartPoint(ST_GeometryN(T2.geom, 1))) < {tolerance}) '
                  f'GROUP BY T1.{parameters[self.PRIMARY_KEY]} HAVING count(*) = 1 '
                  f"AND COALESCE(T1.{field_excluded}, 'NULL') = COALESCE(MAX(T2.{field_excluded}), 'NULL') "
                         'UNION '
                   'SELECT DISTINCT ST_EndPoint(ST_GeometryN(T1.geom, 1)) AS geom FROM '  
                        f'{parameters[self.TABLE]} AS T1, {parameters[self.TABLE]} AS T2 ' 
                  f'WHERE T1.{parameters[self.PRIMARY_KEY]} != T2.{parameters[self.PRIMARY_KEY]} '
                  f'AND ST_DWithin(ST_EndPoint(ST_GeometryN(T1.geom, 1)), T2.geom, {tolerance}) AND ' 
                   '(ST_Distance(ST_EndPoint(ST_GeometryN(T1.geom, 1)), ST_EndPoint(ST_GeometryN(T2.geom, 1))) < '
                  f'{tolerance} OR ST_Distance(ST_EndPoint(ST_GeometryN(T1.geom, 1)), '
                  f'ST_StartPoint(ST_GeometryN(T2.geom, 1))) < {tolerance}) '
                  f'GROUP BY T1.{parameters[self.PRIMARY_KEY]} HAVING count(*) = 1 '
                  f"AND COALESCE(T1.{field_excluded}, 'NULL') = COALESCE(MAX(T2.{field_excluded}), 'NULL') ")
        else:
            sql = ('SELECT DISTINCT ST_StartPoint(ST_GeometryN(T1.geom, 1)) AS geom FROM '  
                        f'{parameters[self.TABLE]} AS T1, {parameters[self.TABLE]} AS T2 ' 
                  f'WHERE T1.{parameters[self.PRIMARY_KEY]} != T2.{parameters[self.PRIMARY_KEY]} '
                  f'AND ST_DWithin(ST_StartPoint(ST_GeometryN(T1.geom, 1)), T2.geom, {tolerance}) AND ' 
                   '(ST_Distance(ST_StartPoint(ST_GeometryN(T1.geom, 1)), ST_EndPoint(ST_GeometryN(T2.geom, 1))) < '
                  f'{tolerance} OR ST_Distance(ST_StartPoint(ST_GeometryN(T1.geom, 1)), '
                  f'ST_StartPoint(ST_GeometryN(T2.geom, 1))) < {tolerance}) '
                  f'GROUP BY T1.{parameters[self.PRIMARY_KEY]} HAVING count(*) = 1 '
                         'UNION '
                   'SELECT DISTINCT ST_EndPoint(ST_GeometryN(T1.geom, 1)) AS geom FROM '  
                        f'{parameters[self.TABLE]} AS T1, {parameters[self.TABLE]} AS T2 ' 
                  f'WHERE T1.{parameters[self.PRIMARY_KEY]} != T2.{parameters[self.PRIMARY_KEY]} '
                  f'AND ST_DWithin(ST_EndPoint(ST_GeometryN(T1.geom, 1)), T2.geom, {tolerance}) AND ' 
                   '(ST_Distance(ST_EndPoint(ST_GeometryN(T1.geom, 1)), ST_EndPoint(ST_GeometryN(T2.geom, 1))) < '
                  f'{tolerance} OR ST_Distance(ST_EndPoint(ST_GeometryN(T1.geom, 1)), '
                  f'ST_StartPoint(ST_GeometryN(T2.geom, 1))) < {tolerance}) '
                  f'GROUP BY T1.{parameters[self.PRIMARY_KEY]} HAVING count(*) = 1 ')
                
        feedback.pushInfo(sql)

        found = processing.run("gdal:executesql",
                                   {'INPUT': parameters['INPUT'],
                                   'SQL':sql,
                                   'OUTPUT': output},
                                   context=context, feedback=feedback, is_child_algorithm=True)


        return {self.OUTPUT: found['OUTPUT']}
