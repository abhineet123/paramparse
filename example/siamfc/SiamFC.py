class DesignParams:
    def __init__(self):
        self.join_method = "xcorr"
        self.net = "baseline-conv5_e55.mat"

        self.net_gray = ''
        self.windowing = 'cosine_sum'

        self.exemplar_sz = 127
        self.search_sz = 255
        self.score_sz = 33
        self.tot_stride = 4

        self.context = 0.5
        self.pad_with_image_mean = 1

        self.help = {
        }


class EnvironmentParams:
    def __init__(self):
        # self.root_dataset = "data"
        self.root_pretrained = "siamfc/pretrained"

        self.root_parameters = 'parameters'
        self.help = {
        }


class HyperParams:
    def __init__(self):
        self.response_up = 8
        self.window_influence = 0.25
        self.z_lr = 0.01
        self.scale_num = 3

        self.scale_step = 1.04
        self.scale_penalty = 0.97
        self.scale_lr = 0.59
        self.scale_min = 0.2
        self.scale_max = 5
        self.help = {
        }


class SiamFCParams:
    def __init__(self):
        self.update_location = 0

        self.allow_gpu_memory_growth = 1
        self.per_process_gpu_memory_fraction = 1.0

        self.gpu = -1
        self.visualize = 0

        self.design = DesignParams()
        self.env = EnvironmentParams()
        self.hp = HyperParams()

        self.help = {
            'design': 'DesignParams',
            'env': 'EnvironmentParams',
            'hp': 'HyperParams',
        }

