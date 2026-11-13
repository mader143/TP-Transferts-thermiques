import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

class Weather_Data():
    def __init__(self, path : str):
        self.excel = pd.read_excel(path)
        self._data_handler() # modifiera les données pour combler les données manquantes
        
    def _data_handler(self) -> None:
        """
        Traite les données manquantes
        """
        
        # il faut ajouter la logique pour sélectionner une période d'intérêt / méthode d'interpollation ou tronquer / etc.
        
        self.year = self.excel["Year"]
        self.month = self.excel["Month"]
        self.day = self.excel["Day"]
        self.hour = self.excel["Time (LST)"]
        self.temp_c = self.excel["Temp (°C)"]         # données manquantes... Il va falloir soit interpoller / prendre moyenne / couper
        self.temp_k = self.temp_c + 273.15
        self.wind_speed = self.excel["Wind Spd (km/h)"]
        
        