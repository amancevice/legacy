using System;
using System.Collections.Generic;
using System.IO;
using System.Net;
using System.Text;
using System.Web;
using System.Web.Services;
using System.Web.Services.Protocols;
using Microsoft.SharePoint.Client;
using Microsoft.SharePoint.Client.Utilities;

namespace VamosaServices
{
    [WebService(Namespace = "http://moss2010.vamosa.com/")]
    [WebServiceBinding(ConformsTo = WsiProfiles.BasicProfile1_1)]
    public class SharePointService : System.Web.Services.WebService
    {
        // Members
        private ClientContext clientContext;
        private bool isConnected = false;

        //--------	Constructors/Init  --------\\
        #region INIT
        public SharePointService() { }

        private bool setContext(string contextURL, string user, string password)
        {
            try
            {
                NetworkCredential credential = new NetworkCredential(user, password);
                CredentialCache credentialCache = new CredentialCache();
                credentialCache.Add(new Uri(contextURL), "NTLM", credential);

                clientContext = new ClientContext(new Uri(contextURL));
                clientContext.Credentials = credentialCache;
                Web site = clientContext.Web;
                clientContext.Load(site);
                clientContext.ExecuteQuery();
                return true;
            }
            catch { return false; }
        }
        #endregion

        //--------- SET Methods ----------\\
        #region SET Methods
        [WebMethod]
        public string createItem(string listName, string[] fieldNames, string[] fieldValues, string contextURL, string user, string password)
        {
            isConnected = setContext(contextURL, user, password);
            if (isConnected != true)
                return "Could not establish connection";

            List list = getListByName(listName);
            ListItemCreationInformation itemInfo = new ListItemCreationInformation();
            ListItem newItem = list.AddItem(itemInfo);

            Dictionary<string, string> itemFieldDict = strings2Dict(fieldNames, fieldValues);
            updateItemFields(newItem, itemFieldDict);

            clientContext.Load(newItem);
            clientContext.ExecuteQuery();
            return newItem.Id.ToString();
        }

        [WebMethod]
        public string createFolders(string listName, string[] folders, string contextURL, string user, string password)
        {
            isConnected = setContext(contextURL, user, password);
            if (isConnected != true)
                return "Could not establish connection";

            if (folders.Length == 0)
                return "No folders to create.";

            List list = getListByName(listName);
            Folder folder = list.RootFolder.Folders.Add(folders[0]);
            for (int i = 1; i < folders.Length; i++)
            {
                folder = folder.Folders.Add(folders[i]);
            }

            return "Folders created successfully";
        }

        [WebMethod]
        public string createDiscussion(string listName, string discussionTitle, string[] fieldNames, string[] fieldValues, string contextURL, string user, string password)
        {
            isConnected = setContext(contextURL, user, password);
            if (isConnected != true)
                return "Could not establish connection";

            List list = getListByName(listName);
            ListItem discussion = Utility.CreateNewDiscussion(clientContext, list, discussionTitle);
            Dictionary<string, string> itemFieldDict = strings2Dict(fieldNames, fieldValues);
            updateItemFields(discussion, itemFieldDict);
            discussion.Update();

            clientContext.Load(discussion);
            clientContext.ExecuteQuery();
            return discussion.Id.ToString();
        }

        [WebMethod]
        public string createReply(string listName, int parentID, string[] fieldNames, string[] fieldValues, string contextURL, string user, string password)
        {
            isConnected = setContext(contextURL, user, password);
            if (isConnected != true)
                return "Could not establish connection";

            List list = getListByName(listName);
            ListItem parent = getItemByID(list,parentID);
            ListItem reply = Utility.CreateNewDiscussionReply(clientContext, parent);
            Dictionary<string, string> itemFieldDict = strings2Dict(fieldNames, fieldValues);
            updateItemFields(reply, itemFieldDict);
            reply.Update();

            clientContext.Load(reply);
            clientContext.ExecuteQuery();
            return reply.Id.ToString();
        }

        [WebMethod]
        public string addAttachment(byte[] bytes, string listName, int itemID, string filename, string contextURL, string user, string password)
        {
            VamosaServices.lists.Lists listsService = new VamosaServices.lists.Lists();
            listsService.Credentials = new NetworkCredential(user, password);
            if (contextURL.EndsWith("/"))
                listsService.Url = contextURL + "_vti_bin/lists.asmx";
            else
                listsService.Url = contextURL + "/_vti_bin/lists.asmx";

            return listsService.AddAttachment(listName,itemID.ToString(),filename,bytes);
        }
        
        [WebMethod]
        public string uploadAsset(byte[] bytes, string listName, string filename, string contextURL, string user, string password)
        {
            isConnected = setContext(contextURL, user, password);
            if (isConnected != true)
                return "Could not establish connection";

            FileCreationInformation newFile = new FileCreationInformation();
            newFile.Content = bytes;
            newFile.Url = filename;

            List list = getListByName(listName);
            Microsoft.SharePoint.Client.File uploadFile = list.RootFolder.Files.Add(newFile);
            clientContext.Load(uploadFile);
            clientContext.ExecuteQuery();

            clientContext.ExecuteQuery();
            return "File uploaded successfully";
        }

        [WebMethod]
        public string updateItemFields(string listName, int itemID, string[] fieldNames, string[] fieldValues, string contextURL, string user, string password)
        {
            isConnected = setContext(contextURL, user, password);
            if (isConnected != true)
                return "Could not establish connection";

            List list = getListByName(listName);
            ListItem item = getItemByID(list, itemID);

            Dictionary<string, string> itemFieldDict = strings2Dict(fieldNames, fieldValues);
            updateItemFields(item, itemFieldDict);

            return "Updated fields successfully";
        }

        [WebMethod]
        public string deleteItem(string listName, int itemID, string contextURL, string user, string password)
        {
            isConnected = setContext(contextURL, user, password);
            if (isConnected != true)
                return "Could not establish connection";

            List list = getListByName(listName);
            ListItem item = getItemByID(list, itemID);
            item.DeleteObject();
            
            clientContext.ExecuteQuery();
            return "Object deleted successfully";
        }
        #endregion

        //---------	GET Methods	--------\\
        #region GET Methods
        [WebMethod]
        public string getListsInfo(string contextURL, string user, string password)
        {
            isConnected = setContext(contextURL, user, password);
            if (isConnected != true)
                return "Could not establish connection";

            ListCollection lists = clientContext.Web.Lists;
            clientContext.Load(lists);
            clientContext.ExecuteQuery();

            string listNames = "";
            foreach (List list in lists)
            {
                listNames += list.Title + " : " + list.Id + "\n";
            }
            return listNames;
        }

        [WebMethod]
        public string getListItemsInfo(string listName, string contextURL, string user, string password)
        {
            isConnected = setContext(contextURL, user, password);
            if (isConnected != true)
                return "Could not establish connection";

            List list = getListByName(listName);
            ListItemCollection items = getItemsByQuery(list, CamlQuery.CreateAllItemsQuery().ViewXml);
            clientContext.Load(items);
            clientContext.ExecuteQuery();
            
            string itemInfo = "";
            foreach (ListItem i in items)
            {
                try {
                    itemInfo += i["Title"] + " : " + i.Id + "\n";
                }
                catch {
                    itemInfo += i["FileRef"] + " : " + i.Id + "\n";
                }
            }
            return itemInfo;
        }

        [WebMethod]
        public string getListFoldersInfo(string listName, string contextURL, string user, string password)
        {
            isConnected = setContext(contextURL, user, password);
            if (isConnected != true)
                return "Could not establish connection";

            List list = getListByName(listName);
            ListItemCollection items = getItemsByQuery(list, CamlQuery.CreateAllFoldersQuery().ViewXml);
            clientContext.Load(items);
            clientContext.ExecuteQuery();

            string itemInfo = "";
            foreach (ListItem i in items)
            {
                try
                {
                    itemInfo += i["Title"] + " : " + i.Id + "\n";
                }
                catch
                {
                    itemInfo += i["FileRef"] + " : " + i.Id + "\n";
                }
            }
            return itemInfo;
        }

        [WebMethod]
        public string getItemFields(string listName, int itemID, string contextURL, string user, string password)
        {
            isConnected = setContext(contextURL, user, password);
            if (isConnected != true)
                return "Could not establish connection";

            List list = getListByName(listName);
            ListItem item = getItemByID(list, itemID);
            clientContext.Load(item);
            clientContext.ExecuteQuery();
            
            string itemInfo = "";
            foreach (object field in item.FieldValues)
            {
                itemInfo += field.ToString() + "\n";
            }
            return itemInfo;
        }
        #endregion

        //----------- PRIVATE Methods ----------\\
        #region Private Methods
        private Dictionary<string, string> strings2Dict(string[] keys, string[] values)
        {
            Dictionary<string,string> dict = new Dictionary<string,string>();
            for (int i = 0; i < keys.Length; i++)
            {
                dict[keys[i]] = values[i];
            }
            return dict;
        }
        private List getListByGUID(Guid listGUID) { return clientContext.Web.Lists.GetById(listGUID); }
        private List getListByName(string listName) { return clientContext.Web.Lists.GetByTitle(listName); }
        private ListItem getItemByID(List list, int itemID) { return list.GetItemById(itemID); }
        private ListItemCollection getItemsByQuery(List list, string query)
        {
            CamlQuery q = new CamlQuery();
            q.ViewXml = query;
            return list.GetItems(q);
        }
        private ListItemCollection getItemsByField(List list, string fieldName, string fieldValue)
        {
            string query = String.Format(
              @"<View>
                <Query>
                  <Where>
                    <Eq>
                      <FieldRef Name='{0}'/>
                      <Value Type='Text'>{1}</Value>
                    </Eq>
                  </Where>
                </Query>
                <RowLimit>999</RowLimit>
              </View>", fieldName, fieldValue);
            return getItemsByQuery(list,query);
        }
        private void updateItemFields(ListItem item, Dictionary<string, string> fields)
        {
            foreach (KeyValuePair<string, string> field in fields)
            {
                item[field.Key] = field.Value;
            }
            item.Update();
        }
        #endregion
    }
}
