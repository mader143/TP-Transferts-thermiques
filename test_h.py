from utils import Weather_Data, Tuyau_Ext

w_data = Weather_Data("weather_data_52038.xlsx")
w_data.get_properties_for_h_numpy()

tuyau_test = Tuyau_Ext(Q_daily = 950, D_iso_out = 0.15,  D_iso_int = 0.13, D_tuy_int = 0.1)

h_air = tuyau_test._get_h_air(w_data.np_temp_k, w_data.np_wind_speed)

print(h_air)