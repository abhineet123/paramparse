class VisualizerParams:
    """
    :type mode: (int, int, int)
    :type tracked_cols: tuple(str,)
    :type lost_cols: tuple(str,)
    :type inactive_cols: tuple(str,)
    :type det_cols: tuple(str,)
    :type ann_cols: tuple(str,)
    :type text_fmt: tuple(str, int, float, int, int)
    :type gate_fmt: tuple(str, float, float, int, int)
    :type pause_after_frame: bool
    :type help: {str:str}
    """

    def __init__(self):
        """
        :rtype: None
        """
        self.mode = (0, 0, 0)
        self.tracked_cols = ('green',)
        self.lost_cols = ('red',)
        self.inactive_cols = ('cyan',)
        self.det_cols = ('black',)
        self.ann_cols = ('blue',)

        self.convert_to_rgb = 0
        self.pause_after_frame = 1

        self.show_trajectory = 1
        self.box_thickness = 2
        self.traj_thickness = 2
        self.resize_factor = 1.0
        self.text_fmt = ('green', 0, 5, 1.0, 1)
        self.gate_fmt = ('black', 2.0, 5, 1.0, 1)

        self.show = 1
        self.save = 0
        self.save_fmt = ('avi', 'XVID', 30)
        self.save_dir = 'log'
        self.save_prefix = ''

        self.help = {
            'mode': 'three element tuple to specify which kinds of objects are to be shown:'
                    '(tracked, detections, annotations)',
            'tracked_cols': 'bounding box colors in which to show the tracking result for objects in tracked state; '
                            'if there are more objects than the number of specified colors, modulo indexing is used',
            'lost_cols': 'bounding box colors in which to show the tracking result for objects in lost state',
            'inactive_cols': 'bounding box colors in which to show the tracking result for objects in inactive state',
            'det_cols': 'bounding box colors in which to show the detections',
            'ann_cols': 'bounding box colors in which to show the annotations',
            'convert_to_rgb': 'convert the image to RGB before showing it; this is sometimes needed if the raw frame is'
                              ' in BGR format so that it does not show correctly (blue and red channels are '
                              'interchanged)',
            'pause_after_frame': 'pause execution after each frame till a key is pressed to continue;'
                                 'Esc: exit the program'
                                 'Spacebar: toggle this parameter',
            'show_trajectory': 'show the trajectory of bounding boxes with associated unique IDs by drawing lines '
                               'connecting their centers across consecutive frames',
            'box_thickness': 'thickness of lines used to draw the bounding boxes',
            'traj_thickness': 'thickness of lines used to draw the trajectories',
            'resize_factor': 'multiplicative factor by which the images are resized before being shown or saved',
            'text_fmt': '(color, location, font, font_size, font_thickness) of the text used to '
                        'indicate the frame number; '
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
            'gate_fmt': '(color, thickness, font, font_size, font_thickness) of the lines and labels used '
                        'for showing the gates',
            'show': 'Show the images with drawn objects; this can be disabled when running in batch mode'
                    ' or on a system without GUI; the output can instead be saved as a video file',
            'save': 'Save the images with drawn objects as video files',
            'save_prefix': 'Prefix to be added to the name of the saved video files',
            'save_dir': 'Directory in which to save the video files',
            'save_fmt': '3 element tuple to specify the (extension, FOURCC format string, fps) of the saved video file;'
                        'refer http://www.fourcc.org/codecs.php for a list of valid FOURCC strings; '
                        'extension can be one of [jpg, bmp, png] to write to an image sequence instead of a video file',
        }
