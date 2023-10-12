import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

import serial
import serial.tools.list_ports

import PySimpleGUI as sg

import numpy as np

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
        [sg.Submit(button_text="Kết nối", button_color=('#fff', '#000'))]
    ]
    win = sg.Window("Chọn cổng COM", layout, finalize=True, background_color='#eeeeee', font=("Arial", 10))
    e, v = win.read()
    win.close()

    # chon cong com den esp32
    # i = int(input("Chọn cổng COM để kết nối đến ESP32: "))
    port = ports[portlist.index(v[0])]
    ser = serial.Serial(str(port.name), 115200)
    return ser, str(port.description)


# mo cua so portselector
ser, ser_desc = portselector()

print("Now recording data, enter to finish")
ser.write("r\n".encode())
ser.flush()

plt.ion()
fig = plt.figure() 
ax = fig.add_subplot(111)

plt.ylim([0,50])
plt.xlim([0,100])

data = []
line,  = ax.plot(data)

ax.set_xlabel('Time (ms)')
ax.set_ylabel('Data')
ax.set_title('Realtime Data Plot')
ax.legend (['Data'], loc='upper right')

while True:
    if (int(ser.in_waiting) > 0):
        try:
            sout_raw = ser.readline().decode("utf-8")
            sout = sout_raw.split(";")
            new_data = int(sout[0])
            print(new_data)
            data = np.append(data,new_data)
            if len(data) > 100:
                data = data[-100:]

            line.set_ydata(data) 
            line.set_xdata(np.arange(len(data)))
            plt.draw()
            plt.pause (0.05)
        except Exception as e:
            print(e)

ser.close()

