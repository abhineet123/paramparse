class ObjectsParams:
    def __init__(self):
        self.path = ''
        self.fix_frame_ids = 1
        self.sort_by_frame_ids = 1
        self.help = {
            'path': 'path of the text file in MOT format from where the objects data is to be read;'
                             'if this is empty, then a default path is constructed from the sequence and dataset names',
            'fix_frame_ids': 'convert the frame IDs in the annotations and detections from 1-based '
                             '(default MOT challenge format) to 0-based that is needed for internal'
                             ' processing convenience',
            'sort_by_frame_ids': 'sort data by frame IDs'

        }


class DetectionsParams(ObjectsParams):
    def __init__(self):
        ObjectsParams.__init__(self)


class AnnotationsParams(ObjectsParams):
    def __init__(self):
        ObjectsParams.__init__(self)