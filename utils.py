import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from scipy.interpolate import splprep, splev

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
        self.wind_dir = self.excel["Wind Dir (10s deg)"] # h change en fonction de la direction du vent. 0:pas de vent, 9: vent Est, 18: vent du Sud, 27: vent Ouest, 36: vent Nord

class Tuyau:
    def __init__(self, Q_daily, D_iso_out, D_iso_in = None, D_mat_in = None):
        self.Q_daily = Q_daily  # débit m3/jour
        self.D_iso_out = D_iso_out
        self.D_iso_in = D_iso_in
        self.D_mat_in = D_mat_in
        self.A = np.pi*D_iso_out**2/4
        self.Q = self.Q_daily/86400    # débit m3/s
        self.V = self.Q/self.A  # vitesse m/s
        
    def set_water_property(self, nu_water = 1.5e-6, k_water = 0.565, Pr_water = 12.5):
        # valeur pour 1C
        self.nu_water = nu_water
        self.k_water = k_water
        self.Pr_water = Pr_water
    
    def set_material_property(self, k_tuyau, k_iso):
        self.k_tuyau = k_tuyau
        self.k_iso = k_iso
        
    def get_ReD_water(self):
        return self.V * self.D_iso_out / self.nu_water
        
    def get_NuD_water(self, ReD):
        return 0.023*(ReD**(4/5))*self.Pr_water**0.3
    
    def get_h_water(self, NuD):
        return NuD*self.k_water/self.D_iso_out
    
    def get_R_conv_water(self, h_i):
        return 1/(h_i*np.pi*self.D_iso_out)
    
    def get_R_cond_tuyau(self):
        R_tuyau = ...
        R_iso = ...
        
        return
    

class Tuyau_Enfouie(Tuyau):
    def __init__(self, Q_daily, D_iso_out, D_iso_in = None, D_mat_in = None):
        super().__init__(Q_daily, D_iso_out, D_iso_in = None, D_mat_in = None)
    
    def set_ground_property(self, depth, k_sol):
        self.depth = depth
        self.k_sol = k_sol
    
    def get_R_sol(self):
        return np.arccosh(2*self.depth/self.D_iso_out)/2*np.pi*self.k_sol


class Tuyau_Ext(Tuyau):
    def __init__(self, Q_daily, D_iso_out, D_iso_in = None, D_mat_in = None):
        super().__init__(Q_daily, D_iso_out, D_iso_in, D_mat_in)
    
    def get_h_air(self):
        pass
    
    def get_R_conv_air(self):
        pass