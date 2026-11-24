import numpy as np
import matplotlib.pyplot as plt
import pandas as pd


class Weather_Data():
    def __init__(self, path : str):
        self.excel = pd.read_excel(path, nrows=8784) # Garde juste les données de 2024
        self._data_handler() # modifiera les données pour combler les données manquantes
        
    def _data_handler(self) -> None:
        """
        Traite les données manquantes
        """

        # Colonnes à traiter pour les données manquantes
        columns = ["Temp (°C)", "Wind Spd (km/h)", "Wind Dir (10s deg)"]

        # Remplacer les valeurs par les valeurs 24h plus tôt (approximation)
        while self.excel[columns].isna().any().any():

            if self.excel[columns].shift(24).isna().any().any(): # Si c'est dans les premières 24h
                new = self.excel[columns].fillna(self.excel[columns].shift(1))

            else:
                new = self.excel[columns].fillna(self.excel[columns].shift(24))

            if new.equals(self.excel[columns]):
                break
            self.excel[columns] = new

        if self.excel[columns].isna().any().any():
            print(self.excel[self.excel[columns].isna().any(axis=1)])
            raise ValueError("Les données contiennent encore des valeurs manquantes après traitement.")
            

        
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
    def __init__(self, Q_daily = 950, D_iso_out = 0.15, D_iso_int = None, D_tuy_int = None, L = 5300, T_safe = 275):
        self.Q_daily = Q_daily  # débit m3/jour
        self.D_iso_out = D_iso_out
        self.D_iso_int = D_iso_int
        self.D_tuy_int = D_tuy_int
        self.A = np.pi*D_iso_out**2/4
        self.Q = self.Q_daily/86400    # débit m3/s
        self.V = self.Q/self.A  # vitesse m/s
        self.L = L #m
        self.T_safe = T_safe
        self.SIGMA = 5.67e-8
        
    def set_water_property(self, water_temp = 275, nu_water = 1.5e-6, k_water = 0.565, Pr_water = 12.5, rho_water = 1000, cp_water = 4180, T_source = 273.5):
        # valeur pour 1C
        self.water_temp = water_temp
        self.nu_water = nu_water
        self.k_water = k_water
        self.Pr_water = Pr_water
        self.rho_water = rho_water
        self.cp_water = cp_water
        self.T_source = T_source
    
    def set_material_property(self, k_tuyau, k_iso):
        self.k_tuyau = k_tuyau
        self.k_iso = k_iso
        
    def get_R_conv_water(self):
        #linéique
        ReD_water = self._get_ReD(self.V, self.D_iso_out, self.nu_water)
        NuD_water = self._get_NuD_water(ReD_water)
        h_water = self._get_h_water(NuD_water)
        
        return 1/(h_water*np.pi*self.D_iso_out) 
    
    def get_R_tuyau(self):
        #linéique
        R_tuyau = self._get_R_cond(self.D_iso_int, self.D_tuy_int, self.k_tuyau)
        
        return R_tuyau

    def get_R_iso(self):
        R_iso = self._get_R_cond(self.D_iso_out, self.D_iso_int, self.k_iso)
        return R_iso
    
    def _get_R_cond(self, D_ext, D_int, k_cond):
        #linéique
        return np.log(D_ext/D_int)/(2*np.pi*k_cond)
       
    def _get_ReD(self, V, D_iso_out, nu):
        return V * D_iso_out / nu
        
    def _get_NuD_water(self, ReD):
        return 0.023*(ReD**(4/5))*self.Pr_water**0.3
    
    def _get_h_water(self, NuD):
        return NuD*self.k_water/self.D_iso_out


class Tuyau_Enfouie(Tuyau):
    def __init__(self, Q_daily = 950, D_iso_out = 0.15,  D_iso_int = None, D_tuy_int = None, L = 5300):
        super().__init__(Q_daily, D_iso_out, D_iso_int, D_tuy_int, L)
    
    def set_ground_property(self, depth, k_sol, T_sol):
        self.depth = depth
        self.k_sol = k_sol
        self.T_sol = T_sol
    
    def get_R_sol(self):
        #linéique
        return np.arccosh(2*self.depth/self.D_iso_out)/(2*np.pi*self.k_sol)
    
    def get_R_tot(self):
        #linéique
        return self.get_R_conv_water() + self.get_R_tuyau() + self.get_R_iso() +self.get_R_sol() 
    
    # def get_linear_heat_flux(self):
    #     dT = self.water_temp - self.T_sol
    #     q = dT/self.get_R_tot()
    #     return q
    
    # def get_thermal_power(self):
    #     q = self.get_linear_heat_flux()
        
    #     return q*self.L   

    def get_Ti(self):
        #Donne la température d'entrée qui permet à l'eau de rester au dessus de T_safe (2C) (sans traçage)
        self.Ti = (self.T_safe - self.T_sol)*np.exp(self.L/(self.get_R_tot()*self.Q*self.rho_water*self.cp_water)) + self.T_sol
        return self.Ti

    def get_power_source_heating(self):
        #Puissance pour chauffer l'eau de source à la température Ti sécuritaire
        self.Psh = self.Q*self.rho_water*self.cp_water*(self.get_Ti() - self.T_source)
        return self.Psh

    def get_power_tracing(self):
        #Puissance de traçage (circuit thermique qui prends en compte les deux directions de perte de chaleur qin et qout)
        C_dot = self.Q * self.rho_water * self.cp_water
        R_tot = self.get_R_tot()
        R_out = self.get_R_sol() +self.get_R_iso()
        NTU = self.L / (R_tot * C_dot)
        T_eq = (self.T_safe - self.T_source * np.exp(-NTU)) / (1 - np.exp(-NTU))
        self.Pt_lineique = (T_eq - self.T_sol) / R_out
        self.Pt = self.Pt_lineique * self.L
        return self.Pt


class Tuyau_Ext(Tuyau):
    def __init__(self, Q_daily, D_iso_out, D_iso_int = None, D_tuy_int = None, L = 5300):
        super().__init__(Q_daily, D_iso_out, D_iso_int, D_tuy_int, L)

    def set_air_property(self, T_air, wind_speed_ms, emissivite = 0.85, T_env = None):
        self.T_air = T_air          # K
        self.wind_speed = wind_speed_ms # m/s
        self.emissivite = emissivite
        self.T_env = T_air if T_env is None else T_env # K
        self.T_surf = T_air         # K

    def _solve_T_surf(self, tol = 1e-6, max_iter = 100):
        R_int = self.get_R_conv_water() + self.get_R_tuyau() + self.get_R_iso()
        T_surf = self.T_air

        for _ in range(max_iter):
            R_ext = 1/(1/self.get_R_conv_air(T_surf) + 1/self.get_R_rad(T_surf))
            T_surf_new = (self.water_temp/R_int + self.T_env/R_ext) / (1/R_int + 1/R_ext)
            if abs(T_surf_new - T_surf) < tol:
                self.T_surf = T_surf_new
                return self.T_surf
            T_surf = T_surf_new

        self.T_surf = T_surf
        return self.T_surf
    
    def get_R_conv_air(self, T_surf = None):
        #linéique
        if T_surf is None:
            T_surf = self.T_surf
        Tf = 0.5*((T_surf - 273.15) + (self.T_air - 273.15)) # en C pour _get_air_property
        h_air = self._get_h_air(Tf, self.wind_speed)
        self.R_conv_air = 1/(h_air*np.pi*self.D_iso_out)
        return self.R_conv_air
    
    def get_R_rad(self, T_surf = None):
        #linéique
        if T_surf is None:
            T_surf = self.T_surf
        h_rad = self.emissivite * self.SIGMA * (T_surf + self.T_env) * (T_surf**2 + self.T_env**2)
        self.R_rad = 1/(h_rad*np.pi*self.D_iso_out)
        return self.R_rad

    def get_R_tot(self):
        #linéique
        T_surf = self._solve_T_surf()
        return self.get_R_conv_water() + self.get_R_tuyau() + self.get_R_iso() + 1/(1/self.get_R_conv_air(T_surf) + 1/self.get_R_rad(T_surf)) #rad et conv air en parallele
    
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
        #wind speed doit être en m/s
        
        nu_air, k_air, Pr_air = self._get_air_property(Tf)
        ReD_air = self._get_ReD(wind_speed, self.D_iso_out, nu_air)
        
        if ReD_air*Pr_air >= 0.2: #Churchill-Bernstein
            num = 0.62 * (ReD_air**0.5) * (Pr_air**(1/3))
            den = (1.0 + (0.4 / Pr_air)**(2/3))**(1/4)
            bracket = (1.0 + (ReD_air / 282000.0)**(5/8))**(4/5)
            NuD_air = 0.3 + (num / den) * bracket
        
        else: #Convection naturelle, Churchill and Chu (RaD < 10^12)
            g = 9.81
            Tf_k = Tf + 273.15
            beta = 1.0 / Tf_k
            dT = max(self.T_surf - self.T_air, 1e-3)
            RaD = (g * beta * dT * (self.D_iso_out**3) / (nu_air**2)) * Pr_air

            NuD_air = (
                0.60
                + (0.387 * (RaD**(1/6)))
                / ((1.0 + (0.559 / Pr_air)**(9/16))**(8/27))
            )**2

        h_air = (NuD_air * k_air) / self.D_iso_out
        return h_air
    

    
    