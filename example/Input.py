import platform
from Objects import  AnnotationsParams, DetectionsParams


class InputParams:
    def __init__(self):
        self.path = ''
        self.frame_ids = (-1, -1)

        if platform.system() == 'Windows':
            self.db_root_path = 'E:/Datasets'
        else:
            self.db_root_path = '/data'
        self.source_type = 0
        self.img_fmt = ('image%06d', 'jpg')
        self.vid_fmt = 'mp4'

        self.resize_factor = 1
        self.convert_to_gs = 1
        self.read_from_bin = 0
        self.write_to_bin = 0
        self.batch_mode = 1
        self.roi = (0,0,0,0)

        self.annotations = AnnotationsParams()
        self.tracking_res = AnnotationsParams()
        self.detections = DetectionsParams()

        self.help = {
            'path': 'path of the directory, video file or binary file from where images are to be read;'
                    ' if this is not specified then it is computed from db_root_path, '
                    'sequence set/name (in Params.py), source_type and img_fmt/vid_fmt',
            'frame_ids': 'two element tuple specifying the IDs of the first and last frames in the sub sequence; '
                         'if either is less than 0, it is computed from ratios and offsets',
            'db_root_path': 'path of the directory that contains all datasets',
            'source_type': '0: image sequence 1: video file',
            'img_name_template': 'naming format for image sequence',
            'img_fmt': '(naming scheme, extension) of each image file in the sequence',
            'vid_fmt': 'file extension of the video file',
            'resize_factor': 'multiplicative factor by which to resize the input images',
            'convert_to_gs': 'convert all input images to greyscale (if they are RGB) before they are used',
            'read_from_bin': 'write all image data to a binary file for quick and lossless reading',
            'write_to_bin': 'write all image data to a binary file for quick and lossless reading',
            'batch_mode': 'read all frames in the input sequence at once to avoid repeated disk accesses',
            'roi': 'four element tuple specifying the region of interest (ROI) as (xmin, ymin, xmax, ymax) of '
                   'the corresponding bounding box; ROI is only enabled if xmx > xmin and ymax > ymin',
            'annotations': 'parameters for Annotations in Objects module',
            'tracking_res': 'parameters for tracking results (same as Annotations in Objects module)',
            'detections': 'parameters for Detections in Objects module'
        }

