from LK import LKParams
from Siamese import SiameseParams

class TemplatesParams:
    """
    :param int tracker: 0 / lk: LK, 1 / siam / siamese: Siamese
    :param tuple(int) std_box_size: [width height] of the standard box that all templates are resized into
    :param tuple(int) enlarge_box_size: factors by which to enlarge the box to obtain the ROI around it for context
    :param int count: number of templates

    :param tuple(tuple) init_shift: ratio of shifts in the initial target location to generate additional
    templates during initialization

    :param int roi_interp_type_id:  interpolation type used while resizing images before extracting the
     ROI within which tracking is performed
     0: nearest neighbor
     1: bilinear interpolation

    :param int sub_pix_method: method used for extracting patch with subpixel interpolation:
     0: pyWarp
     1: OpenCV
    :param int pattern_interp_type_id: indexes into Utilities.CVConstants.interp_types
    :param int similarity_type_id: indexes into Utilities.CVConstants.similarity_types

    :param tuple(int) pattern_shape: patch shape for template appearance - (n_rows, n_cols)
    :param float max_ratio: min allowed height ratio
    :param float min_velocity_norm: min allowed velocity norm in LK

    :param int max_velocity_frames: max frames used to compute mean velocity
    """

    def __init__(self):
        self.tracker = 'lk'

        self.std_box_size = (60, 45)  #
        self.enlarge_box_size = (5, 3)  #

        self.count = 10

        # self.max_detections = 10  # max number of detections per frame

        self.init_shift = (
            (-0.01, -0.01),
            (-0.01, 0.01),
            (0.01, -0.01),
            (0.01, 0.01)
        )
        self.max_ratio = 0.9
        self.min_velocity_norm = 0.2
        self.max_velocity_frames = 3
        self.pattern_shape = (24, 12)

        self.roi_interp_type_id = 1

        self.sub_pix_method = 1

        self.pattern_interp_type_id = 1

        self.similarity_type_id = -1
        self.pause_for_debug = 0
        self.visualize = 0

        self.lk = LKParams()
        self.siamese = SiameseParams()

        self.help = {
            'tracker': 'Type of tracker to use - '
                            '0 / lk: LK '
                            '1 / siam / siamese: Siamese',
            'std_box_size': 'size of the standard box that all templates are resized into - (width height)',
            'enlarge_box_size': 'factors by which to enlarge the box to obtain the ROI around it - (width height)',
            'count': 'number of templates',
            'init_shift': 'proportional shifts used to generate initial template locations'
                          ' about the main target location',
            'max_ratio': 'min allowed height ratio',
            'min_velocity_norm': 'min allowed velocity norm in LK',
            'max_velocity_frames': 'max frames used to compute mean velocity',
            'pattern_shape': 'Patch shape for template appearance model - (n_rows, n_cols)',
            'roi_interp_type_id': 'ID of the interpolation type used while resizing images before extracting the '
                                  'ROI within which tracking is performed - indexes into '
                                  'Utilities.utils.CVConstants.interp_types',
            'pattern_interp_type_id': 'ID of the interpolation type used while resizing images before extracting the '
                                      'patches that represent the template appearance - indexes into '
                                      'Utilities.utils.CVConstants.interp_types',
            'similarity_type_id': 'ID of the similarity type used to obtain similarity feature from template patches - '
                                  'indexes into Utilities.utils.CVConstants.similarity_types',
            'visualize': 'visualize results',
            'lk': 'LKParams',
            'siamese': 'SiameseParams',
            'pause_for_debug': 'pause execution for debugging'

        }

