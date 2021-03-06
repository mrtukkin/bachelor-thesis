'''
    Based on code from Evan Shelhamer
    fcn.berkeleyvision.org
'''
from caffe import layers as L
from caffe import params as P
import math


def upsample(bottom, factor, nout, name=None):
    '''Generates an bilinear upsampling layer

    Args:
        bottom (caffe.Layer): The bottom layer
        factor (int): The factor to resize with
        nout (int): The numer of outputs
        name (str, optional): A name for the layer

    Returns:
        the layers
    '''
    ks = 2 * factor - factor % 2
    pad = math.ceil(float(factor - 1) / 2.0)
    if name is not None:
        return L.Deconvolution(bottom, name=name, convolution_param=dict(
            kernel_size=ks, stride=factor, num_output=nout, pad=pad,
            weight_filler=dict(type='bilinear'),
            bias_term=False), param=dict(lr_mult=0, decay_mult=0))
    else:
        return L.Deconvolution(bottom, convolution_param=dict(
            kernel_size=ks, stride=factor, num_output=nout, pad=pad,
            weight_filler=dict(type='bilinear'),
            bias_term=False), param=dict(lr_mult=0, decay_mult=0))


def fc(bottom, nout=4096, std=0.01, lrmult=0):
    '''Generates a fully connected layer tailed by an relu

    Args:
        bottom (caffe.Layer): The bottom layer
        nout (int): The numer of outputs
        std (int, optional): The standard dev. for the weight filler
        lrmult (int, optional): A lr_mult multiplier

    Returns:
        the layers
    '''

    fc = L.InnerProduct(bottom,
                        inner_product_param=dict(
                            weight_filler=dict(type='gaussian', std=std),
                            bias_filler=dict(type='constant', value=0),
                            num_output=nout),
                        param=[dict(lr_mult=1 * lrmult, decay_mult=1),
                               dict(lr_mult=2 * lrmult, decay_mult=0)])
    return fc, L.ReLU(fc, in_place=True)


def conv_relu(bottom, nout, ks=3, stride=1, pad=1, lrmult=False, name=None):
    '''Generates a Convolution layer tailed by an relu

    Args:
        bottom (caffe.Layer): The bottom layer
        nout (int): The numer of outputs
        ks (int, optional): The kernel_size
        stride (int, optional): The stride for the Convolution
        pad (int, optional): The padding for the Convolution
        lrmult (int, optional): A lr_mult multiplier

    Returns:
        the layers
    '''
    if name is not None:
        conv = L.Convolution(bottom, kernel_size=ks, stride=stride,
                             num_output=nout, pad=pad, name=name,
                             param=[dict(lr_mult=1 * lrmult, decay_mult=1),
                                    dict(lr_mult=2 * lrmult, decay_mult=0)])
    else:
        conv = L.Convolution(bottom, kernel_size=ks, stride=stride,
                             num_output=nout, pad=pad,
                             param=[dict(lr_mult=1 * lrmult, decay_mult=1),
                                    dict(lr_mult=2 * lrmult, decay_mult=0)])
    return conv, L.ReLU(conv, in_place=True)


def max_pool(bottom, ks=2, stride=2):
    '''Generates a MAX pooling layer.

    Args:
        bottom (caffe.Layer): The bottom layer
        ks (int, optional): The kernel_size
        stride (int, optional): The stride for the pooling

    Returns:
        the layer
    '''
    return L.Pooling(bottom, pool=P.Pooling.MAX, kernel_size=ks, stride=stride)
