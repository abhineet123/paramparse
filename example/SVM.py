class SVMParams:
    def __init__(self):
        # SVM implementation to use: 0: high level libsvm 1: low level libsvm 2:sklearn.svm 3: lasvm
        self.implementation = 0
        self.verbose = 1

        self.help = {
            'implementation': 'SVM implementation to use:'
                              ' 0: libsvm (high level) 1: libsvm (low level) 2: sklearn.svm 3: lasvm',
            'verbose': 'Show detailed diagnostic messages, if any, from the underlying library'
        }

