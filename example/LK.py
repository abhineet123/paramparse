class LKParams:
    def __init__(self):
        self.margin_box = (5, 2)  # [width height] of the margin in computing flow
        self.grid_res = 10

        self.max_iters = 20
        self.eps = 0.03
        self.level_track = 1
        self.lk_win_size = 4
        self.ncc_win_size = 10

        self.fb_thresh = 10
        self.fb_norm_factor = 30

        self.cv_wrapper = 0
        self.stacked = 0
        self.gpu = 0
        self.show_points = 0
        self.verbose = 0

        self.help = {
            'margin_box': '[width height] in pixels of the border around the object bounding box within which '
                          'optical flow is also computed',
            'grid_res': 'resolution of the grid of points where LK optical flow is computed; '
                        'e.g. a resolution of 10 means that the object patch is sampled by a 10x10 grid of'
                        ' equally spaced points where the optical flow is computed',
            'max_iters': 'maximum no. of iterations of the optical flow process per frame',
            'eps': 'threshold of change in LK estimate that is used for terminating the iterative process',
            'level_track': 'no. of pyramidal levels to use',
            'lk_win_size': 'size of the neighborhood around each point whose pixel values are used for '
                           'computing the optical flow estimate',
            'ncc_win_size': 'size of sub patches around each point whose similarities (NCC) are computed',
            'fb_thresh': 'forward-backward error threshold',
            'fb_norm_factor': 'normalization factor for computing features from optical flow forward-backward error',
            'cv_wrapper': 'use the OpenCV python wrapper for LK and NCC computation instead '
                          'of the custom implementation; this is usually slower than the custom version',
            'stacked': 'use stacked implementation of LK - here all patches are stacked onto a single large image '
                       'and pairwise LK is computed in a single call to the OpenCV LK function; this is usually faster'
                       ' especially when there are many objects / detections in the scene',
            'gpu': 'use GPU implementation of LK; this is only supported if a modern GPU with CUDA support '
                   'is available and OpenCV is compiled with CUDA support; ',
            'show_points': 'show the optical flow points for each tracked patch',
            'verbose': 'print detailed information'
        }

