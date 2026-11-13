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


class Pipe3D:
    def __init__(self, r, R):
        self.lat_long = [
            (60.062830940231535, -77.22336734920782), (60.06128478681783, -77.22101103213207), 
            (60.05923765534929, -77.22040013511241), (60.05712505675619, -77.2217528356559), 
            (60.05403214274848, -77.22105466763345), (60.052834105226324, -77.22232009717415), 
            (60.04945758366282, -77.22524367575943), (60.04623322780488, -77.24470510998243), 
            (60.046320376695796, -77.24837049210028), (60.0449695430374, -77.25186133221251),
            (60.04477344968718, -77.25631215335564), (60.04194086014124, -77.26089388217406), 
            (60.0382363381365, -77.2658246938326), (60.03756076285704, -77.26966461795608), 
            (60.03930415475071, -77.27695174669039)
        ]
        
        # 1. Conversion en coordonnées locales (mètres)
        self.coords = self._latlon_to_local_meters(self.lat_long)
        
        # 2. Interpolation 3D / Lissage de la trajectoire (ex: 200 points le long du tuyau)
        x = self.coords[:, 0]
        y = self.coords[:, 1]
        # On peut simuler une altitude z (par exemple plate ou basée sur un profil fictif / terrain)
        z = np.zeros_like(x) 
        
        # Paramétrique spline
        tck, u = splprep([x, y, z], s=0, k=3)
        u_fine = np.linspace(0, 1, 20)
        self.x_smooth, self.y_smooth, self.z_smooth = splev(u_fine, tck)
        
        # 3. Affichage 3D
        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(projection='3d')
        
        # Tracer la ligne centrale lissée du tuyau
        ax.plot(self.x_smooth, self.y_smooth, self.z_smooth, label="Axe du tuyau", color="grey", linewidth=3)
        
        # Si vous voulez dessiner des anneaux de rayon R le long du tuyau pour faire un effet "visuel cute" 3D :
        theta = np.linspace(0, 2*np.pi, 30)
        for i in range(0, len(u_fine), 15):  # Tous les 15 points
            cx, cy, cz = self.x_smooth[i], self.y_smooth[i], self.z_smooth[i]
            # Cercle simple perpendiculaire (approximation visuelle)
            ring_x = cx + R * np.cos(theta)
            ring_y = cy + R * np.sin(theta)
            ring_z = np.full_like(theta, cz)
            ax.plot(ring_x, ring_y, ring_z, color='blue', alpha=0.3)

        ax.set_title("Visualisation 3D du tuyau")
        ax.set_xlabel("X (m)")
        ax.set_ylabel("Y (m)")
        ax.set_zlabel("Z (m)")
        plt.show()

    def _latlon_to_local_meters(self, coords):
        R_earth = 6371000.0
        lat0, lon0 = coords[0]
        lat0_rad = np.radians(lat0)
        local_coords = []
        for lat, lon in coords:
            dlat = np.radians(lat - lat0)
            dlon = np.radians(lon - lon0)
            x = dlon * np.cos(lat0_rad) * R_earth
            y = dlat * R_earth
            local_coords.append((x, y))
        return np.array(local_coords)