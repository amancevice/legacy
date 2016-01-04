<%@include file="/libs/wcm/global.jsp"%>
<%@page import="com.day.cq.commons.jcr.JcrUtil,
                javax.xml.parsers.DocumentBuilder,
                javax.xml.parsers.DocumentBuilderFactory,
                org.w3c.dom.Document,
                org.w3c.dom.Element,
                org.w3c.dom.NodeList,
                java.io.InputStream,
                java.io.ByteArrayInputStream,
                org.apache.commons.lang.StringEscapeUtils,
                org.apache.commons.codec.binary.Base64"%>

<!-- 

CQ5 Connector, use XML payload of the form:

<pages>
    <page path = "/path/of/page" filename = "new_page" template_path = "/path/of/template" label = "new page">
        <node path = "relative/path/of/node" type = "some_type">
            <prop name = "property_name" type="property_type">VALUE</prop>
            ...
        </node>
        ...
    </page>
    ...
</pages>


Acceptable property types and expected VALUEs:

"String"    -   Any text (HTML characters must be escaped)
"Binary"    -   Text in Base64
"Long"      -   long data type value (eg. 11091992)
"Double"    -   double data type (eg. 11.09)
"Date"      -   Text of form: ±YYYY-MM-DDThh:mm:ss.SSSTZD (see http://jackrabbit.apache.org/api/1.3/org/apache/jackrabbit/test/ISO8601.html)
"Boolean"   -   true/false
"Path"      -   Unknown
"Name"      -   Unknown
"Reference" -   UUID of referencable node (format not known)
In addition, any type may have the suffix "[]" to indicate multiple delimited values

-->

<%
    log.trace("Connector JSP start");
    if (currentNode.hasProperty("payload")==false) {
    // Display Message if connector is being accessed without payload.
%>
    <h1>Vamosa Connector</h1>
    <p> Connector version 1.1 for Day CQ version 5.3</p>
    <p> Connector is now deployed and compiled. 
        Please supply a payload when calling this service!</p>
    <FORM action="?" method="post" onsubmit="setTimeout('window.location.reload()',3000);">
        <P>
            <!-- 'TEXTAREA' represents the property "text" in the connector -->
            <TEXTAREA name="jcr:content/payload" rows="20" cols="80"></TEXTAREA>
            <INPUT type="hidden" name=":redirect" value=<% currentPage.getPath(); %>>
            <INPUT type="submit" value="Send">
        </P>
    </FORM>
<%
    }
    else {
        try{
            // Get XML from "text" property of connector
            String xml = currentNode.getProperty("payload").getValue().getString();
            
            // XML parsing variables to build page
            DocumentBuilderFactory dbf = DocumentBuilderFactory.newInstance();
            DocumentBuilder db = dbf.newDocumentBuilder();
            ByteArrayInputStream xmlStream = new ByteArrayInputStream(xml.getBytes());
            Document doc = db.parse(xmlStream);
            doc.getDocumentElement().normalize();            
            
            //--------------------------------------[Page] variables------------------------------------------
            // pages:               [NodeList] of <page> elements
            // pageElement:         a single <page> [Element]
            // page_path:           attribute of <page>, absolute path of [Page]
            // page_filename:       attribute of <page>, name of the [Page] in the file system (ie, no spaces)  
            // page_templatePath:   attribute of <page>, absolute path of the [Template] for the [Page]
            // page_label:          attribute of <page>, name of the [Page]
            // newPage:             CQ [Page]
            NodeList pages = doc.getElementsByTagName("page");
            Element pageElement;
            String page_path, page_filename, page_templatePath, page_label;
            Page newPage;
            
            //-----------------------[Asset] variables---------------------------
            // assets:              [NodeList] of <asset> elements
            // assetElement:   a single <asset> [Element]
            // asset_filename: attribute of <asset>, name of the [Asset]
            // asset_path:     attribute of <asset>, absolute path of [Asset]
            // asset_type:     attribute of <asset>, type of the [Asset]
            NodeList assets = doc.getElementsByTagName("asset");
            Element assetElement;
            String asset_filename, asset_path, asset_type;
            Node asset;
            
            
            //-----------------------[Node] variables----------------------
            //-------- NOTE: [Node] in CQ refers to javax.jcr.Node --------
            //--------           NOT an org.w3c.dom.Node           --------
            // session:       CQ [Session]
            // parentElement: parent element (<asset> or <page>)
            // elements:      [NodeList] of <node> elements
            // nodeElement:   a single <node> [Element]
            // parent_path:   path of the parent element (<page> or <asset>)
            // node_path:     attribute of <node>, absolute path of CQ [Node]
            // node_type:     attribute of <node>, type of CQ [Node]
            // node:          CQ [Node]
            Session session = currentNode.getSession();
            Element parentElement;
            NodeList nodes;
            Element nodeElement;
            String parent_path, node_path, node_type;
            Node node;
            
            //------------------------------[Property] variables-----------------------------------
            // props:           [NodeList] of <prop> elements
            // propElement:     a single <prop> element
            // prop_name:       attribute of <prop>, name of the [Property]
            // prop_typeName:   attribute of <prop>, text value of [PropertyType]
            // prop_val:        content of <prop>, value of [Property]
            // prop_type:       integer representation of [PropertyType] (used to create [Value])
            // prop_valList:    list of delimited strings to be converted into [Value]s
            // valueFactory:    [ValueFactory] to create [Value]
            // value:           [Value] to set to [Property]
            // values:          list of [Value]s to set to [Property]
            NodeList props;
            Element propElement;
            String prop_name, prop_val, prop_typeName;
            int prop_type;
            String[] prop_valList;
            ValueFactory valueFactory = session.getValueFactory();
            Value value;
            Value [] values;
            
            // Create page...
            if (pages.getLength() > 0){
            	
            	// Get page parameters from XML
                pageElement = (Element) pages.item(0);
                page_path =  pageElement.getAttribute("path");
                page_filename = pageElement.getAttribute("filename");
                page_templatePath = pageElement.getAttribute("template_path");
                page_label = StringEscapeUtils.unescapeHtml(pageElement.getAttribute("label"));
        
                // Create/Access page
                newPage = pageManager.getPage(page_path+'/'+page_filename);
                if (newPage==null){
                    newPage = pageManager.create(page_path,page_filename,page_templatePath,page_label);
                    out.println("[ Page Created ] Successfully!<br/>");
                }else
                    out.println("[ Page Located ] Successfully!<br/>");
                
                // Obfuscate object
                parentElement = pageElement;
                parent_path = page_path+'/'+page_filename;
                
            // ...Or asset
            }else if (assets.getLength() > 0){
            	
            	// Get parameters from XML
            	assetElement = (Element) assets.item(0);
            	asset_filename = assetElement.getAttribute("filename");
            	asset_path = assetElement.getAttribute("path");
            	asset_type = assetElement.getAttribute("type");
            	
            	// Create asset
            	asset = JcrUtil.createPath(asset_path+'/'+asset_filename,"sling:Folder",asset_type,session,false);
            	out.println("[ Asset Created ] Successfully!<br/>");
            	
            	// Obfuscate object
            	parentElement = assetElement;
            	parent_path = asset_path+'/'+asset_filename;
            }
            else {parentElement = null;parent_path = null;}
            
            if (parentElement != null && parent_path != null){
	            
	            // Iterate through nodes, adding the node and each of its subsequent properties
	            nodes = parentElement.getElementsByTagName("node");
	            for (int thisNode = 0; thisNode < nodes.getLength(); thisNode++) {
	        
	                // Get <node> element, attributes & create path
	                nodeElement = (Element) nodes.item(thisNode);
	                node_path =  parent_path+'/'+nodeElement.getAttribute("path");
	                node_type = nodeElement.getAttribute("type");
	                out.println("[ Adding Node ] ("+node_path+") of type ("+node_type+")<br/>");
	                node = JcrUtil.createPath(node_path,node_type,session);
	            
	                // Iterate through <prop> elements to add to 'node'
	                props = nodeElement.getElementsByTagName("prop");
	                for (int thisProp = 0; thisProp < props.getLength(); thisProp++) {
	                    // Get <prop> element & attributes
	                    propElement = (Element) props.item(thisProp);
	                    prop_name = propElement.getAttribute("name");
	                    prop_typeName = propElement.getAttribute("type");
	                    prop_val = StringEscapeUtils.unescapeHtml(propElement.getTextContent());
	                    
	                    out.println("[ Adding Property ] ("+prop_name+") of type ("+prop_typeName+") with value ("+prop_val+")<br/>");
	                    // Set multiple values to property
	                    if (prop_typeName.endsWith("[]")) {
	                        prop_type = PropertyType.valueFromName(prop_typeName.substring(0,prop_typeName.indexOf('[')));
	                        // Delimeter for separated values:
	                        prop_valList = prop_val.split(",");
	                        values = new Value[prop_valList.length];
	                        for (int thisPropVal = 0; thisPropVal < prop_valList.length; thisPropVal++) {
	                            if (prop_type == PropertyType.BINARY)
	                                values[thisPropVal] = valueFactory.createValue(new ByteArrayInputStream(Base64.decodeBase64(prop_valList[thisPropVal].getBytes())));
	                            else if (prop_type == PropertyType.REFERENCE)
	                                values[thisPropVal] = valueFactory.createValue(session.getNodeByUUID(prop_valList[thisPropVal]));
	                            else
	                                values[thisPropVal] = valueFactory.createValue(prop_valList[thisPropVal],prop_type);
	                        }
	                        node.setProperty(prop_name,values);
	                    }
	                    // Set single value to property
	                    else {
	                        prop_type = PropertyType.valueFromName(prop_typeName);
	                        if (prop_type == PropertyType.BINARY)
	                            value = valueFactory.createValue(new ByteArrayInputStream(Base64.decodeBase64(prop_val.getBytes())));
	                        else if (prop_type == PropertyType.REFERENCE)
	                            value = valueFactory.createValue(session.getNodeByUUID(prop_val));
	                        else
	                            value = valueFactory.createValue(prop_val,prop_type);
	                        node.setProperty(prop_name,value);
	                    }
	                }
	            }
            }else{
            	// Page/Asset error
            	out.println("[ ERROR ] Null page/asset!");
            }
            // Remove "text" property from connector
            JcrUtil.setProperty(currentNode,"payload",null);
            // Save page
            out.println("[ Saving ]....<br/>");
            session.save();
            out.println("[ Saved ] Successfully<br/>");
        }catch(Exception e) {
            currentNode.setProperty("payload",(Value)null);
            currentNode.getSession().save();
            out.println("[ERROR!] ------------------------------------------<br/>");
            out.println(e.getMessage());
            out.println("[ERROR!] ------------------------------------------<br/>");
            e.printStackTrace(new java.io.PrintWriter(out));
        }
    }
%>