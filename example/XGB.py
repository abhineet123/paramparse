class XGBParams:
    def __init__(self):
        self.max_depth = 2
        self.eta = 1
        self.objective = 'binary:logistic'
        self.nthread = 4
        self.eval_metric = 'auc'
        self.num_round = 10
        self.verbose = 1

        self.help = {
        }

