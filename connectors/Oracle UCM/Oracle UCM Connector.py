"""
Description:
	Creates content within an Oracle UCM instance
	
Author:
	A Mancevice
	
Project Resources:
    "webservice"	- URL of the UCM Web Service
	"user"			- username for the UCM Instance
	"password"		- password for the UCM Instance
	"verbose"		- toggle logging. If set to True, service calls will
					  will be more frequent and objects will be checked
					  out after the CheckIn service completes.
	"metadata"		- list of custom UCM metadata names. The values for
					  this metadata will come from an objects [Target.*]
					  metadata, where * is a custom UCM metadata name
	
Object Metadata:
	The following metadata is required,
	[Target.dDocName]
	[Target.dDocTitle]
	[Target.dDocType]
	[Target.dDocAuthor]
	[Target.dSecurityGroup]
	[Target.dDocAccount]

Pre-condition:
	
	
Post-condition:
	Content exists within the UCM instance.
	
Version Date        Author      Change description
===========================================================================
1.0		4/29/10		A Mancevice Initial Coding
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
sys.add_package("com.stellent.www.CheckIn")
sys.add_package("com.stellent.www.Search")
sys.add_package("com.stellent.www.GetFile")
sys.add_package("com.stellent.www.DocInfo")

from com.vamosa.projects import Project
from com.vamosa.tasks import ParameterisedTask
from com.vamosa.utils import DOM4JUtils
from com.vamosa.utils import Base64

from java.io import ByteArrayInputStream
from java.net import URL
from javax.xml.namespace import QName
from java.util import HashMap

from com.stellent.www.CheckIn import CheckInLocator
from com.stellent.www.CheckIn import IdcProperty
from com.stellent.www.CheckIn import IdcFile
from com.stellent.www.Search import SearchLocator
from com.stellent.www.GetFile import GetFileLocator
from com.stellent.www.DocInfo import DocInfoLocator

class MyParameterisedClass(ParameterisedTask):
	def usage(self):
		self.requiresContentDescriptor("contentDescriptor", "the default content descriptor")
		self.requiresContent("content", "the default content")
		self.requiresString("webservice","Address of the UCM Web Service")
		self.requiresString("user","UCM Username")
		self.requiresString("password","UCM Password")	
		self.requiresBoolean("verbose","Full output toggle (set to False to reduce service calls)")
		self.requiresResource("metadata","List of UCM properties to seek in metadata")
		
	def enhance( self, contentDescriptor, content, webservice, user, password, verbose, metadata ):
		
		metadataList = metadata.compile().split('\n')
		
		# INIT SERVICE
		oracle = VamosaService()
		oracle.init_service(webservice,user,password,verbose)
		
		# GET VALUES
		checkInMap = self.getCheckInValues(contentDescriptor,content,oracle,metadataList)
		dDocName = checkInMap["dDocName"]
		dDocTitle = checkInMap["dDocTitle"]
		dDocType = checkInMap["dDocType"]
		dDocAuthor = checkInMap["dDocAuthor"]
		dSecurityGroup = checkInMap["dSecurityGroup"]
		dDocAccount = checkInMap["dDocAccount"]
		customDocMetadata = checkInMap["customDocMetadata"]
		primaryFile = checkInMap["primaryFile"]
		alternateFile = checkInMap["alternateFile"]
		extraProps = checkInMap["extraProps"]
		
		# LOAD
		result = oracle.vCheckIn(dDocName,dDocTitle,dDocType,dDocAuthor,dSecurityGroup,dDocAccount,customDocMetadata,primaryFile,alternateFile,extraProps)
		if result.getStatusInfo().getStatusCode() == 0:
			dID = result.getDID()
			contentDescriptor.metadata["Load.dID"] = str(dID)
			if verbose:
				logger.info(oracle.getGetFileString(oracle.vGetFileByID(dID)))
				oracle.vCheckOut(dID,[])
		else:
			logger.error("[!] Content not created: %s" % result.getStatusInfo().getStatusMessage())
			
			
	#********************************************************#
	# --- Get Values for Pages & Assets in prep for load --- #
	#********************************************************#
	def getCheckInValues( self, cd, content, oracle, metadataList ):
			
		checkInMap = {}
		# Manditory Metadata
		checkInMap["dDocName"]= cd.metadata["Target.dDocName"]
		checkInMap["dDocTitle"]= cd.metadata["Target.dDocTitle"]
		checkInMap["dDocType"]= cd.metadata["Target.dDocType"]
		checkInMap["dDocAuthor"]= cd.metadata["Target.dDocAuthor"]
		checkInMap["dSecurityGroup"]= cd.metadata["Target.dSecurityGroup"]
		checkInMap["dDocAccount"]= cd.metadata["Target.dDocAccount"]
	
		# Custom Metadata
		mdMap = HashMap()
		map(lambda x: mdMap.put(x,cd.metadata["Target.%s" % x]), metadataList)
		checkInMap["customDocMetadata"] = oracle.map2IdcPropList(mdMap)
	
		# File
		filename = cd.metadata["Target.Filename"]
		if cd.metadata["Identify Metadata.Content-Type"] == "application/xhtml+xml":
			fileContents = Base64.encodeString(content.contentData)
		else:
			fileContents = content.contentData
		checkInMap["primaryFile"] = oracle.content2IdcFile(filename,fileContents)
		checkInMap["alternateFile"] = None
		
		# Extras
		propMap = {}
		# ... add more?
		checkInMap["extraProps"] = oracle.map2IdcPropList(propMap)
		
		return checkInMap
	
	
############################################################################
##### ---------------          Service Class           --------------- #####
############################################################################	
class VamosaService:
	
	def init_service( self, service_url, user, password, doGetFile ):
		self.service = CheckInLocator().getCheckInSoap(URL(service_url))
		self.service.setUsername(user)
		self.service.setPassword(password)
		
		if doGetFile:
			self.file = GetFileLocator().getGetFileSoap(URL(service_url))
			self.file.setUsername(user)
			self.file.setPassword(password)
		
	def vCheckIn( self, dDocName, dDocTitle, dDocType, dDocAuthor, dSecurityGroup, dDocAccount, customDocMetadata, primaryFile, alternateFile, extraProps ):
		return self.service.checkInUniversal(dDocName,dDocTitle,dDocType,dDocAuthor,dSecurityGroup,dDocAccount,customDocMetadata,primaryFile,alternateFile,extraProps)
		
	def vCheckOut( self, dID, extraProps ):
		return self.service.checkOut(dID,extraProps)
		
	def vGetFileByID( self, dID, rendition="Primary", extraProps=[] ):
		return self.file.getFileByID(dID,rendition,extraProps)
		
	def vGetFileByName( self, dDocName, revisionSelectionMethod="Latest", rendition="Primary", extraProps=[] ):
		return self.file.getFileByName(dDocName,revisionSelectionMethod,rendition,extraProps)
		
	####################################################
	# ---------------  Helper Methods  --------------- #
	####################################################
	def map2IdcPropList( self, map ):
		idcProps = []
		for key in map:
			name = key
			value = map[key]
			idcProps.append(IdcProperty(name,value))
		return idcProps
			
	def content2IdcFile( self, name, content ):
		byteArray = Base64.decode(content)
		return IdcFile(name,byteArray)
		
	def getGetFile( self, result ):
		fileBytes = result.getDownloadFile()
		return Base64.encodeBytes(fileBytes)
		
	def getGetFileString( self, result ):		
		fileInfos = result.getFileInfo()
		fileString = '\n'
		for fileInfo in fileInfos:
			fileString += "-------------------------------\n"
			fileString +="dDocName:\t%s\n" % fileInfo.getDDocName()
			fileString +="dDocTitle:\t%s\n" % fileInfo.getDDocTitle()
			fileString +="dDocType:\t%s\n" % fileInfo.getDDocType()
			fileString +="dDocAuthor:\t%s\n" % fileInfo.getDDocAuthor()
			fileString +="dSecurityGroup:\t%s\n" % fileInfo.getDSecurityGroup()
			fileString +="dDocAccount:\t%s\n" % fileInfo.getDDocAccount()
			fileString +="dID:\t\t%s\n" % fileInfo.getDID()
			#fileString +="dRevClassID:\t%s\n" % fileInfo.getDRevClassID()
			#fileString +="dRevisionID:\t%s\n" % fileInfo.getDRevisionID()
			#fileString +="dRevLabel:\t%s\n" % fileInfo.getDRevLabel()
			#fileString +="dIsCheckedOut:\t%s\n" % fileInfo.getDIsCheckedOut()
			#fileString +="dCheckoutUser:\t%s\n" % fileInfo.getDCheckoutUser()
			#fileString +="dCreateDate:\t%s\n" % fileInfo.getDCreateDate()
			#fileString +="dInDate:\t\t%s\n" % fileInfo.getDInDate()
			#fileString +="dOutDate:\t\t%s\n" % fileInfo.getDOutDate()
			#fileString +="dStatus:\t\t%s\n" % fileInfo.getDStatus()
			#fileString +="dReleaseState:\t%s\n" % fileInfo.getDReleaseState()
			#fileString +="dFlag1:\t\t%s\n" % fileInfo.getDFlag1()
			#fileString +="dWebExtension:\t%s\n" % fileInfo.getDWebExtension()
			#fileString +="dProcessingState:\t%s\n" % fileInfo.getDProcessingState()
			#fileString +="dMessage:\t\t%s\n" % fileInfo.getDMessage()
			#fileString +="dReleaseDate:\t%s\n" % fileInfo.getDReleaseDate()
			#fileString +="dRendition1:\t%s\n" % fileInfo.getDRendition1()
			#fileString +="dRendition2:\t%s\n" % fileInfo.getDRendition2()
			#fileString +="dIndexerState:\t%s\n" % fileInfo.getDIndexerState()
			#fileString +="dPublishType:\t%s\n" % fileInfo.getDPublishType()
			#fileString +="dPublishState:\t%s\n" % fileInfo.getDPublishState()
			#fileString +="dDocID:\t\t%s\n" % fileInfo.getDDocID()
			#fileString +="dIsPrimary:\t%s\n" % fileInfo.getDIsPrimary()
			#fileString +="dIsWebFormat:\t%s\n" % fileInfo.getDIsWebFormat()
			#fileString +="dLocation:\t%s\n" % fileInfo.getDLocation()
			#fileString +="dOriginalName:\t%s\n" % fileInfo.getDOriginalName()
			fileString +="dFormat:\t%s\n" % fileInfo.getDFormat()
			fileString +="dExtension:\t%s\n" % fileInfo.getDExtension()
			#fileString +="dFileSize:\t%s\n" % fileInfo.getDFileSize()
			mds = fileInfo.getCustomDocMetaData()
			for md in mds:
				fileString += "  customDocMetaData:\t%s, %s\n" % (md.getName(),md.getValue())
		return fileString