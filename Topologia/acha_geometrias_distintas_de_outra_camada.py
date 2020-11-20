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
                       QgsProcessingParameterString)
import processing


class FindDifferentGeometriesFromOtherLayer(QgsProcessingAlgorithm):
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

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return FindDifferentGeometriesFromOtherLayer()

    def name(self):
        return 'finddifferentgeometriesfromotherlayer'

    def displayName(self):
        return self.tr('Find Different Geometries From Other Layer')

    def group(self):
        return self.tr('Topology Scripts')

    def groupId(self):
        return 'topologyscripts'

    def shortHelpString(self):
        return self.tr("Find geometries of one layer that are different from geometries on another layer. It works for layers in sql databases, like postgis and geopackage, "
                        "with the geometry field named geom. \n"
                        "The Input layer is one layer with the connection to the database. The Table parameter is the table name. For schema-based databases, "
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
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Output layer')
            )
        )

        # Input tables
        self.addParameter(QgsProcessingParameterString(self.TABLE,
                                                       self.tr('Table'),
                                                       defaultValue=''))

        self.addParameter(QgsProcessingParameterString(self.TABLE2,
                                                       self.tr('Table2'),
                                                       defaultValue=''))                                                       



    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        

        # DO SOMETHING       
        sql = (f'SELECT T1.geom FROM {parameters[self.TABLE]} AS T1 LEFT JOIN {parameters[self.TABLE2]} AS T2 '  
               f'ON T1.geom && T2.geom AND ST_Equals(T1.geom, T2.geom) WHERE T2.geom IS NULL')
               
                
        feedback.pushInfo(sql)

        find_pseudo = processing.run("gdal:executesql",
                                   {'INPUT': parameters['INPUT'],
                                   'SQL':sql,
                                   'OUTPUT': parameters['OUTPUT']},
                                   context=context, feedback=feedback, is_child_algorithm=True)


        return {self.OUTPUT: find_pseudo['OUTPUT']}
