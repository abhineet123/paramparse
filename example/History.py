class HistoryParams:
    def __init__(self):
        # no. of frames in the target history to use for predicting its motion
        self.prediction_n_frames = 10
        self.predict_size = 0
        self.max_interp_frame_diff = 5
        self.pause_for_debug = 0
        self.help = {
            'prediction_n_frames': 'Maximum number of frames from the history to consider for computing the '
                                   'predicted location',
            'predict_size': 'Enable predicting the size of the object too-if this is disabled, then the size'
                            'is taken from the last entry in the history',
            'max_interp_frame_diff': 'Maximum difference between the frame ID in the last entry in the history and '
                                     'that of the current frame for interpolation to be used to fill in the gap '
                                     'between them - if the frame difference is greater than this, then '
                                     'interpolation is not used',
            'pause_for_debug': 'pause execution for debugging',
        }

