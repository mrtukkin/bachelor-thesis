from .set import SetList
from PIL import Image
from scipy.misc import imsave
from tqdm import tqdm
from . import caffeine
import caffe
import copy
import numpy as np
import os
import tempfile
import warnings

class NetRunner(object):
    """docstring for NetRunner."""
    epochs = 1
    baselr = 1

    def __init__(self):
        pass

    def createNet(self, model, weights, gpu):
        caffe.set_device(gpu)
        caffe.set_mode_gpu()
        self.net = caffe.Net(model, weights, caffe.TEST)

    def createSolver(self, solverpath, weights, gpu):
        caffe.set_device(gpu)
        caffe.set_mode_gpu()
        self.solver = caffe.SGDSolver(solverpath)
        solver.net.copy_from(weights)

    def addListFile(self, fpath):
        self.list = SetList(fpath)

    def loadimg(self, path, mean):
        im = Image.open(path)
        in_ = np.array(im, dtype=np.float32)
        in_ = in_[:,:,::-1]
        in_ -= np.array(mean)
        in_ = in_.transpose((2,0,1))
        return in_

    def forward(self, in_):
        self.net.blobs['data'].reshape(1, *in_.shape)
        self.net.blobs['data'].data[...] = in_
        # run net and take argmax for prediction
        self.net.forward()
        return self.net.blobs['score'].data[0].argmax(axis=0)

    def forwardList(self, postfix=''):
        for i in tqdm(self.list.list):
            o = self.forward(self.loadimg(i))
            imsave(i + postfix + '.out.png', o)


class FCNPartRunner(NetRunner):
    samples = []
    net_generator = caffeine.fcn.fcn8s
    builddir = 'data/models/tmp/'
    imgdir = 'data/datasets/voc2010/JPEGImages/'
    results = 'data/results/'
    weights = 'data/models/fcn8s/fcn8s-heavy-pascal.caffemodel'
    target = {}

    def __init__(self, tag, traintxt, valtxt, samples=0, random=True):
        super().__init__()
        self.name = tag
        self.random = random
        self.trainlist = SetList(traintxt)
        self.vallist = SetList(valtxt)
        if self.random:
            self.vallist.shuffle()
        self.targets()
        if samples > len(self.trainlist):
            warnings.Warning('More samples selected then possible...')
            samples = len(self.trainlist)
        samples = len(self.trainlist) if samples < 1 else samples
        self.selectSamples(samples)

    def targets(self, builddir=None):
        if builddir is None:
            builddir = self.builddir
        self.target['dir'] = os.path.normpath(builddir + '/' + tag) + '/'
        self.target['snapshots'] = self.target['dir'] + 'snapshots/'
        self.target['solver'] = self.target['dir'] + 'solver.prototxt/'
        self.target['train'] = self.target['dir'] + 'train.prototxt/'
        self.target['val'] = self.target['dir'] + 'val.prototxt/'
        self.target['trainset'] = self.target['dir'] + 'train.txt/'
        self.target['valset'] = self.target['dir'] + 'val.txt/'
        return

    def selectSamples(self, count):
        self.samples = copy.copy(self.trainlist)
        if self.random:
            self.samples.shuffle()
        self.samples.list = self.samples.list[:count]
        self.samples.target = self.target['trainset']

    def FCNparams(self, split):
        params = []
        params['img_dir'] = self.imgdir
        params['label_dir'] = self.labeldir
        params['splitfile'] = self.target[split + 'set']
        if not self.samples.mean:
            self.samples.calculate_mean()
        params['mean'] = self.samples.mean
        return params

    def write(self, split):
        with open(self.target[split], 'w') as f:
            f.write(str(self.net_generator(self.FCNparams(split))))

    def prepare(self):
        #Create build and snapshot direcotry:
        os.makedirs(self.target['snapshots'], exist_ok=True)
        self.samples.save()
        self.vallist.target = self.target['valset']
        self.vallist.save()
        self.write('train')
        self.write('val')
        self.writeSolver()

    def writeSolver(self):
        train_net = self.target['train']
        val_net = self.target['val']
        with open(self.target['solver'], 'w') as f:
            f.write((
                "train_net: '" + train_net + "\n"
                "test_net: '" + val_net + "\n"
                "test_iter: " + len(self.trainlist) + "\n"
                "test_interval: " + 99999999999 + "\n"
                "display: 100\n"
                "average_loss: 20\n"
                "lr_policy: 'fixed'\n"
                "base_lr: " + str(self.baselr) + "\n"
                "momentum: 0.99\n"
                "iter_size: 1"
                "max_iter: 100000\n"
                "weight_decay: 0.0005\n"
                "snapshot: " + len(self.trainlist) + "\n"
                "snapshot_prefix: "
                "'" + self.target['snapshots'] + "train" + "'\n"
                "test_initialization: false\n"
            ))

    def train(self):
        self.prepare()
        self.createSolver(self.target['solver'], self.weights, self.gpu)
        interp_layers = [k for k in solver.net.params.keys() if 'up' in k]
        caffeine.surgery.interp(self.solver.net, interp_layers)
        for _ in range(self.epochs):
            solver.step(len(self.samples))
        self.solver.snapshot()