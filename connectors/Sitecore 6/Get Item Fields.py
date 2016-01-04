import sys

# add packages from Java into the python module library
sys.add_package("org.python.core")
sys.add_package("com.vamosa.tasks")
sys.add_package("com.vamosa.utils")
sys.add_package("net.sitecore.vamosa")

from com.vamosa.tasks import ParameterisedTask
from com.vamosa.utils import DOM4JUtils
from com.vamosa.utils import Base64

from java.io import ByteArrayInputStream
from java.net import URL
from javax.xml.namespace import QName
from net.sitecore.vamosa import VamosaServiceLocator

class MyParameterisedClass(ParameterisedTask):
	def usage(self):
		self.requiresProject("project", "the default project")
		self.requiresString("itemPath","Path to item")
		self.requiresString("service","URL of Vamosa Web Service")
		self.requiresString("db","database name")

	def enhanceProject( self, project, itemPath, service, db ):
		sitecore = VamosaService()
		sitecore.init_service(service)
		if db == None: db = "master"
		
		logger.info(sitecore.getItemFields(itemPath,db))
		
class VamosaService:
	def init_service( self, service_url ):		
		self.location = VamosaServiceLocator().getVamosaServiceSoap(URL(service_url+"?wsdl"))
		
	def uploadAsset( self, path, name, extension, data, dbName ):
		return self.location.uploadAsset(path,name,extension,data,dbName)
		
	def createItem( self, parent_path, template_path, name, dbName, fields, values ):
		return self.location.createItem(parent_path,template_path,name,dbName,fields,values)
		
	def updateFields( self, path, fields, values ):
		return self.location.updateFields(path,fields,values)
	
	def getItemFields( self, path, dbName ):
		return self.location.getItemFields(path,dbName)]]