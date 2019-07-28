import paramparse

from Data import DataParams, TrainParams, TestParams
from Trainer import TrainerParams
from Tester import TesterParams
from Server import ServerParams

class Params:
    """
    :type cfg: str
    :type data: DataParams
    :type tester: TesterParams
    :type trainer: TrainerParams
    :type server: ServerParams
    :type help: {str:str}
    """

    def __init__(self):
        self.train = TrainParams()
        self.test = TestParams(self.train)

        self.cfg = 'cfg/params.cfg'
        self.log_dir = ''

        self.data = DataParams()
        self.tester = TesterParams()
        self.trainer = TrainerParams()
        self.server = ServerParams()

        self.help = {
            'train': 'training settings',
            'test': 'testing settings',
            'cfg': 'optional ASCII text file from where parameter values can be read;'
                   'command line parameter values will override the values in this file',
            'log_dir': 'directory where log files are created; '
                       'leaving it empty disables logging to file',
            'data': 'parameters for Data module',
            'tester': 'Tester parameters',
            'trainer': 'Trainer parameters',
            'server': 'Server mode parameters for integration with the interactive interface',
        }

    def processArguments(self):
        paramparse.process(self)
