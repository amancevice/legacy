	using System.Collections.Generic;
	using System.IO;
	using System.Web.Services;
	using System.Web.Services.Protocols;
	using Sitecore.Data;
	using Sitecore.Data.Fields;
	using Sitecore.Data.Items;
	using Sitecore.Data.Managers;
	using Sitecore.Resources.Media;
	using Sitecore.SecurityModel;
	using Sitecore.Visual;
	
	[WebService(Namespace="http://sitecore.net/vamosa/")]
	[WebServiceBinding(ConformsTo = WsiProfiles.BasicProfile1_1)]
	public class VamosaService : System.Web.Services.WebService
	{
		
		//--------	Constructors	--------\\
		public VamosaService () {}
		
		//--------	Directives	--------\\
		[WebMethod]
		public string uploadAsset( string path, string name, string extension, byte[] data, string dbName ) {
			string filename = name+"."+extension;
			Database db = Database.GetDatabase(dbName);
			MemoryStream stream = new MemoryStream(data);
			MediaCreatorOptions mco = new MediaCreatorOptions(); 
			mco.Destination = @"/sitecore/media library"+path+"/"+name;
			mco.Database = db;
			mco.IncludeExtensionInItemName = true;
			using (new SecurityDisabler())
			{
				Item mediaItem = MediaManager.Creator.CreateFromStream(stream,filename,mco);
				return mediaItem.ID.ToString();
			}
			return "None";
	 	}
		[WebMethod]
		public string createItem( string parent_path, string template_path, string name, string dbName, string[] fields, string[] values ) {
			Database db = Database.GetDatabase(dbName);
			using(new SecurityDisabler()) {
				Item newItem = db.CreateItemPath(parent_path+"/"+name);
				if (newItem.Template.ID.ToString() != db.GetItem(template_path).ID.ToString()) {
					newItem.ChangeTemplate(db.GetItem(template_path));
				}
				updateFields(newItem,fields,values);
				return newItem.ID.ToString();
			}
		}
	 	 	
		[WebMethod]
		public void updateFields( string dbName, string path, string[] fields, string[] values ) {
			Database db = Database.GetDatabase(dbName);
			Item item = db.GetItem(path);
			for (int i=0; i<fields.Length; i++) {
				updateField(item,fields[i],values[i]);
			}
		}
		
		private void updateFields( Item item, string[] fields, string[] values ) {
			for (int i=0; i<fields.Length; i++) {
				updateField(item,fields[i],values[i]);
			}
		}
		
		private void updateField( Item item, string field, string value) {
			using (new SecurityDisabler()) {
				using (new EditContext(item)) {
					if (item.Fields[field].CanWrite == true) {
						item.Fields[field].SetValue(value,true);
				   	}
				}
				item.Editing.EndEdit();
			}
		}
		
		[WebMethod]
		public string getItemFields( string id, string dbName ) {
			Database db = Database.GetDatabase(dbName);
			Item item = db.GetItem(id);
			string result = "FIELDS\n";
			foreach (Field f in item.Fields) {
				result += f.Name + ":\t" + f.Value + "\n";
			}
			return result;
		}
	}