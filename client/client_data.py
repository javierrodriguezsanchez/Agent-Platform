import os
import json

class client_data:
    def __init__(self):
        try:
            with open(os.path.join('data.json')) as f:
                self.data = json.load(f)
        except:
            # Crear un nuevo diccionario vacío
            self.data = {}
            
            # Crear el archivo JSON con el diccionario vacío
            with open('data.json', 'w') as archivo:
                json.dump(self.data, archivo)

    def load(self,x):
        if x not in self.data.keys():
            return None
        return self.data[x]
    
    def save(self,field,content):
        self.data[field]=content
        # Crear el archivo JSON con el diccionario vacío
        with open('data.json', 'w') as archivo:
            json.dump(self.data, archivo)