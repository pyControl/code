from api.api import Api
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
import seaborn as sns
sns.set()
sns.set_style('white')
plt.rcParams['interactive'] == True

class Rl_mov_ave(Api):
    def __init__(self):

        self.mov_avs = []
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
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
            ax = self.figure.add_subplot(111)
            ax.clear()
            ax.set_ylim((0,1))
            if len(self.mov_avs)<4:
                ax.set_xlim((0,4))
            else:
                ax.set_xlim((0,len(self.mov_avs)))
            ax.set_xlabel('Trial Number')
            ax.set_ylabel('Moving Average of Choices')
            sns.despine()
            ax.plot(self.mov_avs, '*-')
            self.canvas.draw()
