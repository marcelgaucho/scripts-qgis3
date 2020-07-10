from qgis.PyQt.QtCore import QCoreApplication, QVariant
from qgis.core import *

'''
# Get list of selected features in camada _filtro
def selectionPK(camada, col_chave_primaria):
    if len(camada.selectedFeatures()) == 0:
        raise processing.GeoAlgorithmExecutionException(u'camada sem selecao')
        
    selecao = camada.selectedFeatures()
    selecao_id = [str(feicao[col_chave_primaria]) for feicao in selecao]
    #print "selecao_id=", selecao_id
    return ", ".join(selecao_id)

selecao = selectionPK(camada_filtro, chave_primaria_filtro)
print selecao
'''

                       
class ExAlgo(QgsProcessingAlgorithm):
    INPUT = 'Input'
    FILTER = 'Filter'
    INPUT_PK = 'Input_PK'
    FILTER_PK = 'Filter_PK'
    
 
    def __init__(self):
        super().__init__()
 
    def name(self):
        return "filtragem_camada"
     
    def displayName(self):
        return "Filtragem de Camada"
 
    def group(self):
        return "BC250"
 
    def groupId(self):
        return "bc250"
 
    def shortHelpString(self):
        return "Filter a PostGIS layer where it intersects other PostGIS polygon layer providing the primary keys of the 2 layers."
 
    def helpUrl(self):
        return "https://qgis.org"
         
    def createInstance(self):
        #return type(self)()
        return ExAlgo()
   
    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterVectorLayer(
            self.INPUT,
            'Input',
            [QgsProcessing.TypeVectorAnyGeometry]))
            
        self.addParameter(QgsProcessingParameterVectorLayer(
            self.FILTER,
            'Filter',
            [QgsProcessing.TypeVectorPolygon]))    
        
        self.addParameter(QgsProcessingParameterString(
            self.INPUT_PK,
            "Input_PK",
            "id"))
            
        self.addParameter(QgsProcessingParameterString(
            self.FILTER_PK,
            "Filter_PK",
            "id"))

    def processAlgorithm(self, parameters, context, feedback):
        # Retrieve sources as vector layers
        input_source = self.parameterAsVectorLayer(parameters, self.INPUT, context)
        filter_source = self.parameterAsVectorLayer(parameters, self.FILTER, context)        

        # Debugging info
        feedback.pushInfo('input_source1 = ' + str(input_source))
        feedback.pushInfo('filter_source1 = ' + str(filter_source))
        

        # Selected features from filter source
        selecao = filter_source.getSelectedFeatures()
        
        chave_primaria_entrada = parameters[self.INPUT_PK]
        chave_primaria_filtro = parameters[self.FILTER_PK]
        
        feedback.pushInfo('chave primária entrada = ' + chave_primaria_entrada)
        selecao_id = [str(feicao[chave_primaria_filtro]) for feicao in selecao]
        
        for i in selecao_id:
            feedback.pushInfo(i)
        
        
        selecao_id = ", ".join(selecao_id)
        
        # Get table names of layers
        uri_entrada = QgsDataSourceUri(input_source.dataProvider().dataSourceUri())
        uri_filtro = QgsDataSourceUri(filter_source.dataProvider().dataSourceUri())
        tabela_entrada = uri_entrada.schema() + '.' + uri_entrada.table()
        tabela_filtro = uri_filtro.schema() + '.' + uri_filtro.table()
        
        if tabela_entrada[0] == '.':
            tabela_entrada = uri_entrada.table()
        
        feedback.pushInfo('tabela entrada =' + tabela_entrada)
        feedback.pushInfo('tabela filtro =' + tabela_filtro)
        
        
        
        
        # Set subset string in input layer
        filter_string = chave_primaria_entrada +" IN (SELECT A." + chave_primaria_entrada + " FROM " + tabela_entrada + " AS A JOIN " + tabela_filtro + " AS B ON ST_Intersects(A.geom, B.geom) WHERE B." + chave_primaria_filtro + " IN ("+ selecao_id + "))"
        feedback.pushInfo('filter_string = ' + filter_string)
        
        input_source.setSubsetString(filter_string)        
        
        return {'Resultado': 'feicoes filtradas'}
        
