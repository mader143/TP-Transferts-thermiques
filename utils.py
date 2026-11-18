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
        self.wind_dir = self.excel["Wind Dir (10s deg)"] # h change en fonction de la direction du vent. 0:pas de vent, 9: vent Est, 18: vent du Sud, 27: vent Ouest, 36: vent Nord

class Tuyau:
    def __init__(self, Q_daily = 950, D_iso_out = 0.15, D_iso_in = None, D_tuy_int = None, L = 5300):
        self.Q_daily = Q_daily  # débit m3/jour
        self.D_iso_out = D_iso_out
        self.D_iso_in = D_iso_in
        self.D_tuy_int = D_tuy_int
        self.A = np.pi*D_iso_out**2/4
        self.Q = self.Q_daily/86400    # débit m3/s
        self.V = self.Q/self.A  # vitesse m/s
        self.L = 5300 #m
        
    def set_water_property(self, water_temp = 275, nu_water = 1.5e-6, k_water = 0.565, Pr_water = 12.5):
        # valeur pour 1C
        self.water_temp = water_temp
        self.nu_water = nu_water
        self.k_water = k_water
        self.Pr_water = Pr_water
    
    def set_material_property(self, k_tuyau, k_iso):
        self.k_tuyau = k_tuyau
        self.k_iso = k_iso
        
    def get_R_conv_water(self):
        ReD_water = self._get_ReD(self.V, self.D_iso_out, self.nu_water)
        NuD_water = self._get_NuD_water(ReD_water)
        h_water = self._get_h_water(NuD_water)
        
        return 1/(h_water*np.pi*self.D_iso_out) 
    
    def get_R_cond_tuyau(self):
        R_tuyau = self._get_R_cond(self.D_iso_in, self.D_tuy_int, self.k_tuyau)
        R_iso = self._get_R_cond(self.D_iso_out, self.D_iso_in, self.k_tuyau)
        
        return R_tuyau + R_iso  # en série
    
    def _get_R_cond(self, D_ext, D_int, k_cond):
        return np.log(D_ext/D_int)/(2*np.pi*k_cond)
       
    def _get_ReD(self, V, D_iso_out, nu):
        return V * D_iso_out / nu
        
    def _get_NuD_water(self, ReD):
        return 0.023*(ReD**(4/5))*self.Pr_water**0.3
    
    def _get_h_water(self, NuD):
        return NuD*self.k_water/self.D_iso_out


class Tuyau_Enfouie(Tuyau):
    def __init__(self, Q_daily = 950, D_iso_out = 0.15,  D_iso_in = None, D_tuy_int = None, L = 5300):
        super().__init__(Q_daily, D_iso_out, D_iso_in, D_tuy_int, L)
    
    def set_ground_property(self, depth, k_sol, T_sol):
        self.depth = depth
        self.k_sol = k_sol
        self.T_sol = T_sol
    
    def get_R_sol(self):
        return np.arccosh(2*self.depth/self.D_iso_out)/(2*np.pi*self.k_sol)
    
    def get_R_tot(self):
        return self.get_R_conv_water() + self.get_R_cond_tuyau() +self.get_R_sol() 
    
    def get_linear_heat_flux(self):
        dT = self.water_temp - self.T_sol
        q = dT/self.get_R_tot()
        
        return q
    
    def get_thermal_power(self):
        q = self.get_linear_heat_flux()
        
        return q*self.L
    
    
    


class Tuyau_Ext(Tuyau):
    def __init__(self, Q_daily, D_iso_out, D_iso_in = None, D_tuy_int = None, L = 5300):
        super().__init__(Q_daily, D_iso_out, D_iso_in, D_tuy_int, L)
    
    def get_R_conv_air(self):
        pass
    
    def get_R_rad(self):
        pass
    
    def _get_air_property(self, Tf):
        #Interpolation pour les propriétés de l'air à la bonne température
        #données ia à verifier, ajouter des données pe      <---------------------!!!!
        
        T_table = np.array([-40, -20, 0, 20])
        nu_table = np.array([1.05e-5, 1.20e-5, 1.35e-5, 1.51e-5])  # m2/s
        k_table = np.array([0.0223, 0.0239, 0.0257, 0.0271])       # W/mK
        Pr_table = np.array([0.720, 0.720, 0.715, 0.710])
        
        nu = np.interp(Tf, T_table, nu_table)
        k = np.interp(Tf, T_table, k_table)
        Pr = np.interp(Tf, T_table, Pr_table)
        
        return nu, k, Pr
    
    def _get_h_air(self, Tf, wind_speed):
        
        nu_air, k_air, Pr_air = self._get_air_property(Tf)
        ReD_air = self._get_ReD(wind_speed, self.D_iso_out, nu_air)
        
        if ReD_air*Pr_air >= 0.2: #Churchill-Bernstein
            num = 0.62 * (ReD_air**0.5) * (Pr_air**(1/3))
            den = (1.0 + (0.4 / Pr_air)**(2/3))**(1/4)
            bracket = (1.0 + (ReD_air / 282000.0)**(5/8))**(4/5)
            NuD_air = 0.3 + (num / den) * bracket
            h_air = (NuD_air * k_air) / self.D_iso_out
            
            return h_air
        
        else:
            raise ValueError("Approximation invalide") #quoi faire dans ce cas
    

    
    