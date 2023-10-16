from openpyxl.styles import Color, PatternFill, Font, Border
from openpyxl.styles import colors
from openpyxl.cell import Cell
from openpyxl import Workbook

import PySimpleGUI as sg

import serial
import serial.tools.list_ports

import datetime 
import time
import os

import keyboard

# trinh chon cong com
def portselector():
    # hien thi tat ca cong serial dang mo tren may tinh
    ports = serial.tools.list_ports.comports()
    ports = sorted(ports)

    portlist = []
    for i in range(len(ports)):
        port = ports[i].name
        desc = ports[i].description
        hwid = ports[i].hwid
        portlist.append("{}. {}: {} [{}] \n".format(i+1, port, desc, hwid))
        # print("{}: {} [{}]".format(port, desc, hwid))

    # print(portlist)

    layout = [
        [sg.Text("Chọn cổng COM đến ESP32: ", background_color='#eeeeee', text_color='#000')],
        [sg.Combo(values=portlist, expand_x=True, background_color='#eeeeee', text_color='#000', button_background_color='#eeeeee', button_arrow_color="#000")],
        [sg.Submit(button_text="Kết nối", button_color=('#fff', '#000'), tooltip="pmeicute")]
    ]
    win = sg.Window("Chọn cổng COM", layout, finalize=True, background_color='#eeeeee', font=("Arial", 10))
    e, v = win.read()
    win.close()

    # chon cong com den esp32
    # i = int(input("Chọn cổng COM để kết nối đến ESP32: "))
    port = ports[portlist.index(v[0])]
    ser = serial.Serial(str(port.name), 115200, timeout=0.050)
    return ser, str(port.description)

# get current mills time
def current_milli_time():
    return round(time.time() * 1000)

# export to excel workbook
def exportExcel(x, t, path):
    
    # create a workbook
    wb = Workbook()
    ws = wb.active

    # append data to worksheet
    # header
    ws.append(["Li độ", "Thời gian"])
    # data
    for i in range(len(x)):
        ws.append([x[i], t[i]])

    wb.save(path)



# mo cua so portselector
ser, ser_desc = portselector()
# bien luu du lieu
x = []
t = []

os.system("cls")
print("Now recording data, enter to finish")
ser.write("r\n".encode())
ser.flush()

while True:
    if (int(ser.in_waiting) > 0):
        try:
            sout_raw = ser.readline().decode("utf-8")
            sout = sout_raw.split(";")
            print(sout)
            x.append(int(sout[0]))
            t.append(int(sout[1]))
            
        except Exception as e:
            print(e)
    if keyboard.is_pressed('enter'):
        print("Stop recording")
        break
    
path = input("Enter path for exported file, leave blank if you want to save to the same folder: ")
if (path == ""):
    exportExcel(x, t, f"{datetime.datetime.now().strftime('%d%m%y_%H%M%S')}.xlsx")
else:
    exportExcel(x, t, f"{path}/{datetime.datetime.now().strftime('%d%m%y_%H%M%S')}.xlsx")