from Target import TargetParams
from Input import InputParams
from Visualizer import VisualizerParams
import Utilities as utils


class TrainerParams:
    """
    :type input: InputParams
    :type help: {str:str}
    """

    def __init__(self):
        # parameters for generating training data
        self.overlap_occ = 0.7
        self.overlap_pos = 0.5
        self.overlap_neg = 0.2

        # training parameters
        self.max_iter = 10000  # max iterations in total
        self.max_count = 10  # max iterations per sequence
        self.max_pass = 2

        # heuristics
        self.exit_threshold = 0.95

        self.verbose = 0

        self.input = InputParams()
        self.target = TargetParams()
        self.visualizer = VisualizerParams()
        self.debug = utils.DebugParams()

        self.help = {
            'overlap_occ': 'IOA threshold for deciding if an annotation is to be considered as occluded by another',
            'overlap_pos': 'IOU threshold for deciding if a detection is considered as true positive - '
                           'iou with the maximally overlapping is taken; '
                           'this is also used as one of the conditions for deciding if a given annotation '
                           'can be used as the starting one for a training trajectory - its overlap or IOI with the '
                           'maximally overlapping detection must to be greater than this threshold for it to be '
                           'considered as a valid starting point for the trajectory',
            'overlap_neg': 'IOU threshold for deciding if a detection is considered as false negative - '
                           'iou with the maximally overlapping is taken; '
                           'the detection is labeled as unknown if this iou is less than overlap_pos but grater '
                           'than overlap_neg',
            'max_iter': 'Maximum number of iterations allowed on any given sequence before training on that sequence is'
                        ' considered to be complete - an iteration is considered to have happened when one instance of'
                        'training over a particular trajectory has been completed',
            'max_count': 'Maximum number of times training can occur for any given trajectory or the maximum number of '
                         'instances of training that can take place for any given trajectory - when the number of '
                         'instances exceeds this number, that particular trajectory is considered to be too difficult'
                         ' to train on',
            'max_pass': 'Maximum number of training passes over all the trajectories in a given sequence - one pass is '
                        'considered to have been completed when one training instance has been run over '
                        'all the trajectories in that sequence ',
            'exit_threshold': 'Minimum fraction of the area of an annotation that must be inside the of the image'
                              'boundaries if that annotation can be considered as the starting point of a '
                              'training trajectory - Same as its namesake in the tracked state policy module parameters',
            'max_inactive_targets': 'maximum no. of inactive targets allowed to accumulate in the record'
                                    ' before being removed',
            'verbose': 'Enable printing of general diagnostic messages',
            'input': 'Input parameters',
            'target': 'Target parameters',
            'visualizer': 'Visualizer parameters',
            'debug': 'Debugging parameters'
        }

