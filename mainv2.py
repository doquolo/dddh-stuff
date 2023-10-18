import PySimpleGUI as sg
sg.set_options(dpi_awareness=True)

import numpy as np

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.lines import Line2D

import multiprocessing as mf

import serial
import serial.tools.list_ports

# serial
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


# setup a function to poll data from mcu
def update(x_out, y_out, currentSerial):
    # start UART
    # mo cua so portselector
    ser, ser_desc = portselector()

    currentSerial.put(ser_desc)

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
                

# Embedding the Matplotlib toolbar into your application
def draw_figure_w_toolbar(canvas, fig):
    if canvas.children:
        for child in canvas.winfo_children():
            child.destroy()
    figure_canvas_agg = FigureCanvasTkAgg(fig, master=canvas)
    figure_canvas_agg.draw()
    figure_canvas_agg.get_tk_widget().pack(side='right', fill='both', expand=1)

if __name__ == "__main__":
    # create gui
    layout = [
        [sg.Canvas(key='fig_cv', size=(500 * 2, 700))],
    ]

    window = sg.Window(f'OscView', layout, background_color='#ffffff')
    # create daemon
    x_out = mf.Queue()
    y_out = mf.Queue()
    currentSerial = mf.Queue()
    ctx = mf.get_context('spawn')
    q = ctx.Queue()
    p = ctx.Process(target=update, args=(x_out, y_out, currentSerial, ))
    p.start()

    
    # Instantiate Matplotlib figure and axis
    fig = plt.figure()
    ax = fig.add_subplot(111)
    DPI = fig.get_dpi()
    fig.set_size_inches(505 * 2 / float(DPI), 707 / float(DPI))

    # legends
    ax.set_title("Đồ thị giao động")
    ax.set_xlabel("Thời gian (ms)")
    ax.set_ylabel("Li độ (cm)")

    # Create a Line2D object for the line plot
    line = Line2D([], [], color='b')
    ax.add_line(line)

    fig.canvas.draw()
    # cache the background
    axbackground = fig.canvas.copy_from_bbox(ax.bbox)

    # Global variables
    max_data_points = 500  # Maximum number of data points to display
    x = []
    y = []

    while True:
        event, values = window.read(timeout=5)

        if event == sg.WIN_CLOSED:
            break

        # read data
        if not currentSerial.empty():
            ser_desc = str(currentSerial.get())
            window.TKroot.title(f"OscView - {ser_desc}")
        while not x_out.empty():
            x.append(x_out.get())
            y.append(y_out.get())

        # trim data to only 1000 sample onscreen
        if (len(x) > max_data_points):
            x = x[-max_data_points:]
            y = y[-max_data_points:]

        # Update the Line2D object with the new data
        line.set_data(x, y)
        
        # auto adjust plot view + draw
        ax.autoscale()
        ax.relim()
        fig.canvas.restore_region(axbackground)
        ax.draw_artist(line)
        draw_figure_w_toolbar(window['fig_cv'].TKCanvas, fig)

    window.close()
    p.kill()
    
