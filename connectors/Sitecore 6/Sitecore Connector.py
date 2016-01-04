"""
Description:
    Creates content within a sitecore instance

Author:
    A Mancevice

Project Resources:
    "vamosa_webservice" - URL of the deployed Vamosa-Sitecore Web Service
	"db" - name of the content repository database ("master" is default)

Object Metadata:
    [Target.Path] - Path to parent Item in database (ie, does not include the item itself)
					ex.
						Content: "/sitecore/content/Home/News"
						Asset: "/Files/PDFs"
						Note that the path for assets should begin after the "/sitecore/media library" directory
						Directory structure must exist prior to load.
	
	[Target.Name] - Name of the Item (asset [Target.Name] values should include the file extension)
					ex.
						Content: "Because Content Matters"
						Asset: "Vamosa.pdf"
	
	[Target.Template Path] - Path to the item template used for creating content items
					ex. "/sitecore/templates/Starter Kit/Content Templates/News Article"

Pre-condition:
    Assets have above metadata.
	Content is transformed into XML such that each item field is a node and the 
	corresponding value is the value of said node.
	eg.
		<field name="Title">News Article</field>
		<field name="Text">&lt;b&gt;Hello World!&lt;/b&gt;</field>

Post-condition:
    Content exists within the Sitecore instance.


Version Date        Author      Change description
===========================================================================
1.0     11/24/09	A Mancevice	Initial Coding
"""

# The following global objects are available to the Enhance Rule environment:
# contentManagerService - com.vamosa.content.ContentManagerService
# projectManagerService - com.vamosa.projects.ProjectManagerService
# queryLibrarianService - com.vamosa.query.QueryLibrarianService
# taskLibrarianService  - com.vamosa.process.TaskLibrarianService
# pipelineRunner        - com.vamosa.process.PipelineRunner
# logger                - org.apache.commons.logging.Log
# pipelineName          - java.lang.String containing the name of the pipeline
import sys, os

# add packages from Java into the python module library
sys.add_package("org.python.core")
sys.add_package("com.vamosa.tasks")
sys.add_package("com.vamosa.utils")
sys.add_package("net.sitecore.vamosa")

from com.vamosa.projects import Project
from com.vamosa.tasks import ParameterisedTask
from com.vamosa.utils import DOM4JUtils
from com.vamosa.utils import Base64

from java.io import ByteArrayInputStream
from java.net import URL
from javax.xml.namespace import QName
from net.sitecore.vamosa import VamosaServiceLocator

class MyParameterisedClass(ParameterisedTask):
	def usage(self):
		self.requiresContentDescriptor("contentDescriptor", "the default content descriptor")
		self.requiresContent("content", "the default content")
		self.requiresString("vamosa_webservice","Address of the Vamosa Web Service")
		self.requiresString("db","name of database")
		self.requiresBoolean("verbose","Full output toggle (set to False to reduce sevice calls)")
		
	def enhance( self, contentDescriptor, content, vamosa_webservice, db, verbose ):
		
		sitecore = VamosaService()
		sitecore.init_service(vamosa_webservice)
		if db == None: db = "master"
		
		# LOAD ASSET
		if contentDescriptor.metadata["Identify Metadata.Content-Type"] != "application/xhtml+xml":
			
			# Use Web Service
			path = contentDescriptor.metadata["Target.Path"]
			filename = contentDescriptor.metadata["Target.Name"]
			name = filename.split('.')[0]
			extension = filename.split('.')[-1]
			dataString = content.contentData
			dataBytes = Base64.decode(dataString)
			id = sitecore.uploadAsset(path,name,extension,dataBytes,db)
			logger.info("Asset loaded with ID: %s" % (id))
			contentDescriptor.metadata["Load.ID"] = id
			
		# LOAD CONTENT
		else:
			if Project.getProjectAsSubProject(contentDescriptor.project).getSubprojectType() == "PLACEHOLDER":
				# Create Placeholder
				parent_path = contentDescriptor.metadata["Target.Path"]
				template_path = contentDescriptor.metadata["Target.Template Path"]
				name = contentDescriptor.metadata["Target.Name"]
				id = sitecore.createItem(parent_path,template_path,name,db,[],[])
				logger.info("Placeholder Loaded with ID: %s" % (id))
				contentDescriptor.metadata["Load.ID"] = id
				contentDescriptor.metadata["Load.Type"] = "PLACEHOLDER"
				if verbose: logger.info(sitecore.getItemFields("%s/%s" % (parent_path,name),db))
			else:
				# Prepare fields
				dom = content.contentDOM
				fields = map(lambda x: x.attributeValue("name"), dom.selectNodes("//item/*"))
				values = map(lambda x: x.getText(), dom.selectNodes("//item/*"))
				
				# Create Object
				parent_path = contentDescriptor.metadata["Target.Path"]
				name = contentDescriptor.metadata["Target.Name"]
				sitecore.updateFields(db,"%s/%s" % (parent_path,name),fields,values)
				logger.info("Content Updated with ID: %s" % (contentDescriptor.metadata["Load.ID"]))
				contentDescriptor.metadata["Load.Type"] = "CONTENT"
				if verbose: logger.info(sitecore.getItemFields("%s/%s" % (parent_path,name),db))
				
				
class VamosaService:
	def init_service( self, service_url ):		
		self.location = VamosaServiceLocator().getVamosaServiceSoap(URL(service_url+"?wsdl"))
		
	def uploadAsset( self, path, name, extension, data, dbName ):
		return self.location.uploadAsset(path,name,extension,data,dbName)
		
	def createItem( self, parent_path, template_path, name, dbName, fields, values ):
		return self.location.createItem(parent_path,template_path,name,dbName,fields,values)
		
	def updateFields( self, dbName, path, fields, values ):
		return self.location.updateFields(dbName,path,fields,values)
	
	def getItemFields( self, path, dbName ):
		return self.location.getItemFields(path,dbName)