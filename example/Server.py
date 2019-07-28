from Data import TrainParams, TestParams
from Trainer import TrainerParams
from Tester import  TesterParams
from Visualizer import VisualizerParams
from PatchTracker import PatchTrackerParams
from Gate import GateParams

class ServerParams:
    """
    :type mode: int
    :type load_path: str
    :type continue_training: int | bool
    :type gate: GateParams
    :type patch_tracker: PatchTrackerParams
    :type visualizer: VisualizerParams
    """

    def __init__(self):
        self.mode = 0
        self.load_path = 'trained_target.zip'
        self.save_path = ''

        self.port = 3002
        self.skip_thresh = 10
        self.verbose = 0

        self.train = TrainParams()
        self.test = TestParams()

        self.gate = GateParams()
        self.patch_tracker = PatchTrackerParams()
        self.visualizer = VisualizerParams()

        self.help = {
            'mode': 'server mode: '
                    '0: disable '
                    '1: testing '
                    '2: training',
            'load_path': 'location of the zip file from where the pre-trained target is to be loaded',
            'save_path': 'location of the zip file from where the trained target is to be saved',
            'continue_training': 'continue training a previously trained target loaded from trained_target_path',
            'port': 'port on which the server listens for requests',
            'skip_thresh': 'maximum number of attempts to look for the detections for a particular frame '
                           'before skipping to the next one',
            'verbose': 'show detailed diagnostic messages',
            'gate': 'parameters for the Gate module',
            'patch_tracker': 'parameters for the patch tracker module',
        }

