"""
Description:
	The CQ5 Loader can operate in three different ways using per-object and
	per-project methods. These three methods can be used to load assets, pages
	or build an IA based on an Excel resource.
	
	ASSETS are to be loaded using the per-object 'enhance' method. Assets are loaded
	to the /var/dam/ directory by first establishing a connection to the CRX repository
	via a virtual drive (using NetDrive is one method) and saving files directly to this
	drive. Any additional metadata can be applied by creating an asset skeleton and 
	establishing a rules.xml resource to populate it. Additional metadata is populated
	through the CQ connector, just as pages are. If loading via WebDAV is not feasible,
	assets may be loaded through the connector JSP.
	
	PAGES are to be loaded using the per-project 'enhanceProject' method. Page
	loads require a query-parameter that returns an ORDERED set of pages to load.
	The query must return pages ordered by IA level because a page cannot be
	instantiated below a page that has not been previously created. Note that the 
	query needs at least one metadata attribute so that the result is a list 
	(ie. calling the 0th element--the content descriptor--is legal). This script
	assumes that pages have already been cut up into the propper XML format.
	
	IA can be loaded prior to loading pages (for instance, if the client wishes
	to restructure the IA with pages not currently existing in the new site).
	The IA option requires the boolean parameter 'ia_isIA' to be set to 'True'
	to execute.
	
Author:
	A Mancevice

Project Resources:
	
	@connector_url ------------- url to CQ connector page
	@cq_user ------------------- username for CQ login
	@cq_password --------------- password for CQ login
	
	@asset_skeleton ------------ xml template for asset payloads (OPTIONAL)
	@asset_transformationRules - transformation rules XML for applying metadata (OPTIONAL)
	@asset_drive --------------- drive letter for WebDAV directory
	@asset_filenameAttr -------- metadata attribute name for asset filenames
	@asset_pathAttr ------------ metadata attribute name for asset paths
	@asset_doWebDAV ------------ switch to load assets over WebDAV
	
	@page_query ---------------- Query to return pages to load IN ORDER
	@page_queryLib ------------- Query Library where 'page_query' resides
	
	@ia_path ------------------- path to IA Excel file
	@ia_cacheCols -------------- no. of columns in Excel file to cache
	@ia_isIA ------------------- a boolean flag to escape regular page loading

Pre-condition:

	"convenience.py", "rules.py" must exist in the vamosa\jboss\3rdparty\jythonlib\services\vamosa
	
	Assets: Must have data. Note that the target URI for assets in metadata should
		begin with /content/dam/... but the assets are loaded to the directory
		/var/dam/... Assets loaded to this directory will be imported to the 
		/content/dam/ directory by CQ, creating thumbnails and populating any
		metadata it finds automatically. Additional metadata for assets (cut
		into the provided XML asset skeleton) should be sent to /content/dam/...
		
	Pages: Pages are cut up into XML payloads
	
	IA: The Excel sheet contains at least four (4) columns containing
		"Path" ---------- Path to the page
		"Filename" ------ Filename of the page
		"Label" --------- Label of the page (ie, page title)
		"Template Path" - Template path (the path to the CQ template for the page)
	Note that the columns MUST be named as they appear above. Additionally none of the above 
	values may contain any characters outside the scope of standard filename characters, save
	values in the "Label" column. However, any extended characters in said column should be 
	replaced with XHTML entities (the ampersand (&) character, for instance must be replaced 
	with "&amp;")

Post-condition:
	Pages, placeholders and/or assets are loaded into CQ instance!


Version Date		Author	  Change description
===========================================================================
1.0	 6/3/2009	A Mancevice		Initial Coding
2.0	 2/4/2010	A Mancevice		Rewrote Asset loading method, tidied code
"""

# The following global objects are available to the Enhance Rule environment:
# contentManagerService - com.vamosa.content.ContentManagerService
# projectManagerService - com.vamosa.projects.ProjectManagerService
# queryLibrarianService - com.vamosa.query.QueryLibrarianService
# taskLibrarianService -- com.vamosa.process.TaskLibrarianService
# pipelineRunner -------- com.vamosa.process.PipelineRunner
# logger ---------------- org.apache.commons.logging.Log
# pipelineName ---------- java.lang.String containing the name of the pipeline

import sys, re, services, os, codecs

# add packages from Java into the python module library
sys.add_package("org.python.core")
sys.add_package("com.vamosa.tasks")
sys.add_package("com.vamosa.utils")

from com.vamosa.tasks import ParameterisedTask
from com.vamosa.utils import DOM4JUtils
from com.vamosa.utils import Base64

from services.vamosa import convenience
from services.vamosa import rules

from java.util import HashMap
from java.io import BufferedOutputStream
from java.io import FileOutputStream

from org.apache.commons.httpclient import HttpClient
from org.apache.commons.httpclient import Header
from org.apache.commons.httpclient.methods import PostMethod
from org.apache.commons.httpclient.methods import GetMethod

from os.path import exists
from os import makedirs

class MyParameterisedClass(ParameterisedTask):
	def usage(self):
		self.requiresProject("project","the default project")
		self.requiresContentDescriptor("contentDescriptor","the default content descriptor")
		self.requiresContent("content","the default content")
		
		self.requiresString("connector_url","URL to the Vamosa Connector in CQ")
		
		self.requiresString("cq_user","CQ Username")
		self.requiresString("cq_password","CQ Password")
		
		self.requiresResource("asset_skeleton","XML skeleton for asset metadata payloads")
		self.requiresResource("asset_transformationRules","Rules XML for pupulating XML Skeleton")
		self.requiresString("asset_drive","Drive letter for WebDAV directory")
		self.requiresString("asset_filenameAttr","Metadata name for asset filename in target CMS")
		self.requiresString("asset_pathAttr","Metadata name for asset path in target CMS")
		self.requiresBoolean("asset_doWebDAV","Load Assets to WebDAV (T/F)")
		
		self.requiresString("page_query","Query to find pages to migrate")
		self.requiresQueryLibrary("page_queryLib","Query Library in VCM")
		
		self.requiresContent("ia_path","Path to IA Mapping Excel file")
		self.requiresInteger("ia_cacheCols","number of columns to cache from XLS/resource")
		self.requiresBoolean("ia_isIA","Flag to load IA vs. content")
		
		
	########################################################
	#### ------------  ENHANCE PROJECT  --------------- ####
	#### --- Build IA Structure based on Excel File --- ####
	def enhanceProject( self, project, connector_url, cq_user, cq_password, page_query, page_queryLib, ia_path, ia_cacheCols, ia_isIA ):
		
		# IA vs. Page switch
		if ia_isIA: self.enhanceIA(connector_url,cq_user,cq_password,ia_path,ia_cacheCols)
		else: self.enhancePages(project,connector_url,cq_user,cq_password,page_query,page_queryLib)
		
		
	###################################################
	#### ------------  ENHANCE IA  --------------- ####
	def enhanceIA( self, connector_url, cq_user, cq_password, ia_path, ia_cacheCols ):
		
		# Validate Parameters
		if not self.validInputs(connector_url,cq_user,cq_password,"asset_drive","asset_filenameAttr","asset_pathAttr","page_query","page_queryLib",ia_path,ia_cacheCols): return
		
		# HTTP Connection Details
		client = HttpClient()
		base64EncodedCredentials = Base64.encodeString("%s:%s" % (cq_user,cq_password))
		header = Header("Authorization", "Basic %s" % (base64EncodedCredentials))
		
		# IA Build
		cached_IA = self.cacheIA(ia_path,ia_cacheCols)
		for placeholder in cached_IA:
			
			post = PostMethod(connector_url)
			post.addRequestHeader(header)
			get = GetMethod(connector_url)
			get.addRequestHeader(header)
			
			# Prep Payload
			path = placeholder["Path"]
			filename = placeholder["Filename"]
			template_path = placeholder["Template Path"]
			label = placeholder["Label"]
			
			# Send Payload
			payload = '<page path="%s" filename="%s" template_path="%s" label="%s"><node path="jcr:content" type="nt:unstructured"><prop name="jcr:title" type="String">%s</prop></node></page>' % (path,filename,template_path,label,label)
			[loadStatus, failureReason] = self.sendPayload(client,get,post,payload,path+filename)
			if loadStatus != "SUCCESS":
				logger.error("url: %s, reason: %s" % (placeholder["URL"], failureReason))
				
				
	######################################################
	#### ------------  ENHANCE PAGES  --------------- ####
	def enhancePages( self, project, connector_url, cq_user, cq_password, page_query, page_queryLib ):	
				
		# Validate Parameters
		if not self.validInputs(connector_url,cq_user,cq_password,"asset_drive","asset_filenameAttr","asset_pathAttr",page_query,page_queryLib,"ia_path","ia_cacheCols"): return
		
		# HTTP Connection Details
		client = HttpClient()
		base64EncodedCredentials = Base64.encodeString("%s:%s" % (cq_user,cq_password))
		header = Header("Authorization", "Basic %s" % (base64EncodedCredentials))
		
		# Cycle through contentdescriptors specified by scope query
		query = queryLibrarianService.findQueryByName(page_queryLib, page_query)
		params = HashMap()
		params.put('projectId',project.id)
		res = queryLibrarianService.executeQuery(query, params)
		
		# Get cd
		for r in res:
			cd = r[0]
			post = PostMethod(connector_url)
			post.addRequestHeader(header)
			get = GetMethod(connector_url)
			get.addRequestHeader(header)
			try:
				payload = cd.getContent()[0].getContentData().encode("utf-8")
				[loadStatus, failureReason] = self.sendPayload(client,get,post,payload,cd.url)
				cd.metadata["Load.Status"] = loadStatus
				cd.metadata["Load.Failure Reason"] = failureReason
				if loadStatus != "SUCCESS":
					logger.error("url: %s, reason: %s" % (cd.url, failureReason))
			except:
				cd.metadata["Load.Status"] = "FAILURE"
				cd.metadata["Load.Failure Reason"] = "Null content"
				logger.error("url: %s, reason: %s" % (cd.url, failureReason))
				
				
	###################################################################
	#### -------------------  ENHANCE ASSET  --------------------- ####
	#### ----- Send Asset Payload to CQ5; build and populate ----- ####
	def enhance( self, contentDescriptor, content, connector_url, cq_user, cq_password, asset_doWebDAV, asset_skeleton, asset_transformationRules, asset_drive, asset_filenameAttr, asset_pathAttr ):
		
		# Validate Parameters
		if not self.validInputs(connector_url,cq_user,cq_password,asset_drive,asset_filenameAttr,asset_pathAttr,"page_query","page_querylib","ia_path","ia_cacheCols"): return
		
		if asset_doWebDAV:
			# Save Asset to WebDAV Drive
			drive = asset_drive[0]
			path = re.sub("/content/dam/","/var/dam/",contentDescriptor.metadata[asset_pathAttr])
			filename = contentDescriptor.metadata[asset_filenameAttr]
			filepath = "%s:%s/%s" % (drive,path,filename)
			
			if not exists("%s:%s" % (drive,path)): makedirs("%s:%s" % (drive,path))
			file = BufferedOutputStream(FileOutputStream(filepath))
			data = Base64.decode(content.contentData)
			try: 
				file.write(data, 0, len(data))
				file.close()
				contentDescriptor.metadata["Load.Status"] = "SUCCESS"
			except:
				logger.error("! [WebDAV] Could not write %s to file system" % (contentDescriptor.url))
				file.close()
				contentDescriptor.metadata["Load.Status"] = "FAILURE"
				contentDescriptor.metadata["Load.Failure Reason"] = "! [WebDAV] Could not deposit file on file system"
				return
			
		# Build & Send Asset Metadata Payload if required
		if asset_skeleton and asset_transformationRules:
			
			# Build Payload
			payload = self.buildAssetPayload(asset_skeleton,asset_transformationRules,content,contentDescriptor)
			
			# HTTP Connection Details
			client = HttpClient()
			base64EncodedCredentials = Base64.encodeString("%s:%s" % (cq_user,cq_password))
			header = Header("Authorization", "Basic %s" % (base64EncodedCredentials))
			
			# Send Metadata Payload
			post = PostMethod(connector_url)
			post.addRequestHeader(header)
			get = GetMethod(connector_url)
			get.addRequestHeader(header)
			[loadStatus, failureReason] = self.sendPayload(client,get,post,payload,contentDescriptor.url)
			contentDescriptor.metadata["Load.Status"] = loadStatus
			if loadStatus == "SUCCESS":
				contentDescriptor.metadata["Load.Failure Reason"] = ''
			else:
				contentDescriptor.metadata["Load.Failure Reason"] = "Metadata: "+failureReason
				logger.error("! [METADATA] %s" % (failureReason))		
				
				
	###################################################
	#### ---------  Send Payload to CQ  ---------- ####
	def sendPayload( self, client, get, post, payload, identifier ):
		
		post.setParameter("jcr:content/payload",payload)
		postCode = client.executeMethod(post)
		if postCode != 200:
			loadStatus = "FAILURE"
			failureReason = "[POST] %d-code jcr:content/payload property not set for %s" % (postCode,identifier)
			self.setLoadStatus(cd,loadStatus,failureReason)
			return [loadStatus, failureReason]
		getCode = client.executeMethod(get)
		if getCode != 200:
			loadStatus = "FAILURE"
			failureReason = "[GET] %d-code returned pinging %s" % (getCode,identifier)
			self.setLoadStatus(cd,loadStatus,failureReason)
			return [loadStatus, failureReason]
		else:
			getResponse = get.getResponseBodyAsString()
			logger.debug(getResponse)
			if getResponse.find("[ERROR!]") >= 0:
				errorMessage = getResponse[(getResponse.find("[ERROR!]")+56):].strip()
				errorMessage = errorMessage[:errorMessage.find("[ERROR!]")]
				loadStatus = "FAILURE"
				failureReason = errorMessage
				return [loadStatus, failureReason]
			else:
				loadStatus = "SUCCESS"
				return [loadStatus, '']
		
		
	####################################################
	#### ---------  Build Asset Payload  ---------- ####
	def buildAssetPayload( self, asset_skeleton, asset_transformationRules, content, contentDescriptor ):
	
		targetTemplate = asset_skeleton.compile()
		transformationRules = asset_transformationRules.compile()
		
		vcmGlobals = {'logger':logger, 'targetXML':targetTemplate}
		contentTypeRulesNodes = transformationRules.selectNodes("//contenttype")
		for contentTypeRulesNode in contentTypeRulesNodes:
			rules.execute(vcmGlobals, contentDescriptor, content, contentTypeRulesNode)
			return vcmGlobals["targetXML"].asXML()
		
		
	#####################################################
	#### ---------  Cache IA Excel Sheet  ---------- ####
	def cacheIA( self, ia_path, ia_cacheCols ):
	
		logger.info('...Caching Excel file %s...' % ia_path)
		cached_IA = convenience.cacheExcelFile(ia_path, ia_cacheCols)
		logger.info('...Done caching Excel file...')
		
		col_names = cached_IA.pop(0)
		logger.info('Found columns: %s' % (', '.join(col_names)))
		
		return [dict(zip(col_names, x)) for x in cached_IA]
		
		
	################################################
	#### ---------  Validate Inputs  ---------- ####
	def validInputs( self, connector_url, cq_user, cq_password, asset_drive, asset_filenameAttr, asset_pathAttr, page_query, page_queryLib, ia_path, ia_cacheCols ):
		
		ok = True
		if connector_url == None:
			logger.error("! [Connector] Please supply valid connector URL inputs")
			ok = False
		if cq_user == None or cq_password == None:
			logger.error("! [CQ] Please supply valid CQ credentials")
			ok = False
		if asset_drive == None or asset_filenameAttr == None or asset_pathAttr == None:
			logger.error("! [Asset] Please supply all asset parameters")
			ok = False
		if page_query == None or page_queryLib == None:
			logger.error("! [Page] Please supply query to return pages IN ORDER")
			ok = False
		if ia_path == None or ia_cacheCols == None:
			logger.error("! [IA] Please supply valid IA parameters")
			ok = False
		return ok