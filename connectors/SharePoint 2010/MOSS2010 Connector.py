"""
Description:
	Provides the service to connect to SharePoint 2010

Author:
	A Mancevice

Parameters:
	
Object Metadata:
	
Pre-condition:
	
Post-condition:
	

Version Date		Author	  Change description
===========================================================================
1.0		5/27/2010	A mancevice	Initial Coding
"""

# The following global objects are available to the Enhance Rule environment:
# contentManagerService - com.vamosa.content.ContentManagerService
# projectManagerService - com.vamosa.projects.ProjectManagerService
# queryLibrarianService - com.vamosa.query.QueryLibrarianService
# taskLibrarianService  - com.vamosa.process.TaskLibrarianService
# pipelineRunner		- com.vamosa.process.PipelineRunner
# logger				- org.apache.commons.logging.Log
# pipelineName		  - java.lang.String containing the name of the pipeline

import sys, re

# add packages from Java into the python module library
sys.add_package("org.python.core")
sys.add_package("com.vamosa.tasks")
sys.add_package("com.vamosa.utils")
sys.add_package("com.vamosa.moss2010")

from com.vamosa.tasks import ParameterisedTask
from com.vamosa.utils import DOM4JUtils
from com.vamosa.utils import Base64
from com.vamosa.moss2010 import SharePointServiceLocator
from java.net import URL

class MyParameterisedClass(ParameterisedTask):
	def usage(self):
		self.requiresContentDescriptor("contentDescriptor", "the default content descriptor")
		self.requiresContent("content", "the default content")
		self.requiresString("local_service_url","URL of local service for SharePoint (eg. \"http://localhost/sharepoint.asmx?wsdl\")")
		self.requiresString("sharepoint_url","URL of SharePoint site (eg. \"http://moss2010/sites/nokia/\")")
		self.requiresString("user","Username for SharePoint")
		self.requiresString("password","Password for SharePoint")

	def enhance( self, contentDescriptor, content, local_service_url, sharepoint_url, user, password ):
		
		sharepoint = VamosaService(local_service_url,lists_url,sharepoint_url,user,password)
		
		
class VamosaService:
	def __init__( self, local_service_url, lists_url, sharepoint_url, user, password ):
		self.service = SharePointServiceLocator().getSharePointServiceSoap(URL(local_service_url))
		self.contextURL = sharepoint_url
		self.user = user
		self.password = password
		
	#---------------------------------------#
	############     SETs      ##############
	#---------------------------------------#
	
	# Creates Item in List
	# String listName - name of List
	# String[] fieldNames - list of fields for item
	# String[] fieldValues - list of values for fields (must be in corresponding order as fieldNames)
	# return created item's ID or error message
	def vCreateItem( self, listName, fieldNames, fieldValues ):
		return self.service.createItem(listName,fieldNames,fieldValues,self.contextURL,self.user,self.password)
		
	# Creates nested list of folders under list
	#       e.g. ['a','b','d','e'] --> a/b/c/d
	# String listName - name of List
	# String[] folders - names of nested folders
	# returns string response
	def vCreateFolders( self, listName, folders ):
		return self.service.createFolders(listName,folders,self.contextURL,self.user,self.password)
		
	# Creates discussion thread
	# String listName - name of List
	# String discussionTitle - title for discussion thread
	# String[] fieldNames - list of fields for item
	# String[] fieldValues - list of values for fields (must be in corresponding order as fieldNames)
	# returns discussion's ID or error message
	def vCreateDiscussion( self, listName, discussionTitle, fieldNames, fieldValues ):
		return self.service.createDiscussion(listName,discussionTitle,fieldNames,fieldValues,self.contextURL,self.user,self.password)
		
	# Creates reply to discussion thread
	# String listName - name of List
	# int parentID - ID of parent discussion thread
	# String[] fieldNames - list of fields for item
	# String[] fieldValues - list of values for fields (must be in corresponding order as fieldNames)
	# returns reply's ID or error message
	def vCreateReply( self, listName, parentID, fieldNames, fieldValues ):
		return self.service.createReply(listName,parentID,fieldNames,fieldValues,self.contextURL,self.user,self.password)
		
	# Adds attachment to item
	# byte[] bytes - byte array of attachment
	# String listName - name of List
	# int itemID - ID of item for attachment
	# String filename - filename of attachment
	# returns string that contains the URL for the attachment, which can subsequently be used to reference the attachment
	def vAddAttachment( self, bytes, listName, itemID, filename ):
		return self.service.addAttachment(bytes,listName,itemID,filename,self.contextURL,self.user,self.password)
		
	# Uploads asset to List
	# byte[] bytes - byte array of asset
	# String listName - name of List
	# String filename - filename of asset
	# returns success/error message
	def vUploadAsset( self, bytes, listName, filename ):
		return self.service.uploadAsset(bytes,listName,filename,self.contextURL,self.user,self.password)
		
	# Updates fields of previously created
	# String listName - name of List
	# String[] fieldNames - list of fields for item
	# String[] fieldValues - list of values for fields (must be in corresponding order as fieldNames)
	# returns success/error message
	def vUpdateItemFields( self, listName, itemID, fieldNames, fieldValues ):
		return self.service.updateItemFields(listName,itemID,fieldNames,fieldValues,self.contextURL,self.user,self.password)
		
	# Deletes item from MOSS
	# String listName - name of List
	# int itemID - ID of item to be deleted
	def vDeleteItem( self, listName, itemID ):
		return self.service.deleteItem(listName,itemID,self.contextURL,self.user,self.password)
		
	# GETs
	def vGetListsInfo( self ):
		listsString =  self.service.getListsInfo(self.contextURL,self.user,self.password)
		listsMap = {}
		for list in listsString.split('\n'):
			try:
				listName, listGUID = list.split(" : ")
				listsMap[listName] = listGUID
			except:
				continue
		return listsMap
		
	def vGetListItemsInfo( self, listName ):
		itemsString = self.service.getListItemsInfo(listName,self.contextURL,self.user,self.password)
		itemsMap = {}
		for item in itemsString.split('\n'):
			try:
				itemName, itemID = item.split(" : ")
				itemsMap[itemName] = int(itemID)
			except:
				continue
		return itemsMap
		
	def vGetListFoldersInfo( self, listName ):
		itemsString = self.service.getListFoldersInfo(listName,self.contextURL,self.user,self.password)
		itemsMap = {}
		for item in itemsString.split('\n'):
			try:
				itemName, itemID = item.split(" : ")
				itemsMap[itemName] = int(itemID)
			except:
				continue
		return itemsMap
		
	def vGetItemFields( self, listName, itemID ):
		itemFieldsString = self.service.getItemFields(listName,itemID,self.contextURL,self.user,self.password)
		itemFields = {}
		for itemField in itemFieldsString.split('\n'):
			matcher = re.match(r"\[(?P<name>[\w]+), (?P<value>.*?)\]",itemField)
			if matcher:
				name = matcher.group("name")
				value = matcher.group("value")
				itemFields[name] = value;
		return itemFields
