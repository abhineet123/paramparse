class PatchTrackerParams:
    """
    :type use_mtf: int | bool
    :type mtf_cfg_dir: str
    :type tracker_type: int
    :type show: int | bool
    :type save: int | bool
    :type box_color: str
    :type text_fmt: tuple(str, int, float, int, int)
    :type save_fmt: tuple(str, str, int)
    """

    def __init__(self):
        self.use_mtf = 1
        self.mtf_cfg_dir = 'mtf'
        self.tracker_type = 0

        self.show = 1
        self.convert_to_rgb = 0
        self.thickness = 2
        self.box_color = 'red'
        self.resize_factor = 1.0
        self.show_text = 1
        self.text_fmt = ('green', 0, 5, 1.0, 1)
        self.save = 0
        self.save_fmt = ('avi', 'XVID', 30)
        self.save_dir = 'videos'

        self.help = {
            'use_mtf': 'use MTF patch tracker',
            'mtf_cfg_dir': 'directory containing the cfg files for MTF',
            'tracker_type': 'tracker type to use if use_mtf is disabled',
            'show': 'show the tracked object location drawn on the input image',
            'convert_to_rgb': 'convert the image to RGB before showing it; this is sometimes needed if the raw frame is'
                              ' in BGR format so that it does not show correctly (blue and red channels are '
                              'interchanged)',
            'thickness': 'thickness of the bounding box lines drawn on the image',
            'box_color': 'color of the bounding box used to represent the tracked object location',
            'resize_factor': 'multiplicative factor by which the images are resized before being shown or saved',
            'show_text': 'write text in the top left corner of the image to indicate the frame number and FPS',
            'text_fmt': '(color, location, font, font_size, thickness) of the text used to '
                        'indicate the frame number and FPS; '
                        'Available fonts: '
                        '0: cv2.FONT_HERSHEY_SIMPLEX, '
                        '1: cv2.FONT_HERSHEY_PLAIN, '
                        '2: cv2.FONT_HERSHEY_DUPLEX, '
                        '3: cv2.FONT_HERSHEY_COMPLEX, '
                        '4: cv2.FONT_HERSHEY_TRIPLEX, '
                        '5: cv2.FONT_HERSHEY_COMPLEX_SMALL, '
                        '6: cv2.FONT_HERSHEY_SCRIPT_SIMPLEX ,'
                        '7: cv2.FONT_HERSHEY_SCRIPT_COMPLEX; '
                        'Locations: 0: top left, 1: top right, 2: bottom right, 3: bottom left',
            'save': 'save the visualization result with tracked object location drawn on the'
                    ' input image as a video file',
            'save_fmt': '(extension, encoder, FPS) of the saved video',
            'save_dir': 'directory where to save the video',
        }
