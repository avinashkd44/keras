"""Built-in regularizers.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import six
from . import backend as K
from .utils.generic_utils import serialize_keras_object
from .utils.generic_utils import deserialize_keras_object


class Regularizer(object):
    """Regularizer base class.
    """

    def __call__(self, x):
        return 0.

    @classmethod
    def from_config(cls, config):
        return cls(**config)


class L1L2(Regularizer):
    """Regularizer for L1 and L2 regularization.

    # Arguments
        l1: Float; L1 regularization factor.
        l2: Float; L2 regularization factor.
    """

    def __init__(self, l1=0., l2=0.):
        self.l1 = K.cast_to_floatx(l1)
        self.l2 = K.cast_to_floatx(l2)

    def __call__(self, x):
        regularization = 0.
        if self.l1:
            regularization += K.sum(self.l1 * K.abs(x))
        if self.l2:
            regularization += K.sum(self.l2 * K.square(x))
        return regularization

    def get_config(self):
        return {'l1': float(self.l1),
                'l2': float(self.l2)}


# Aliases.


def l1(l=0.01):
    return L1L2(l1=l)


def l2(l=0.01):
    return L1L2(l2=l)


def l1_l2(l1=0.01, l2=0.01):
    return L1L2(l1=l1, l2=l2)


def serialize(regularizer):
    return serialize_keras_object(regularizer)


def deserialize(config, custom_objects=None):
    return deserialize_keras_object(config,
                                    module_objects=globals(),
                                    custom_objects=custom_objects,
                                    printable_module_name='regularizer')


def get(identifier):
    if identifier is None:
        return None
    if isinstance(identifier, dict):
        return deserialize(identifier)
    elif isinstance(identifier, six.string_types):
        config = {'class_name': str(identifier), 'config': {}}
        return deserialize(config)
    elif callable(identifier):
        return identifier
    else:
        raise ValueError('Could not interpret regularizer identifier: ' +
                         str(identifier))
class EigenvalueRegularizer(Regularizer):
    '''This takes a constant that controls
    the regularization by Eigenvalue Decay on the
    current layer and outputs the regularized
    loss (evaluated on the training data) and
    the original loss (evaluated on the
    validation data).
    '''
    '''
    def __init__(self, k):
        self.k = k
        self.uses_learning_phase = True

    def set_param(self, p):
        if hasattr(self, 'p'):
            raise Exception('Regularizers cannot be reused. '
                            'Instantiate one regularizer per layer.')
        self.p = p

    def __call__(self, loss):
        power = 9  # number of iterations of the power method
        W = self.p
        if K.ndim(W) > 2:
            raise Exception('Eigenvalue Decay regularizer '
                            'is only available for dense '
                            'and embedding layers.')
        WW = K.dot(K.transpose(W), W)
        dim1, dim2 = K.eval(K.shape(WW))  # number of neurons in the layer

        # power method for approximating the dominant eigenvector:
        o = K.ones([dim1, 1])  # initial values for the dominant eigenvector
        main_eigenvect = K.dot(WW, o)
        for n in range(power - 1):
            main_eigenvect = K.dot(WW, main_eigenvect)

        WWd = K.dot(WW, main_eigenvect)

        # the corresponding dominant eigenvalue:
        main_eigenval = (K.dot(K.transpose(WWd), main_eigenvect) /
                         K.dot(K.transpose(main_eigenvect), main_eigenvect))
        # multiplied by the given regularization gain
        regularized_loss = loss + (main_eigenval ** 0.5) * self.k

        return K.in_train_phase(regularized_loss[0, 0], loss)
'''
    def __init__(self, k):
        self.k = k
        
    def __call__(self, x):
        if K.ndim(x) != 2:
            raise ValueError('EigenvalueRegularizer '
                             'is only available for tensors of rank 2.')
        covariance = K.dot(K.transpose(x), x)
        dim1, dim2 = K.eval(K.shape(covariance))

        # Power method for approximating the dominant eigenvector:
        power = 9  # Number of iterations of the power method.
        o = K.ones([dim1, 1])  # Initial values for the dominant eigenvector.
        main_eigenvect = K.dot(covariance, o)
        for n in range(power - 1):
            main_eigenvect = K.dot(covariance, main_eigenvect)
        covariance_d = K.dot(covariance, main_eigenvect)

        # The corresponding dominant eigenvalue:
        main_eigenval = (K.dot(K.transpose(covariance_d), main_eigenvect) /
                         K.dot(K.transpose(main_eigenvect), main_eigenvect))
        # Multiply by the given regularization gain.
        regularization = (main_eigenval ** 0.5) * self.k
        return K.sum(regularization)

class WeightRegularizer(Regularizer):

    def __init__(self, l1=0., l2=0.):
        self.l1 = K.cast_to_floatx(l1)
        self.l2 = K.cast_to_floatx(l2)
        self.uses_learning_phase = True
        self.p = None

    def set_param(self, p):
        if self.p is not None:
            raise Exception('Regularizers cannot be reused. '
                            'Instantiate one regularizer per layer.')
        self.p = p

    def __call__(self, loss):
        if self.p is None:
            raise Exception('Need to call `set_param` on '
                            'WeightRegularizer instance '
                            'before calling the instance. '
                            'Check that you are not passing '
                            'a WeightRegularizer instead of an '
                            'ActivityRegularizer '
                            '(i.e. activity_regularizer="l2" instead '
                            'of activity_regularizer="activity_l2".')
        regularized_loss = loss
        if self.l1:
            regularized_loss += K.sum(self.l1 * K.abs(self.p))
        if self.l2:
            regularized_loss += K.sum(self.l2 * K.square(self.p))
        return K.in_train_phase(regularized_loss, loss)

    def get_config(self):
        return {'name': self.__class__.__name__,
                'l1': float(self.l1),
                'l2': float(self.l2)}


class ActivityRegularizer(Regularizer):

    def __init__(self, l1=0., l2=0.):
        self.l1 = K.cast_to_floatx(l1)
        self.l2 = K.cast_to_floatx(l2)
        self.uses_learning_phase = True
        self.layer = None

    def set_layer(self, layer):
        if self.layer is not None:
            raise Exception('Regularizers cannot be reused')
        self.layer = layer

    def __call__(self, loss):
        if self.layer is None:
            raise Exception('Need to call `set_layer` on '
                            'ActivityRegularizer instance '
                            'before calling the instance.')
        regularized_loss = loss
        for i in range(len(self.layer.inbound_nodes)):
            output = self.layer.get_output_at(i)
            if self.l1:
                regularized_loss += K.sum(self.l1 * K.abs(output))
            if self.l2:
                regularized_loss += K.sum(self.l2 * K.square(output))
        return K.in_train_phase(regularized_loss, loss)

    def get_config(self):
        return {'name': self.__class__.__name__,
                'l1': float(self.l1),
                'l2': float(self.l2)}


def l1(l=0.01):
    return WeightRegularizer(l1=l)


def l2(l=0.01):
    return WeightRegularizer(l2=l)


def l1l2(l1=0.01, l2=0.01):
    return WeightRegularizer(l1=l1, l2=l2)


def activity_l1(l=0.01):
    return ActivityRegularizer(l1=l)


def activity_l2(l=0.01):
    return ActivityRegularizer(l2=l)


def activity_l1l2(l1=0.01, l2=0.01):
    return ActivityRegularizer(l1=l1, l2=l2)        
