# -*- coding: utf-8 -*-

import requests
import psycopg2
from processing.tools import postgis
import xml.etree.ElementTree as ET



from qgis.core import (QgsProcessing,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterString,
                       QgsProcessingParameterVectorLayer,
                       QgsDataSourceUri)



class AdverteCamadasStore(QgsProcessingAlgorithm):
    URL = 'URL'
    USER = 'USER'
    PASSWORD = 'PASSWORD'


    def createInstance(self):
        return AdverteCamadasStore()

    def name(self):
        return 'adverte_camadas_store'

    def displayName(self):
        return 'Adverte camadas do Store'

    def group(self):
        return 'Geoserver'

    def groupId(self):
        return 'geoserver'

    def shortHelpString(self):
        return ("With a Geoserver URL of featuretypes of a PostGIS datastore, " 
                """plus the user and password of GeoServer, you can advert all layers in the Geoserver datastore. 
                Com uma URL featuretypes de um datastore do PostGIS, mais o usuário e senha do GeoServer, você pode advertir todas """
                "as camadas de um datastore do GeoServer")

    def initAlgorithm(self, config=None):
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
        url = parameters[self.URL]
        headers = {'Content-type': 'text/xml'}
        user = parameters[self.USER]
        password = parameters[self.PASSWORD]

        # Debugging info
        feedback.pushInfo('url = ' + url)
        feedback.pushInfo('user = ' + user)
        feedback.pushInfo('password = ' + password)
        feedback.pushInfo('')
        
        # Get layers in the datastore 
        headers = {'Accept': 'application/xml'}
        resp = requests.get(url,auth=(user,password), headers=headers)
        resp.raise_for_status() # raise error depending on the result
        feedback.pushInfo(resp.text)
        xml = resp.text
        feedback.pushInfo('')
        
        # Store featuretypes name parsing xml to Python
        featuretypes = []
        root = ET.fromstring(xml)
        for element in root:
            name_element = element.find('name')
            name = name_element.text
            featuretypes.append(name)
                
        feedback.pushInfo(str(featuretypes))
        feedback.pushInfo('')
        
        # Store payloads in list      
        payloads = []
        for name in featuretypes:
            a = ("""<featureType>
                    <name>""" + name + """</name>
                    <advertised>true</advertised>
                    </featureType>""")
            payloads.append(a)
            
        feedback.pushInfo(str(payloads))
        feedback.pushInfo('')
        
        # Advertising
        headers = {'Content-type': 'text/xml'}
        for i, payload in enumerate(payloads):
            resp = requests.put(url + '/' + featuretypes[i], auth=(user, password), data=payload, headers=headers)
            feedback.pushInfo("Camada advertida foi " + featuretypes[i])
            feedback.pushInfo('resp = ' + resp.text)
            
        return {'Resultado': 'Camadas advertidas'}
