class DebugParams:
    """
    :type write_state_info: bool | int
    :type write_to_bin: bool | int
    :type write_thresh: (int, int)
    :type cmp_root_dirs: (str, str)
    """

    def __init__(self):
        self.write_state_info = 0
        self.write_thresh = (0, 0)
        self.write_to_bin = 1
        self.memory_tracking = 0
        self.cmp_root_dirs = ('../../isl_labelling_tool/tracking_module/log', 'log')
        self.help = {
            'write_state_info': 'write matrices containing the target state information to files '
                                'on disk (for debugging purposes)',
            'write_thresh': 'two element tuple to indicate the minimum (iter_id, frame_id) after which '
                            'to start writing and comparing state info',
            'write_to_bin': 'write the matrices to binary files instead of human readable ASCII text files',
            'memory_tracking': 'track memory usage to find leaks',
            'cmp_root_dirs': 'root directories where the data files to be compared are written',
        }

