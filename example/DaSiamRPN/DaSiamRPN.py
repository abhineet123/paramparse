class DaSiamRPNParams:
    """

    :param int model: 0: SiamRPNvot 1: SiamRPNBIG 2: SiamRPNotb,
    :param str windowing: to penalize large displacements [cosine/uniform]
    :param int exemplar_size: input z size
    :param int instance_size: input x size (search region)
    :param float context_amount: context amount for the exemplar
    :param bool adaptive: adaptive change search region
    :param int score_size: size of score map
    :param int anchor_num: number of anchors
    """

    def __init__(self):
        self.windowing = 'cosine'
        self.exemplar_size = 127
        self.instance_size = 271
        self.total_stride = 8
        self.context_amount = 0.5
        self.ratios = (0.33, 0.5, 1, 2, 3)
        self.scales = (8,)

        self.penalty_k = 0.055
        self.window_influence = 0.42
        self.lr = 0.295
        self.adaptive = 0
        self.visualize = 0

        self.anchor_num = len(self.ratios) * len(self.scales)
        self.score_size = int((self.instance_size - self.exemplar_size) / self.total_stride + 1)

        self.model = 0
        self.update_location = 0
        self.pretrained_wts_dir = 'DaSiamRPN/pretrained_weights'

        self.help = {
        }

