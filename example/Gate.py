class GateParams:
    """
    :type intersection_method: int
    :type intersection_thresh: float
    """

    def __init__(self):
        self.intersection_method = 2
        self.intersection_thresh = 0.1
        self.help = {
            'intersection_method': 'method used for computing gate-target intersection: '
                                   '0: box center lies on gate '
                                   '1: gate intersects box'
                                   '2: gate intersects target trajectory',
            'intersection_thresh': 'threshold for box center intersection with gate',
        }

