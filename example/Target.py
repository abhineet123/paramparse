from Active import ActiveParams
from Lost import LostParams
from Tracked import TrackedParams
from Templates import TemplatesParams
from History import HistoryParams


class TargetParams:
    """
    :type tracker_type: int
    :type pause_for_debug: int
    :type verbose: int
    :type tracker: LKParams
    :type history: HistoryParams
    :type templates: TemplatesParams
    :type active: ActiveParams
    :type lost: LostParams
    :type tracked: TrackedParams
    """

    def __init__(self):

        self.history = HistoryParams()
        self.templates = TemplatesParams()
        self.active = ActiveParams()
        self.lost = LostParams()
        self.tracked = TrackedParams()

        self.pause_for_debug = 0
        self.verbose = 0

        self.help = {
            'history': 'History parameters (specified in History.py)',
            'templates': 'Templates parameters (specified in Templates.py)',
            'active': 'Active state parameters (specified in Active.py)',
            'lost': 'Lost state parameters (specified in Lost.py)',
            'tracked': 'Tracked state parameters (specified in Tracked.py)',
            'pause_for_debug': 'pause execution for debugging',
            'verbose': 'Enable printing of some general diagnostic messages',
        }

