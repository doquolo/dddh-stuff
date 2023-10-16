import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

import serial
import serial.tools.list_ports

import PySimpleGUI as sg

import numpy as np

import multiprocessing as mf
import atexit

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

# Terminate the background process (p) if it is still running
def stop_background_process():
    if p.is_alive():
        p.terminate()
        p.join()
# setup a function to poll data from mcu
def update(x_out, y_out):
    # start UART
    # mo cua so portselector
    ser, ser_desc = portselector()

    print("Now recording data, enter to finish")
    ser.write("r\n".encode())
    ser.flush()

    # local var 
    # start reading
    while True:
        if (int(ser.in_waiting) > 0):
            sout_raw = ser.readline().decode("utf-8")
            sout = sout_raw.split(";")
            print(sout)
            try:
                x_val = int(sout[1])
                y_val = int(sout[0])
                print(x_val, y_val)
                x_out.put(x_val)
                y_out.put(y_val)
            except Exception as e:
                print(e)
                

if __name__ == '__main__':
    # Register the function to stop the background process when the program exits
    atexit.register(stop_background_process)
    # create daemon
    x_out = mf.Queue()
    y_out = mf.Queue()
    ctx = mf.get_context('spawn')
    q = ctx.Queue()
    p = ctx.Process(target=update, args=(x_out, y_out, ))
    p.start()

    # create graph
    x, y = [], []
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)

    scat = ax.scatter([], [], color='b', s=10)
    ax.plot()

    fig.canvas.draw()

    # cache the background
    axbackground = fig.canvas.copy_from_bbox(ax.bbox)

    plt.show(block=False)
    # start update graph
    while True:
        # read data
        while not x_out.empty():
            x.append(x_out.get())
            y.append(y_out.get())
        
        # trim data to only 1000 sample onscreen
        if (len(x) > 1000):
            x = x[-1000:]
            y = y[-1000:]
            # Determine the axis limits based on your data
            x_min = min(x)
            x_max = max(x)
            # Calculate some padding to make the data span the plot area nicely
            x_padding = (x_max - x_min) * 0.1  # 10% padding on both sides
            # Set the axis limits to span the data with padding
            ax.set_xlim(x_min - x_padding, x_max + x_padding)

        # plot
        scat = ax.scatter(x, y, color='b', s=20)
        fig.canvas.restore_region(axbackground)
        ax.draw_artist(scat)
        fig.canvas.blit(ax.bbox)
        fig.canvas.flush_events()
        

