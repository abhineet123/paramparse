class MLPParams:
    def __init__(self):
        self.n_layers = 2
        self.activation_type = 'relu'
        self.hidden_sizes = (24,)
        self.train_epochs = 10
        self.loss_type = 0
        self.verbose = 1

        self.help = {
            'verbose': 'Show detailed diagnostic messages, if any, from the underlying library'
        }
