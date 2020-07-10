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
import processing
from qgis.core import (QgsProcessingAlgorithm,
                       QgsProcessingParameterVectorLayer,
                       QgsProcessingParameterFeatureSink,
                       QgsFeatureSink
                       )

class ConfereReambAtributos(QgsProcessingAlgorithm):
    IDA = 'Ida'
    VOLTA = 'Volta'
    OUTPUT = 'Output'


    def createInstance(self):
        return ConfereReambAtributos()

    def name(self):
        return 'confere_reamb_atributos'

    def displayName(self):
        return 'Confere Reamb Atributos'
    
    def groupId(self):
        return 'reambulacao'
        
    def group(self):
        return 'Reambulacao'
    
    def initAlgorithm(self, config=None):
        # Camada de ida
        self.addParameter(QgsProcessingParameterVectorLayer(
            self.IDA,
            'Camada de ida da reambulação'))
            
        # Camada de volta
        self.addParameter(QgsProcessingParameterVectorLayer(
            self.VOLTA,
            'Camada de volta da reambulação'))  
  
        # Camada de resultado
        self.addParameter(QgsProcessingParameterFeatureSink(
            self.OUTPUT,
            'Output'))         
        
            
    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        feedback.pushInfo('parametros = ' + str(parameters))
        #feedback.pushInfo('parametros = ' + str(parameters[self.OUTPUT]))
        
        # Retrieving parameters
        ida = self.parameterAsVectorLayer(parameters, self.IDA, context)
        volta = self.parameterAsVectorLayer(parameters, self.VOLTA, context)
        #output = self.parameterAsOutputLayer(parameters, self.OUTPUT, context)
        
        feedback.pushInfo('Dados de conexão')
        feedback.pushInfo('ida = ' + str(ida))
        feedback.pushInfo('volta = ' + str(volta))
        #feedback.pushInfo('output = ' + str(output))
        
        # Fazendo join para retornar aquelas feições coincidentes
        resultado = processing.run("qgis:joinattributesbylocation", {'INPUT':ida, 'JOIN':volta, 'PREDICATE':2, 'METHOD': 0, 'DISCARD_NONMATCHING': True, 'OUTPUT':'memory:'}, context=context, feedback=feedback)
        
        # Camada do resultado
        camada = resultado['OUTPUT']
        feedback.pushInfo('resultadooo = ' + str(camada))
        #feedback.pushInfo('joined = ' + str(resultado))
        
        # Campos da junção e campos originais
        campos_nomes = [campo.name() for campo in camada.fields()]
        campos_nomes_2 = [elemento for elemento in campos_nomes if elemento[-2:] == '_2']
        campos_nomes_original = [elemento for elemento in campos_nomes if elemento not in campos_nomes_2]

        # Comparação dos atributos
        feicoes_mudanca_atributos = []
        for feicao in camada.getFeatures():
            for i in range(len(campos_nomes_original)):
                #print(feicao[campos_nomes_original[i]], feicao[campos_nomes_2[i]])
                if feicao[campos_nomes_original[i]] != feicao[campos_nomes_2[i]]:
                    #print(feicao[campos_nomes_original[i]], feicao[campos_nomes_2[i]])
                    feicoes_mudanca_atributos.append(feicao)
                    #print("Atributos diferentes!")
                    break
            
        
        # Geração da camada de saída
        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            camada.fields(),
            camada.wkbType(),
            camada.sourceCrs()
        )
        
        feedback.pushInfo('sink = ' + str(sink))
        feedback.pushInfo('sink id = ' + str(dest_id))
        
        sink.addFeatures(feicoes_mudanca_atributos, QgsFeatureSink.FastInsert)
            

        return {self.OUTPUT: dest_id}
