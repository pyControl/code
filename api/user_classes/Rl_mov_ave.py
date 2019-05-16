from api.api import Api
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
import seaborn as sns
sns.set()
sns.set_style('white')

class Rl_mov_ave(Api):
    def __init__(self):
        '''class to demonstrate matplotlib plotting using the api'''
        #list of moving averages on every trial
        self.mov_avs = []
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        self.plot_data(self.mov_avs)
        self.canvas.show()

    def run_start(self, recording):
        self.print_to_log('Using api to plot reversal learning moving average of choices')

    def set_state_machine(self, sm_info):
        assert 'mov_ave' in sm_info['variables']

    def process_data(self, new_data):

        _pycontrol_print = [nd for nd in new_data if nd[0] == 'P']

        if _pycontrol_print:
            _pycontrol_print = _pycontrol_print[0][2]
        else:
            return

        if 'T#:' in _pycontrol_print:
            mov_ave = _pycontrol_print.split(':')[-1]
            self.mov_avs.append(float(mov_ave))
            self.plot_data(self.mov_avs)

    def plot_data(self, data, start_xaxis_len=5):
        '''updates the live plot of the data vector.
           Initial xaxis length = start_xaxis_len but axis
           is extended once len(data) exceeds this'''

        ax = self.figure.add_subplot(111)
        ax.clear()

        ax.set_ylim((0,1))
        if len(data)<=start_xaxis_len:
            ax.set_xlim((0,start_xaxis_len))
        else:
            ax.set_xlim((0,len(data)-0.3))

        ax.set_xlabel('Trial Number')
        ax.set_ylabel('Moving Average of Choices')
        sns.despine()
        ax.plot(data, '*-')
        self.canvas.draw()
