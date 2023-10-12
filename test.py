import matplotlib.pyplot as plt

import numpy as np

plt.ion()
fig = plt.figure() 
ax = fig.add_subplot(111)

plt.ylim([0,50])
plt.xlim([0,100])

data = np.random.randint(0, 50, size=(50,)) 
line,  = ax.plot(data)

ax.set_xlabel('Time (ms)')
ax.set_ylabel('Data')
ax.set_title('Realtime Data Plot')
ax.legend (['Data'], loc='upper right')

while True:
    new_data = np.random.randint(0,50) 
    data = np.append(data,new_data)
    if len(data) > 100:
        data = data[-100:]

    line.set_ydata(data) 
    line.set_xdata(np.arange(len(data)))
    plt.draw()
    plt.pause (0.05)