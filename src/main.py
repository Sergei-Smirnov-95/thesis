
import json
import os
import time
import Adafruit_CharLCD as LCD
import threading

from http.server import BaseHTTPRequestHandler, HTTPServer

from .TemperatureSensor import TemperatureSensor
from .HumiditySensor import HumiditySensor
from .PressureSensor import PressureSensor
from .VibrationSensor import VibrationSensor


HOST_PORT = 80

TEMPERATURE_SENSORS = [TemperatureSensor(i) for i in range(0, 4)]
HUMIDITY_SENSOR = HumiditySensor(21)
PRESSURE_SENSOR = PressureSensor()
VIBRATION_SENSOR = VibrationSensor(5)

lcd_rs = 25
lcd_en = 24
lcd_d4 = 23
lcd_d5 = 17
lcd_d6 = 18
lcd_d7 = 22
lcd_backlight = 4

lcd_columns = 16
lcd_rows = 2

lock = threading.Lock()

lcd = LCD.Adafruit_CharLCD(lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6, lcd_d7,
                           lcd_columns, lcd_rows, lcd_backlight)


class MyHttpServer(BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.send_header('Access-Control-Allow-Origin','*')
        self.end_headers()

    def do_GET(self):
        try:
            needFile = False
            root = "/home/pi/team_3/web"
            filename = root + self.path

            if self.path == "/prkpsb-monitor/":
                fileneme = root + "index.html"  

            elif self.path == "/prkpsb-monitor/all":
                self._set_headers()
                meas = get_measures().encode()
                self.wfile.write(meas)
                return
            
            elif self.path == "/prkpsb-monitor/hum":
                needFile = True
            
            elif self.path == "/prkpsb-monitor/vib":
                needFile = True
            
            elif self.path == "/prkpsb-monitor/press":
                needFile = True

            elif self.path == "/prkpsb-monitor/t1":
                 needFile = True

            
            elif self.path == "/prkpsb-monitor/t2":
                 needFile = True

            
            elif self.path == "/prkpsb-monitor/t3":
                 needFile = True
 
            
            elif self.path == "/prkpsb-monitor/t4":
                 needFile = True
            
            if needFile == True:
                self._set_headers()
                with lock:
                    f = open("/home/pi/team_3"+"/history" + self.path,'r')
                    self.wfile.write(f.read().encode())
                    f.close()
            else:
                self.send_response(200)
                if filename[-4:] == '.css':
                    self.send_header('Content-type','text/css')
                elif filename[-5:] == '.json':
                    self.send_header('Content-type','application/javascript')
                elif filename[-3:] == '.js':
                    self.send_header('Content-type','application/javascript')
                elif filename[-4:] == '.ico':
                    self.send_header('Content-type','image/x-icon')
                else:
                    self.send_header('Content-type','text/html')
                self.end_headers()
                with open(filename,'rb') as fh:
                    html= fh.read()
                    self.wfile.write(html)

        except IOException:
            self.send_error(404,"File Not Found".encode())


def get_measures():
    measures = {
            "Temperature": {"Temperature_{}".format(i): sensor.get_meas() for i, sensor in enumerate(TEMPERATURE_SENSORS)},
            "Humidity": HUMIDITY_SENSOR.get_meas(),
            "Pressure": PRESSURE_SENSOR.get_meas(),
            "Vibration": VIBRATION_SENSOR.get_meas()
            }

    return json.dumps(measures)

def print_lcd():
    t = threading.currentThread()
    key = 0
    while getattr(t, "do_run", True):
        meas2=""
        meas = str("Hum="+str(HUMIDITY_SENSOR.get_meas())+" Vib=" +str(VIBRATION_SENSOR.get_meas())+"\n Press="+str(PRESSURE_SENSOR.get_meas()))
        for i,sensor in enumerate(TEMPERATURE_SENSORS):
            meas2 += str("T{}=".format(i+1) + str(sensor.get_meas()) + " " )
            if i == 1:
                meas2 += "\n"
        lcd.clear()

        if key == 0:
            lcd.message(meas)
            key = 1
        elif key == 1:
            lcd.message(meas2)
            key = 0

        time.sleep(5)
    print("Printing stopped")

def save_data():
    t = threading.currentThread()
    cwd = "/home/pi/team_3"
    while getattr(t, "do_run", True):
        files=[cwd+"/history/prkpsb-monitor/t1",cwd+"/history/prkpsb-monitor/t2",
                cwd+"/history/prkpsb-monitor/t3",cwd+"/history/prkpsb-monitor/t4",
                cwd+"/history/prkpsb-monitor/press",cwd+"/history/prkpsb-monitor/vib",
                cwd+"/history/prkpsb-monitor/hum"]      
        i = 0
        for current in files:
            with lock:
                data = []
                with open(current) as fr:
                    for line in fr:
                        data.append(line)
                with open(current,'w') as fw:   
                    if i == 0:
                        newData = str(TemperatureSensor(0).get_meas()) 
                    if i == 1:
                        newData = str(TemperatureSensor(1).get_meas()) 
                    if i == 2:
                        newData = str(TemperatureSensor(2).get_meas())                     
                    if i == 3:
                        newData = str(TemperatureSensor(3).get_meas()) 
                    if i == 4:
                        newData = str(PRESSURE_SENSOR.get_meas())    
                    if i == 5:
                        newData = str(VIBRATION_SENSOR.get_meas())
                    if i == 6:
                        newData = str(HUMIDITY_SENSOR.get_meas())
                    if len(data) <= 99:
                        print(newData, ''.join(str(item) for item in data), sep='\n', file=fw)
                    elif len(data) > 99:
                        print(newData, ''.join(str(item) for item in data[:99]), sep='\n', file=fw)
            i += 1
        time.sleep(900)

def run():
    server_address = ('', HOST_PORT)
    httpserv = HTTPServer(server_address, MyHttpServer)
    t_lcd = threading.Thread(target=print_lcd)
    t_lcd.start()
    t_save = threading.Thread(target=save_data)
    t_save.start()
    print("Starting http...")
    try:
        
        httpserv.serve_forever()

    except KeyboardInterrupt:
        print("Stop http and services")
        t_lcd.do_run = False
        t_save.do_run = False
        t_lcd.join()
        t_save.join()


if __name__ == '__main__':
    run()

