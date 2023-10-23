import datetime
import pandas as pd
import os
import shutil
import warnings

class ModelHandler:
    def __init__(self, handler_name="models"):
        self.handler_name = handler_name
        # Retrieve info of the models if they exist
        #  otherwise, initialize the dataset
        self.modelsinfo = None
        self.retrieve_modelsinfo()
        # Create the folder containing the models
        os.makedirs(handler_name, exist_ok=True)

    def retrieve_modelsinfo(self):
        # Retrieve the csv containing model info,
        #  if it does not exist, create a new dataframe
        if os.path.isfile(os.path.join(self.handler_name, "modelsinfo.csv")):
            self.modelsinfo = pd.read_csv(os.path.join(self.handler_name, "modelsinfo.csv"))
        else:
            self.modelsinfo = pd.DataFrame({"id":[]})

    def store_modelsinfo(self):
        # Check if inforefresh.py script is already been copied to the models folder
        #  if not, create a copy
        if not os.path.isfile(os.path.join(self.handler_name, "inforefresh.py")):
            script_name = os.path.join(os.path.dirname(__file__), "inforefresh.py")
            if os.path.isfile(script_name):
                shutil.copyfile(script_name, os.path.join(self.handler_name, "inforefresh.py"))
            else:
                warnings.warn(f"Script {script_name} not found.")
        # Store the info dataframe to modelsinfo.csv        
        self.modelsinfo.to_csv(os.path.join(self.handler_name, "modelsinfo.csv"), index=False)
        
    def add_model(self, new_modelinfo):
        # Add a model to the dataframe if new
        # if the model already exists, update it with current info
        if (self.modelsinfo["id"] == new_modelinfo["id"][0]).any():
            self.modelsinfo[self.modelsinfo["id"] == new_modelinfo["id"][0]] = new_modelinfo
        else:
            self.modelsinfo = pd.concat([self.modelsinfo, new_modelinfo])
        self.modelsinfo.reset_index(drop=True)
        # Store the dataframe on disk
        self.store_modelsinfo()   
        
    
class ModelInfo:
    def __init__(self, model_handler, model_id=None):
        self.model_handler = model_handler
        # if no model id is provided, generate it
        # otherwise use the given id
        # if the id already exists, the model is taken from the model_handler
        if model_id is None:
            self._generate_unique_id()
            self.info = pd.DataFrame({"id": [self.id]})
        else:
            self.id = model_id
            if (self.model_handler.modelsinfo["id"] == model_id).any():
                self.info = self.model_handler.modelsinfo[self.model_handler.modelsinfo["id"] == model_id]
            else:
                self.info = pd.DataFrame({"id": [self.id]})
          
    def _generate_unique_id(self):
        # generate a unique id for the model based on date and time
        now = datetime.datetime.now()
        unique_id = now.strftime("%Y%m%d_%H%M")[2:]
        id_list = self.model_handler.modelsinfo["id"]
        count = 1    
        new_id = unique_id + "_0"
        for cid in id_list:
            if str(cid) == str(new_id):
                new_id = f"{unique_id}_{count}"
                count += 1
        self.id = new_id 
        
    def get_path(self, file_name="model", file_extension=None):
        # get the path containing the model
        # it is possible to add a file_name and file_extension to
        # generate the path of a file contained in the model path
        self.store()
        folder = os.path.join(self.model_handler.handler_name, self.id)
        os.makedirs(folder, exist_ok=True)
        if file_extension is None:
            return os.path.join(folder, file_name)
        else:
            return os.path.join(folder, file_name+"."+file_extension)
                                     
    def add(self, info_name, value):
        # add a key + value pair to the model dataframe
        self.info[info_name] = [value]
        
    def store(self):
        # add the model to the model_handler dataframe
        self.model_handler.add_model(self.info)