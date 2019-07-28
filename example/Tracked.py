class TrackedParams:
    def __init__(self):
        self.threshold_box = 0.8  # bounding box overlap threshold in tracked state
        self.overlap_box = 0.5  # overlap with detection
        self.weight_tracking = 1  # weight for tracking box in tracked state
        self.weight_detection = 1  # weight for detection box in tracked state
        # minimum overlap with the frame for the object to be considered to be
        # present in the scene
        self.exit_threshold = 0.95
        self.pause_for_debug = 0
        self.help = {
            'threshold_box': 'threshold of the mean overlap of all templates with the best matching detection'
                             ' for the tracking to be considered successful; if the mean overlap is less than this, '
                             'then the object is considered to have been lost',
            'overlap_box': 'minimum overlap (IOU) between the location of the anchoring template and the best '
                           'matching detection for the final object location to be computed as a weighted average of '
                           'the two; if the overlap is less than this, then the detection itself is used as this '
                           'location;',
            'weight_tracking': 'weight given to the anchoring template tracked location while computing the '
                               'weighted average of this and the best matching detection as the final object '
                               'location',
            'weight_detection': 'weight given to the best matching detection while computing the weighted average '
                                  'of this and the anchoring template tracked location as the final object location',
            'exit_threshold': 'minimum overlap between an object location and the frame extents for the object to be '
                              'considered to be within the scene',
            'pause_for_debug': 'pause executionn for debugging'
        }

