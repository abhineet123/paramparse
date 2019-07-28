from siamfc.SiamFC import SiamFCParams
from DaSiamRPN.DaSiamRPN import DaSiamRPNParams

class SiameseParams:
    """
        :type variant: int
    """

    def __init__(self):
        self.variant = '0'

        self.stacked = 0

        self.feature_type = 0
        self.feature_from_raw_scores = 1
        self.n_features = 10

        self.visualize = 0
        self.nms_method = 1
        self.nms_dist_ratio = 0.25
        self.non_best_score_thresh = 0.75
        self.non_best_score_count = 1

        self.siam_fc = SiamFCParams()
        self.da_siam_rpn = DaSiamRPNParams()
        self.verbose = 0

        self.help = {
            'variant': '0 / fc / siam_fc: SiamFC '
                       '1 / da_rpn / da_siam_rpn: DaSiamRPN',
            'stacked': 'use stacked implementation of LK - here all patches are stacked onto a single large image',
            'feature_type': '0: scores flattened '
                            '1: maximum values in each row and column of scores concatenated '
                            '2: top <n_features> maxima values in scores (with nms for resized scores) ',
            'features_from_raw_scores': 'features_from_raw_scores',
            'n_features': 'only used if feature_type = 2',
            'nms_dist_ratio': 'fraction of the maximum dimension of the score map used as the distance threshold '
                              'while performing non-maximum suppression for feature and status extraction',
            'siam_fc': 'SiamFCParams',
            'da_siam_rpn': 'DaSiamRPNParams',
        }

