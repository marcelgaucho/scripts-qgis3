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
                       QgsProcessingParameterVectorDestination,
                       QgsProcessingParameterNumber)
import processing


class FindKNearestNeighborsWithinDistance(QgsProcessingAlgorithm):
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
    TABLE2 = 'TABLE2'
    PRIMARY_KEY = 'PRIMARY_KEY'
    PRIMARY_KEY2 = 'PRIMARY_KEY2'
    TOLERANCE = 'TOLERANCE'
    KNEIGHBORS = 'KNEIGHBORS'

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return FindKNearestNeighborsWithinDistance()

    def name(self):
        return 'findknearestneighborswithindistance'

    def displayName(self):
        return self.tr('Find K Nearest Neighbors Whithin Distance')

    def group(self):
        return self.tr('Topology Scripts')

    def groupId(self):
        return 'topologyscripts'

    def shortHelpString(self):
        return self.tr("Find the K Nearest Neighbors within certain distance of the features. It takes 2 tables (layers). "
                       "The first is the input layer and the second is the neighbors layer. The features returned are from "
                       "the neighbors layer. For each feature of the input layer, the K nearest features from the neighbors layer "
                       "that are within the threshold distance are returned. \n"
                       "It works for layers in a PostGIS database, "
                       "with the geometry field named geom. \n"
                       "The Input layer (connection) is one layer with the connection to the database. The Table parameters are the table names. For schema-based databases, "
                       " it must be qualified by the schema, e.g., foo.test."
                       )

    def initAlgorithm(self, config=None):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # We add the input vector features source. It can have polygon geometry
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                self.tr('Input layer (connection)'),
                [QgsProcessing.TypeVectorAnyGeometry]
            )
        )

        
        # We add a feature sink in which to store our processed features (this
        # usually takes the form of a newly created vector layer when the
        # algorithm is run in QGIS).
        self.addParameter(
            QgsProcessingParameterVectorDestination(
                self.OUTPUT,
                self.tr('Output layer')
            )
        )

        # Input tables
        self.addParameter(QgsProcessingParameterString(self.TABLE,
                                                       self.tr('Table (Input Layer)'),
                                                       defaultValue=''))

        self.addParameter(QgsProcessingParameterString(self.TABLE2,
                                                       self.tr('Table2 (Neighbors Layer)'),
                                                       defaultValue=''))

        # Input Primary Keys
        self.addParameter(QgsProcessingParameterString(self.PRIMARY_KEY,
                                                       self.tr('Primary Key (Table)'),
                                                       defaultValue='id'))

        self.addParameter(QgsProcessingParameterString(self.PRIMARY_KEY2,
                                                       self.tr('Primary Key (Table2)'),
                                                       defaultValue='id'))

        # Tolerance - Default is in degrees and is approximately 111 meters in Equator
        self.addParameter(QgsProcessingParameterNumber(
            self.TOLERANCE,
            'Tolerance',
            QgsProcessingParameterNumber.Double,
            0.001
        ))                                                       

        # K Neighbors. Number of neighbors to find within distance. Default is 1
        self.addParameter(QgsProcessingParameterNumber(
            self.KNEIGHBORS,
            'Number of neighbors',
            QgsProcessingParameterNumber.Integer,
            1
        ))

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        output = self.parameterAsOutputLayer(parameters, self.OUTPUT, context)

        # DO SOMETHING 
        """
            SELECT id, idN, distance, rank FROM (
                SELECT T1.{parameters[self.PRIMARY_KEY]} AS id, T2.{parameters[self.PRIMARY_KEY2]} AS idN,
                       ST_Distance(T1.geom, T2.geom) AS distance, RANK() OVER win AS rank
                FROM {parameters[self.TABLE]} AS T1 JOIN {parameters[self.TABLE2]} AS T2
                ON ST_DWithin(T1.geom, T2.geom, {parameters[self.TOLERANCE]})
                WINDOW win AS (PARTITION BY T1.{parameters[self.PRIMARY_KEY]} ORDER BY ST_Distance(T1.geom, T2.geom) ASC)
                ) AS table
            WHERE rank <= {parameters[self.KNEIGHBORS]}
        """
        sql = (f'SELECT id, idN, distance, rank, geom FROM ( '
                    f'SELECT T1.{parameters[self.PRIMARY_KEY]} AS id, T2.{parameters[self.PRIMARY_KEY2]} AS idN, '  
                           f'ST_Distance(T1.geom, T2.geom) AS distance, RANK() OVER win AS rank, T2.geom '
                    f'FROM {parameters[self.TABLE]} AS T1 JOIN {parameters[self.TABLE2]} AS T2 '
                    f'ON ST_DWithin(T1.geom, T2.geom, {parameters[self.TOLERANCE]}) '
                    f'WINDOW win AS (PARTITION BY T1.{parameters[self.PRIMARY_KEY]} ORDER BY ST_Distance(T1.geom, T2.geom) ASC) '
                    f') AS foo '
               f'WHERE rank <= {parameters[self.KNEIGHBORS]} ')         
               
                
        feedback.pushInfo(sql)

        find_pseudo = processing.run("gdal:executesql",
                                   {'INPUT': parameters['INPUT'],
                                   'SQL':sql,
                                   'OUTPUT': output},
                                   context=context, feedback=feedback, is_child_algorithm=True)


        return {self.OUTPUT: find_pseudo['OUTPUT']}
