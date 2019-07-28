from SVM import SVMParams
from XGB import XGBParams
from MLP import MLPParams

class ActiveParams:
    """
    :type model_type: str
    :type svm: SVMParams
    :type xgb: XGBParams
    :type mlp: MLPParams
    """
    def __init__(self):
        self.model_type = 'svm'
        self.svm = SVMParams()
        self.xgb = XGBParams()
        self.mlp = MLPParams()

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

