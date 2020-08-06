from SVM import SVM
from XGB import XGB
from MLP import MLP

class ActiveParams:
    """
    :type model_type: str
    :type svm: SVM.Params
    :type xgb: XGB.Params
    :type mlp: MLPParams
    """
    def __init__(self):
        self.model_type = 'svm'
        self.svm = SVM.Params()
        self.xgb = XGB.Params()
        self.mlp = MLP.Params()

        self.help = {
            'model_type': 'learning method used for decision making in the active state: '
                          'svm: Support Vector Machine,'
                          'xgb: XGBoost,'
                          'mlp: Multi Layer Perceptron,'
                          'cnn: Convolutional Neural Network',
            'svm': 'parameters for the SVM module',
            'xgb': 'parameters for the XGB module',
            'mlp': 'parameters for the MLP module',
        }

