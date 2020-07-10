# -*- coding: utf-8 -*-
"""
Created on Fri Mar 27 17:24:09 2020

@author: Marcel
"""

# -*- coding: utf-8 -*-

import requests
import xml.etree.ElementTree as ET



from qgis.core import (QgsProcessingAlgorithm,
                       QgsProcessingParameterString)



class SubstituiNomesStore(QgsProcessingAlgorithm):
    URL = 'URL'
    USER = 'USER'
    PASSWORD = 'PASSWORD'
    FIND = 'FIND'
    REPLACE = 'REPLACE'


    def createInstance(self):
        return SubstituiNomesStore()

    def name(self):
        return 'substitui_nomes_store'

    def displayName(self):
        return 'Substitui Nomes Store'

    def group(self):
        return 'Geoserver'

    def groupId(self):
        return 'geoserver'

    def shortHelpString(self):
        return ("With a Geoserver URL of featuretypes of a PostGIS datastore, " 
                "plus the user and password of GeoServer, plus a string to find and another to replace, "  
                """you can replace all the occurencies of a string in the name and title of the layers in the datastore by another string of replacement. 
                Com uma URL featuretypes de um datastore do PostGIS, mais o usuário e senha do GeoServer, mais uma string """
                "de busca ou outra de substituição, você pode substituir todas as ocorrências de uma string no nome e título das camadas em um datastore por outra string.""")

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
        
        # Find string
        self.addParameter(QgsProcessingParameterString(
            self.FIND,
            "Find"))
        
        # Replace string
        self.addParameter(QgsProcessingParameterString(
            self.REPLACE,
            "Replace"))


    def processAlgorithm(self, parameters, context, feedback):
        """
        Retrieving parameters
        an URL example is 'http://localhost:8080/geoserver/rest/workspaces/cite/datastores/Publicacao/featuretypes'
        """
        url = parameters[self.URL]
        headers = {'Content-type': 'text/xml'}
        user = parameters[self.USER]
        password = parameters[self.PASSWORD]
        find = parameters[self.FIND]
        replace = parameters[self.REPLACE]

        # Debugging info
        feedback.pushInfo('Parâmetros de entrada')
        feedback.pushInfo('url = ' + url)
        feedback.pushInfo('headers = ' + str(headers))
        feedback.pushInfo('user = ' + user)
        feedback.pushInfo('password = ' + password)
        feedback.pushInfo('')
        
        # Get layers in the datastore 
        headers = {'Accept': 'application/xml'}
        resp = requests.get(url,auth=(user,password), headers=headers)
        resp.raise_for_status() # raise error depending on the result
        xml = resp.text
        feedback.pushInfo('xml featuretypes')
        feedback.pushInfo(xml)
        feedback.pushInfo('')
        
        
        # Store featuretypes name parsing xml to Python
        featuretypes_name = []
        root = ET.fromstring(xml)
        feedback.pushInfo(str(root))
        for element in root:
            name_element = element.find('name')
            name = name_element.text
            featuretypes_name.append(name)
        
        feedback.pushInfo('FeatureTypes Name')                
        feedback.pushInfo(str(featuretypes_name))
        feedback.pushInfo('')
        
        
        # Loop over FeatureTypes Name to get titles
        featuretypes_title = []
        for name in featuretypes_name:
            resp = requests.get(url + '/' + name,auth=(user,password), headers=headers)
            resp.raise_for_status() # raise error depending on the result
            xml = resp.text
            feedback.pushInfo(xml)
            root = ET.fromstring(xml)
            feedback.pushInfo(str(root))
            title_element = root.find('title')
            title = title_element.text
            featuretypes_title.append(title)
                
        feedback.pushInfo('FeatureTypes Title')   
        feedback.pushInfo(str(featuretypes_title))
        feedback.pushInfo('')
                
        # Create list that stores renamed featuretypes and renamed titles of featuretypes
        featuretypes_name_r = [s.replace(find, replace) for s in featuretypes_name]
        featuretypes_title_r = [s.replace(find, replace) for s in featuretypes_title]
        
        feedback.pushInfo('FeatureTypes Name Renamed')
        feedback.pushInfo(str(featuretypes_name_r))
        feedback.pushInfo('FeatureTypes Title Renamed')
        feedback.pushInfo(str(featuretypes_title_r))
        feedback.pushInfo('')
        
        # Store payloads in list      
        payloads = []
        for i in range(len(featuretypes_name_r)):
            a = ("""<featureType>
                    <name>""" + featuretypes_name_r[i] + """</name>
                    <title>""" + featuretypes_title_r[i] + """</title>
                    </featureType>""")
            payloads.append(a)
            
        feedback.pushInfo("Payloads")
        feedback.pushInfo(str(payloads))
        feedback.pushInfo('')
        
        
        # Replacing names
        headers = {'Content-type': 'text/xml'}
        for i, payload in enumerate(payloads):
            resp = requests.put(url + '/' + featuretypes_name[i], auth=(user, password), data=payload.encode('utf-8'), headers=headers)
            feedback.pushInfo('resp = ' + resp.text)
            feedback.pushInfo("Camada renomeada foi " + featuretypes_name[i])
            feedback.pushInfo("Foi renomeada para " + featuretypes_name_r[i])
            feedback.pushInfo("Título foi " + featuretypes_title[i])
            feedback.pushInfo("Título foi renomeado para " + featuretypes_title_r[i])
            feedback.pushInfo('')
            
        
        return {'Resultado': 'Strings substituídas nas camadas do Store'}
