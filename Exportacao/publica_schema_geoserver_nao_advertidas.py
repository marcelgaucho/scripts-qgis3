# -*- coding: utf-8 -*-

import requests
import psycopg2
from processing.tools import postgis


from qgis.core import (QgsProcessing,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterString,
                       QgsProcessingParameterVectorLayer,
                       QgsDataSourceUri)
from sys import prefix



class PublicaSchemaGeoserver(QgsProcessingAlgorithm):
    DATABASE = 'DATABASE'
    SCHEMA = 'SCHEMA'
    URL = 'URL'
    CAMADA = 'CAMADA'
    USER = 'USER'
    PASSWORD = 'PASSWORD'
    PREFIX = 'PREFIX'

    def createInstance(self):
        return PublicaSchemaGeoserver()

    def name(self):
        return 'publica_schema_geoserver_nao_advertidas'

    def displayName(self):
        return 'Publica Schema no Geoserver Nao Advertidas'

    def group(self):
        return 'Geoserver'

    def groupId(self):
        return 'geoserver'

    def shortHelpString(self):
        return ("With a Geoserver URL of featuretypes of a PostGIS datastore, a layer of connection with the PostGIS schema relative to the datastore " 
                """plus the user and password of GeoServer, you can publish all layers of PostGIS schema in batch. 
                Com uma URL featuretypes de um datastore do PostGIS, você pode publicar todos as camadas de um esquema PostGIS em batch. """
                "An URL example is http://localhost:8080/geoserver/rest/workspaces/cite/datastores/Publicacao/featuretypes")

    def initAlgorithm(self, config=None):
        # Database
        db_param = QgsProcessingParameterString(
            self.DATABASE,
            'Database (connection name)')
        db_param.setMetadata({
            'widget_wrapper': {
                'class': 'processing.gui.wrappers_postgis.ConnectionWidgetWrapper'}})
        self.addParameter(db_param)


        # Schema
        schema_param = QgsProcessingParameterString(
            self.SCHEMA,
            'Schema da Base', 'public', False, True)
        schema_param.setMetadata({
            'widget_wrapper': {
                'class': 'processing.gui.wrappers_postgis.SchemaWidgetWrapper',
                'connection_param': self.DATABASE}})
        self.addParameter(schema_param)
        
        # Prefixo (nome do projeto)
        prefix_param = QgsProcessingParameterString(
            self.PREFIX,
            'Prefixo (nome do projeto)', '', False, True)
        self.addParameter(prefix_param)

        # featuretypes URL
        self.addParameter(QgsProcessingParameterString(
            self.URL,
            "URL"))


        # Geoserver user            
        self.addParameter(QgsProcessingParameterString(
            self.USER,
            "User",
            "admin"))    

        # Geoserver password
        self.addParameter(QgsProcessingParameterString(
            self.PASSWORD,
            "Password",
            "geoserver"))


    def processAlgorithm(self, parameters, context, feedback):
        """
        Retrieving parameters
        an URL example is 'http://localhost:8080/geoserver/rest/workspaces/cite/datastores/Publicacao/featuretypes'
        """
        connection = self.parameterAsString(parameters, self.DATABASE, context)
        db = postgis.GeoDB.from_name(connection)
        
        schema = self.parameterAsString(parameters, self.SCHEMA, context)
        
        url = parameters[self.URL]
        headers = {'Content-type': 'text/xml'}
        user = parameters[self.USER]
        password = parameters[self.PASSWORD]
        prefix = parameters[self.PREFIX]
        

        # Debugging info
        feedback.pushInfo('Dados de conexão')
        feedback.pushInfo('url = ' + url)
        feedback.pushInfo('user = ' + user)
        feedback.pushInfo('password = ' + password)
        feedback.pushInfo('prefix = ' + prefix)
        feedback.pushInfo('')
        
        
        # URI and connection
        uri = db.uri
        
        con = psycopg2.connect(user = uri.username(), password = uri.password(), 
                                      host = uri.host(), port = uri.port(), database = uri.database())
        
        feedback.pushInfo('')
        feedback.pushInfo('Connection = ' + str(con) +'\n')
        

        with con:
            select_schema_tables = "SELECT table_name FROM information_schema.tables " \
                                   "WHERE table_schema = '{}'".format(schema)
                                   
            cur = con.cursor()
            
            cur.execute(select_schema_tables)
            
            rows = cur.fetchall()

            schema_tables = [table[0] for table in rows]
            
        
        feedback.pushInfo('Schema Tables = ' + str(schema_tables) + '\n')


        
        # Nomenclatura Geoserver
        dicio = {'P':'(Ponto)', 'L':'(Linha)', 'A':'(Área)'}
        
        # Names are with underline and with first letter in uppercase. The name of the project goes first.
        names1 = [item[item.find('_')+1:].replace('_', ' ').title().replace(' ', '_') for item in schema_tables]  
        names2 = [prefix + '_' + item for item in names1]    
        
        titles = [prefix + ' ' + item.replace('_', ' ')[:-1] + dicio[item[-1]] if item[-1] in 'PLA' else prefix + ' ' + item.replace('_', ' ') for item in names1]

        # Dicionário de categorias EDGV 3
        dicio_cat = {'ENC': 'Energia e Comunicações', 'ECO': 'Estrutura Econômica', 'HID': 'Hidrografia', 
                     'LML': 'Limites e Localidades', 'PTO':'Pontos de Referência', 'REL':'Relevo', 
                     'SAB':'Saneamento Básico', 'TRA':'Sistema de Transporte', 'AER':'Subsistema Aeroportuário',
                     'DUT':'Subsistema Dutos', 'FER':'Subsistema Ferroviário', 'HDV':'Subsistema Rodoviário',
                     'ROD':'Subsistema Rodoviário', 'VEG':'Vegetação', 'VER':'Área Verde', 'CBGE':'Classes Base do Mapeamento Topográfico em Grandes Escalas',
                     'LAZ':'Cultura e Lazer', 'EDF':'Edificações', 'EMU':'Estrutura de Mobilidade Urbana'}
        
        feedback.pushInfo('Payloads dará informação sobre a nomenclatura exibida pelo Geoserver')
        payloads = []    
        for i in range(len(names1)):
            a = ("""<featureType>
                        <name>""" + names2[i] + """</name> 
                        <nativeName>""" + schema_tables[i] + """</nativeName>
                        <abstract>""" + "Camada representando a classe [" + names1[i][:names1[i].rfind('_')]  + "] de primitiva geométrica ["
                        + names1[i][-1] + ':' + dicio[names1[i][-1]][1:-1] + "] da categoria [" + schema_tables[i][:schema_tables[i].find('_')].upper() + ':' + dicio_cat[schema_tables[i][:schema_tables[i].find('_')].upper()] + "] da EDGV versão [3.0] "
                        "para o projeto [" + prefix + "] da instituição/provedor [IBGE/Cartografia]." + """</abstract> 
                        <title>""" + titles[i] + """</title>
                        <enabled>true</enabled>
                        <advertised>false</advertised>
                        </featureType>""")
            payloads.append(a)
            feedback.pushInfo('payload = ' + a)
            
        feedback.pushInfo('')
        
        
        # Teste de publicação
        '''
        feedback.pushInfo('Teste de Publicação')
        feedback.pushInfo('payloadTeste = ' + payloads[21])
        
        
        try:
            resp = requests.post(url, auth=(user, password), data=payloads[21].encode('utf-8'),headers=headers)
            feedback.pushInfo('resp = ' + resp.text)
        except:
            pass
        '''
        
        # Publicação
        feedback.pushInfo('')
        
        for i, payload in enumerate(payloads):
            try:
                resp = requests.post(url, auth=(user, password), data=payload.encode('utf-8'),headers=headers)
                if resp.text == '':
                    feedback.pushInfo("Camada publicada foi " + names2[i])
                else:
                    feedback.pushInfo("Erro na publicação: " + resp.text)
            except:
                pass
            
        
        '''
        resp = requests.post(url, auth=(user, password), data=payloads[21],headers=headers) # está funcionando
        feedback.pushInfo('resp = ' + resp.text)
        '''
        
        
        
        return {'Resultado': 'Camadas publicadas'}
