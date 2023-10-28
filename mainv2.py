# GUI
import PySimpleGUI as sg
sg.set_options(dpi_awareness=True)

# numpy
import numpy as np

# matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.lines import Line2D

# mf
import multiprocessing as mf
from multiprocessing import freeze_support

# serial
import serial
import serial.tools.list_ports

# excel
from openpyxl.styles import Color, PatternFill, Font, Border
from openpyxl.styles import colors
from openpyxl.cell import Cell
from openpyxl import Workbook

# system
import os
import time
import datetime

# export to excel workbook
def exportExcel(x, t, path):
    
    # create a workbook
    wb = Workbook()
    ws = wb.active

    # append data to worksheet
    # header
    ws.append(["Thời gian", "Li độ"])
    # data
    for i in range(len(x)):
        ws.append([x[i], t[i]])

    wb.save(path)

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
        [sg.Text("Chọn thiết bị đo: ", background_color='#eeeeee', text_color='#000')],
        [sg.Combo(values=portlist, expand_x=True, background_color='#eeeeee', text_color='#000', button_background_color='#eeeeee', button_arrow_color="#000")],
        [sg.Submit(button_text="Kết nối", button_color=('#fff', '#000'))]
    ]
    win = sg.Window("Chọn cổng COM", layout, finalize=True, background_color='#eeeeee', font=("Arial", 10), icon="ruler.ico", keep_on_top=True)
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
            # print(sout)
            try:
                x_val = int(sout[1])
                y_val = int(sout[0])
                # print(x_val, y_val)
                x_out.put(x_val)
                y_out.put(y_val)
            except Exception as e:
                print(e)
                

#  Embedding the Matplotlib toolbar into your application
def draw_figure_w_toolbar(canvas, fig, ax):
    if canvas.children:
        for child in canvas.winfo_children():
            child.destroy()
    figure_canvas_agg = FigureCanvasTkAgg(fig, master=canvas)
    figure_canvas_agg.draw()
    figure_canvas_agg.get_tk_widget().pack(side='right', fill='both', expand=1)
    return figure_canvas_agg.copy_from_bbox(ax.bbox)

def main():
    # crucial for freezing
    freeze_support()
    # create gui
    menu = [
        ['&Tệp', ['&Xuất đồ thị...', '&Thoát']],
        ['&Đồ thị', ['&Tạo mới', '&Thiết lập']],
        ['&Trợ giúp', ['&Thông tin']],
    ]

    layout = [
        [sg.Menu(menu, tearoff=False, key='-menu-')],
        [sg.Canvas(key='fig_cv', expand_x = True, expand_y = True)],
        [sg.StatusBar("Chờ kết nối...", key="-status-", expand_x=True, background_color="#fff", text_color="#000", relief=sg.RELIEF_FLAT, pad=(0, 0), size=(10,1))],
    ]

    window = sg.Window(f'OscView', layout, background_color='#ffffff', icon="ruler.ico", finalize=True, resizable=True)
    # create daemon
    x_out = mf.Queue()
    y_out = mf.Queue()
    currentSerial = mf.Queue()
    ctx = mf.get_context('spawn')
    p = ctx.Process(target=update, args=(x_out, y_out, currentSerial, ))
    p.start()

    # Instantiate Matplotlib figure and axis
    fig = plt.figure()
    ax = fig.add_subplot(111)
    DPI = fig.get_dpi()
    fig.set_size_inches((window.size[0]) / float(DPI), (window.size[1]) / float(DPI))

    # legends
    ax.set_title("Đồ thị giao động")
    ax.set_xlabel("Thời gian (ms)")
    ax.set_ylabel("Li độ (cm)")

    # Create a scatter object for the plot
    scat = ax.scatter([], [], color='b', s=20)
    ax.plot()

    fig.canvas.draw()
    # cache the background
    axbackground = draw_figure_w_toolbar(window['fig_cv'].TKCanvas, fig, ax)

    # Global variables
    max_data_points = 1000  # Maximum number of data points to display
    x = []
    y = []

    start_time = 0

    while True:
        event, values = window.read(timeout=5)

        if event == sg.WIN_CLOSED or event == "Thoát":
            break

        if event == "Thiết lập":
            layout = [
                [
                    sg.Text("Số lượng mẫu hiện thị: ", background_color='#eeeeee', text_color='#000'), 
                    sg.Input(key="-sampleNum-", default_text=max_data_points, background_color='#fff', text_color='#000', border_width=0), 
                ],
                [
                    sg.Button("Lưu cài đặt", key="Submit", button_color=('#fff', '#000'), bind_return_key=True)
                ]
            ]
            win = sg.Window("Xuất đồ thị", layout, finalize=True, background_color='#eeeeee', icon="ruler.ico")
            e, v = win.read()
            if e == "Submit":
                max_data_points = int(v["-sampleNum-"])
                sg.Popup("Đã lưu thiết lập", title = "Thông báo!", button_color="#000", background_color="#fff", text_color="#000", icon="ruler.ico")
                win.close()


        if event == "Tạo mới":
            choice = sg.popup_ok_cancel("Tạo mới đồ thị sẽ xoá hết dữ liệu đồ thị cũ. \nBạn có muốn tiếp tục?", title="Xác nhận!", button_color="#000", background_color="#fff", text_color="#000", icon="ruler.ico")
            if (choice == "OK"): x, y, start_time = [], [], time.time()

        if event == "Xuất đồ thị...":
            dir = str(os.getcwd())
            name = datetime.datetime.now()
            name = name.strftime("%d%m%y_%H%M%S") + ".xlsx"
            layout = [
                [
                    sg.Text("Chọn thư mục: ", background_color='#eeeeee', text_color='#000'), 
                    sg.Input(key="-IN2-" ,change_submits=True, default_text=dir, background_color='#fff', text_color='#000', border_width=0), 
                    sg.FolderBrowse(key="-IN-", button_color=('#fff', '#000'))
                ],
                [
                    sg.Button("Chọn", key="Submit", button_color=('#fff', '#000'))
                ]
            ]
            exp_win = sg.Window("Xuất đồ thị", layout, finalize=True, background_color='#eeeeee', icon="ruler.ico")
            while True:
                event, values = exp_win.read()
                if event == sg.WIN_CLOSED or event=="Exit":
                    break
                elif event == "Submit":
                    dir = values["-IN2-"]
                    dir = dir + f"/{name}"
                    exportExcel(x, y, dir)
                    sg.Popup(f"Đã xuất {name} tại đường dẫn {dir}.", title="Hoàn tất", background_color='#eeeeee', text_color='#000', button_color=('#fff', '#000'))
                    break
            exp_win.close()
        
        # update status bar

        # read data
        if not currentSerial.empty():
            ser_desc = str(currentSerial.get())
            window.TKroot.title(f"OscView - {ser_desc}")
            start_time = time.time()
        while not x_out.empty():
            window["-status-"].update(f"Điểm dữ liệu đã thu thập: x-{len(x)}, y-{len(y)} | Số lượng điểm dữ liệu hiển thị: {max_data_points} | Thời gian đã trôi qua: {int(time.time() - start_time)} (s)")
            x.append(x_out.get())
            y.append(y_out.get())

        # trim data to only a predefined number of samples onscreen
        if (len(x) > max_data_points):
            x_stripped = x[-max_data_points:]
            y_stripped = y[-max_data_points:]
            # Determine the axis limits based on your data
            x_min = min(x_stripped)
            x_max = max(x_stripped)
            # Calculate some padding to make the data span the plot area nicely
            x_padding = (x_max - x_min) * 0.1  # 10% padding on both sides
            # Set the axis limits to span the data with padding
            ax.set_xlim(x_min - x_padding, x_max + x_padding)
            scat = ax.scatter(x_stripped, y_stripped, color='b', s=20)
        else:
            if (len(x) != 0):
                # Determine the axis limits based on your data
                x_min = min(x)
                x_max = max(x)
                # Calculate some padding to make the data span the plot area nicely
                x_padding = (x_max - x_min) * 0.1  # 10% padding on both sides
                # Set the axis limits to span the data with padding
                ax.set_xlim(x_min - x_padding, x_max + x_padding)
            scat = ax.scatter(x, y, color='b', s=20)
        
        # auto adjust plot view + update
        fig.canvas.restore_region(axbackground)
        ax.draw_artist(scat)
        fig.canvas.blit(ax.bbox)
        fig.canvas.flush_events()

    window.close()
    p.kill()
    
