class TrainParams:
    """
    :type seq_set_id: int
    :type seq_ids: (int, )
    :type resume: int
    :type load: int
    """

    def __init__(self):
        self.seq_set_id = 7
        self.seq_ids = (5,)
        self.load = 1
        self.resume = 0
        self.save = 1
        self.load_prefix = 'trained'
        self.save_prefix = 'trained'
        self.results_dir = 'log'

        self.help = {
            'seq_set_id': 'Numeric ID of the data set from which the training sequences '
                          'have to be taken as defined in the Data module; '
                          'at present only sequences from a single data set can be trained on '
                          'in a single run',
            'seq_ids': 'Numeric IDs of the sequences on which training has to be performed '
                       'as defined in the Data module',
            'load': 'Load a previously trained tracker on the given sequences from the disk; '
                    'if disabled, training on the given sequences will be performed from scratch',
            'resume': 'resume training a previously trained target using additional sequences; '
                      'a value greater than 0 also specifies the ID of the sequence from which the '
                      'training is to be continued after loading the target corresponding '
                      'to the sequence preceding it; this ID is specified relative to '
                      'the sequence IDs provided in seq_ids',
            'save': 'Save the trained tracker to disk so it can be loaded later; '
                    'only matters if load is disabled',
            'save_prefix': 'Prefix in the name of the file into which the trained tracker is to be saved',
            'load_prefix': 'prefix in the name of the file from which the previously trained tracker '
                           'has to be loaded for testing',
            'results_dir': 'Directory where training results files are written to',
        }


class TestParams:
    """
    :type seq_set_id: int
    :type seq_ids: (int, )
    :type load: int
    """

    def __init__(self, train=None):

        self.seq_set_id = -1
        self.seq_ids = ()
        self.load = 0
        self.save = 1
        self.load_prefix = ''
        self.save_prefix = ''
        self.results_dir = ''

        self.evaluate = 1
        self.eval_dist_type = 0
        self.eval_file = 'mot_metrics.txt'


        self.help = {
            'seq_set_id': 'Numeric ID of the data set from which the testing sequences '
                          'have to be taken as defined in the Data module; '
                          'at present only one data set can be tested on in a single run',
            'seq_ids': 'Numeric IDs of the sequences on which testing or visualization has to be performed'
                            ' as defined in the Data module',
            'load': 'Load previously saved tracking results from file for evaluation or visualization'
                    ' instead of running the tracker to generate new results',
            'save': 'Save tracking results to file;'
                    'only matters if load is disabled',
            'save_prefix': 'Prefix in the name of the file into which the trained tracker is to be saved',
            'load_prefix': 'prefix in the name of the file from which the previously trained tracker '
                           'has to be loaded for testing',
            'results_dir': 'Directory where the tracking results file is saved in',
            'evaluate': 'Enable evaluation of the tracking result; '
                        'only works if the ground truth for the tested sequence is available',
            'eval_dist_type': 'Type of distance measure between tracking result and ground truth '
                              'bounding boxes to use for evaluation:'
                              '0: intersection over union (IoU) distance'
                              '1: squared Euclidean distance; '
                              'only matters if evaluate is set to 1',
            'eval_file': 'Name of the file into which a summary of the evaluation result will be written'
                         ' if evaluation is enabled',
        }

    def synchronize(self, train):
        """
        :type train: TrainParams
        """
        if self.seq_set_id < 0:
            self.seq_set_id = train.seq_set_id
        if not self.seq_ids:
            self.seq_ids = train.seq_ids
        if not self.results_dir:
            self.results_dir = train.results_dir
        if not self.load_prefix:
            self.load_prefix = train.load_prefix
        if not self.save_prefix:
            self.save_prefix = train.save_prefix


class DataParams:
    """
    :type ratios: (float, float) | None
    :type offsets: (int, int) | None
    """

    def __init__(self):
        self.ratios = (1, 1)
        self.offsets = (0, 0)

        self.ratios_gram = (1, 0)
        self.ratios_idot = (1, 0)
        self.ratios_detrac = (1, 0)
        self.ratios_lost = (1, 0)
        self.ratios_isl = (1, 1)
        self.ratios_mot2015 = (1, 0)
        self.ratios_kitti = (1, 0)

        self.help = {
            'ratios': 'two element tuple to indicate fraction of frames in each sequence on which'
                      ' (training, testing) is to be performed; '
                      'negative values mean that frames are taken from the end of the sequence; '
                      'zero for the second entry means that all frames not used for training are used for '
                      'testing in each sequence; '
                      'if either entry is > 1, it is set to the corresponding value for the sequence set being used',
            'offsets': 'two element tuple to indicate offsets in the start frame ID with respect to the sub sequence'
                       ' obtained from the (train, test) ratios on which (training, testing) is to be performed;'
                       'ratios and offsets together specify the subsequences, if any, on which the two components'
                       ' of the program are to be run',
            'ratios_gram': 'train and test ratios for sequences in the GRAM dataset',
            'ratios_idot': 'train and test ratios for sequences in the IDOT dataset',
            'ratios_detrac': 'train and test ratios for sequences in the DETRAC dataset',
            'ratios_lost': 'train and test ratios for sequences in the LOST dataset',
            'ratios_isl': 'train and test ratios for sequences in the ISL dataset',
            'ratios_mot2015': 'train and test ratios for sequences in the MOT2015 dataset',
            'ratios_kitti': 'train and test ratios for sequences in the KITTI dataset',
        }
