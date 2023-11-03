import datetime
import pandas as pd
import os
import shutil
import warnings
import time

class ModelManager:
    def __init__(self, folder_name="models"):
        self._folder_name = folder_name
        
        # Create the models folder, if necessary
        os.makedirs(self._folder_name, exist_ok=True)
        
        # Check if inforefresh.py script is already been copied to the models folder
        #  if not, create a copy
        
        script_dst_path = os.path.join(self._folder_name, "inforefresh.py")
        if not os.path.isfile(script_dst_path):
            # search for the script to be copied in the modelmanager package
            script_scr_path = os.path.join(os.path.dirname(__file__), "inforefresh.py")
            
            # if the original script exists, copy it, otherwise, launch a warning
            if os.path.isfile(script_scr_path):
                shutil.copyfile(script_scr_path, script_dst_path)
            else:
                warnings.warn(f"Script {script_scr_path} not found.")
        
    def get_folder(self):
        return self._folder_name

    def store_modelinfo(self, modelinfo):       
           
        # Retrieve the dataframe containing info
        # Check if someone else is using the dataframe
        can_write = self._lock_info()
        
        if can_write:
            dataframe = self._retrieve_info()
            
            # Check if the id of the model already exists
            if (dataframe["id"] == modelinfo["id"][0]).any():
                # Add any new column that has been added to the latest version of the dataframe
                for key in modelinfo.keys():
                    if key not in dataframe.columns:
                        dataframe[key] = pd.NA
                # Substitute the old row of the dataframe with the new modelinfo
                row_index = dataframe[dataframe["id"] == modelinfo["id"].loc[0]].index[0]
                dataframe.loc[row_index] = modelinfo.loc[0]
                
            # if the model id does not exists
            else:
                dataframe = pd.concat([dataframe, modelinfo])

            # Rearrange indexes of the dataframe
            dataframe.reset_index(drop=True)
            
            self._store_info(dataframe)
            
            self._unlock_info()
            
    def _lock_info(self):
        lock_file = os.path.join(self._folder_name, ".infolock")
        start_time = time.time()
        can_access = False
        while not can_access:
            if not os.path.isfile(lock_file):
                open(lock_file, "a").close() # create lock file
                can_access = True
            if time.time()-start_time > 60: # wait 1 minute
                warnings.warn(f"Lock timer expired. modelsinfo.csv is locked.")
                break
        
        return can_access
    
    def _unlock_info(self):
        # Release csv lock
        success = False
        lock_file = os.path.join(self._folder_name, ".infolock")
        if os.path.isfile(lock_file):
            os.remove(lock_file)
            success = True
            
        return success
    
    def _retrieve_info(self):
        csv_path = os.path.join(self._folder_name, "modelsinfo.csv")
            
        # Retrieve modelsinfo
        if os.path.isfile(csv_path):
            dataframe = pd.read_csv(csv_path)
        else:
            dataframe = pd.DataFrame({"id":[]})
            
        return dataframe
    
    def _store_info(self, dataframe):
        # Store back the dataframe on disk
        csv_path = os.path.join(self._folder_name, "modelsinfo.csv")
        dataframe.to_csv(csv_path, index=False)
    
class ModelInfo:
    def __init__(self, modelmanager, model_id=None):
        self.modelmanager = modelmanager
        # if no model id is provided, generate it
        # otherwise use the given id
        # if the id already exists, the model is taken from the model_handler
        if model_id is None:
            self._generate_unique_id()
            self.info = pd.DataFrame({"id": [self.id]})
        else:
            self.id = model_id
            if (self.modelmanager.modelsinfo["id"] == model_id).any():
                self.info = self.modelmanager.modelsinfo[self.modelmanager.modelsinfo["id"] == model_id]
            else:
                self.info = pd.DataFrame({"id": [self.id]})
          
    def _generate_unique_id(self):
        # generate an id for the model based on date and time
        now = datetime.datetime.now()
        unique_id = now.strftime("%Y%m%d_%H%M")[2:]
        
        # retrieve the model ids list
        can_write = self._lock_idlist()
        
        if can_write:
            dataframe = self._retrieve_idlist()
        
            count = 1    
            new_id = unique_id + "_0"
            for cid in dataframe["id"]:
                if str(cid) == str(new_id):
                    new_id = f"{unique_id}_{count}"
                    count += 1
            self.id = new_id 
            
            dataframe = pd.concat([dataframe, pd.DataFrame({"id":[new_id]})])
            self._store_idlist(dataframe)
            
            self._unlock_idlist()
        else:
            raise Exception("Could not generate a unique id for the model.")
        
    def get_path(self):
        # get the path containing the model
        # if it doesn't exist, create it
        folder = os.path.join(self.modelmanager.get_folder(), self.id)
        os.makedirs(folder, exist_ok=True)
        return folder
                                     
    def add(self, info_name, value):
        # add a key + value pair to the model dataframe
        self.info[info_name] = [value]
        
    def store(self):
        # store to disk through model manager
        self.modelmanager.store_modelinfo(self.info)
        
    def _lock_idlist(self):
        lock_file = os.path.join(self.modelmanager.get_folder(), ".idlistlock")
        start_time = time.time()
        can_access = False
        while not can_access:
            if not os.path.isfile(lock_file):
                open(lock_file, "a").close() # create lock file
                can_access = True
            if time.time()-start_time > 60: # wait 1 minute
                warnings.warn(f"Lock timer expired. usedidlist.csv is locked.")
                break
        
        return can_access
    
    def _unlock_idlist(self):
        # Release csv lock
        success = False
        lock_file = os.path.join(self.modelmanager.get_folder(), ".idlistlock")
        if os.path.isfile(lock_file):
            os.remove(lock_file)
            success = True
            
        return success
    
    def _retrieve_idlist(self):
        csv_path = os.path.join(self.modelmanager.get_folder(), "usedidlist.csv")
            
        # Retrieve modelsinfo
        if os.path.isfile(csv_path):
            dataframe = pd.read_csv(csv_path)
        else:
            dataframe = pd.DataFrame({"id":[]})
            
        return dataframe
    
    def _store_idlist(self, dataframe):
        # Store back the dataframe on disk
        csv_path = os.path.join(self.modelmanager.get_folder(), "usedidlist.csv")
        dataframe.to_csv(csv_path, index=False)