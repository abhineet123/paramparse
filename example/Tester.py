from Target import TargetParams
from Input import InputParams
from Visualizer import VisualizerParams
from History import HistoryParams

import Utilities as utils


class TesterParams:
    def __init__(self):
        self.overlap_sup = 0.7  # suppress target used in testing only
        self.overlap_suppress1 = 0.5  # overlap for suppressing detections with tracked objects
        self.overlap_suppress2 = 0.5  # overlap for suppressing detections with tracked objects
        self.enable_nms = 0  # enable non-maximum suppression of detections
        self.nms_overlap_thresh = (0.6, 0.95, 0.95)  # iou, ioa_1 and ioa_2 thresholds for
        # performing non-maximum suppression
        self.target_sort_sep = 10  # tracked streak size to use to separate the two sets of targets while sorting them
        # overlap thresholds for deciding which detections to filter out
        self.filter_iou_thresh = 0.5
        self.filter_ioa_thresh = 0.5
        # allow for some annoying ad-hoc heuristics in the original code where transitions to inactive state
        # happen outside of the policies
        self.check_out_of_scene = 1
        self.check_next_frame = 1
        # maximum no. of inactive targets allowed to accumulate in the record before being removed
        self.max_inactive_targets = 0
        self.min_trajectory_len = 5
        # allow for annoying ad-hoc heuristics
        self.next_frame_exit_threshold = 0.05
        self.hungarian = 0

        self.override_target_params = 0

        self.visualize = 0
        self.verbose = 0

        self.input = InputParams()
        self.target = TargetParams()
        self.visualizer = VisualizerParams()
        self.debug = utils.DebugParams()

        self.help = {
            'overlap_sup': 'IOA threshold used to decide if two targets  are in the same image region and if'
                           'one of them therefore needs to be suppressed',
            'overlap_suppress1': 'IOA threshold for non-maximum suppression or future extension',
            'overlap_suppress2': 'IOA threshold for non-maximum suppression or future extension',
            'read_all_frames': 'read all frames in the input sequence at once to avoid repeated disk accesses',
            'enable_nms': 'enable non-maximum suppression of detections',
            'nms_overlap_thresh': 'three element tuple of floats that specifies the iou, ioa_1 and ioa_2 thresholds'
                                  'for performing non-maximum suppression; only matters if enable_nms is 1 ',
            'target_sort_sep': 'tracked streak size to use to separate the two sets of targets while sorting them',
            'max_inactive_targets': 'maximum no. of inactive targets allowed to accumulate in the record'
                                    ' before being removed',
            'filter_iou_thresh': 'IOU threshold between detection and target location for deciding which detections'
                                 ' to filter out',
            'filter_ioa_thresh': 'IOU threshold between detection and target location for deciding which detections'
                                 ' to filter out',
            'check_out_of_scene': 'check if target has gone out of scene after lost state decision making - this is '
                                  'performed irrespective of whether it transitions to the tracked state and is one'
                                  ' of the annoying ad-hoc heuristics used in the original code',
            'check_next_frame': 'check if the predicted location of the target in the next frame is out of scene after'
                                ' lost state decision making - this is only performed if  the target remains in the '
                                'lost state and is one of the annoying ad-hoc heuristics used in the original code',
            'min_trajectory_len': 'Minimum number of frames for which a particular target must be in the tracked '
                                  'state for it to be considered a valid trajectory and be written to the final results',
            'next_frame_exit_threshold': 'minimum fraction of the predicted location of the object in the next frame '
                                         'that must lie inside the frame for it not to be removed',
            'hungarian': 'Use the Hungarian algorithm for performing association between lost targets and detections',
            'override_target_params': 'Override parameters in the trained target with those specified here; '
                                      'the learned model in the target might depend on several of these parameters '
                                      'and might not function well or otherwise behave in an unpredictable manner'
                                      ' if these are changed;',
            'visualize': 'Enable visualization of tracking results',
            'verbose': 'Enable printing of general diagnostic messages',
            'input': 'Input parameters',
            'target': 'Target parameters; only used if override_target_params is enabled1',
            'visualizer': 'Visualizer parameters',
            'debug': 'Debugging parameters'
        }

