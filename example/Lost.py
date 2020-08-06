from SVM import SVM.Params
from XGB import XGB.Params
from MLP import MLPParams


class LostParams:
    def __init__(self):
        self.model_type = 'svm'
        self.max_occlusion = 50

        self.threshold_ratio = 0.6
        self.threshold_dist = 3

        self.overlap_box = 0.5
        self.overlap_pos = 0.5
        self.overlap_neg = 0.2

        self.use_heuristic_features = 1

        self.pause_for_debug = 0

        self.verbose = 0

        self.weight_tracking = 1
        self.weight_association = 1

        self.copy_while_learning = 1

        self.svm = SVM.Params()
        self.xgb = XGB.Params()
        self.mlp = MLPParams()

        self.help = {
            'model_type': 'learning method used for decision making in the lost state: '
                          'svm: Support Vector Machine,'
                          'xgb: XGBoost,'
                          'mlp: Multi Layer Perceptron,'
                          'cnn: Convolutional Neural Network',
            'max_occlusion': 'maximum number of consecutive frames for which the target is allowed to remain in '
                             'the Lost state before it transitions to inactive',
            'threshold_ratio': 'aspect ratio threshold in target association - this is the minimum ratio between the'
                               ' heights of the last known location and a candidate detection for the latter to be '
                               'considered a possible match',
            'threshold_dist': ' distance threshold in target association, multiple of the width of target - '
                              'this is the maximum ratio of the Euclidean distance between the centers of the last '
                              'known target location and a candidate detection with the width of the former '
                              'for the latter to be considered a possible match',
            'overlap_box': 'minimum overlap (IOU) between the LK result and the best matching detection for the final'
                           ' object location to be computed as a weighted average of the two; if the overlap is'
                           ' less than this, then the detection itself is used as this location;',
            'overlap_pos': 'minimum overlap (IOU) of the ground truth location with the best matching detection and '
                           'the computed object location for the corresponding feature vector to be regarded '
                           'as a positive training sample for learning',
            'overlap_neg': 'maximum overlap (IOU) of the ground truth location with the best matching detection or '
                           'the computed object location for the corresponding feature vector to be regarded '
                           'as a negative training sample for learning',
            'use_heuristic_features': 'augment tracker/templates features with heuristics to '
                                      'construct policy classifier features; '
                                      'setting to 0 will use only tracker features',
            'copy_while_learning': 'original code did not update templates state matrices while getting '
                                   'learning features for some unknown annoying reason; toggle this behavior',
            'pause_for_debug': 'pause execution for debugging',
            'verbose': 'Enable printing of some general diagnostic messages',
            'weight_tracking': 'weight given to the tracked location while computing the weighted average '
                               'of this and the best matching detection as the final object location during association',
            'weight_association': 'weight given to the best matching detection while computing the weighted average '
                                  'of this and the tracked location as the final object location during association',
            'svm': 'parameters for the SVM module',
            'xgb': 'parameters for the XGB module',
            'mlp': 'parameters for the MLP module'
        }

