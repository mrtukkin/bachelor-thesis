import os.path
from .PascalPart import PascalPart
from tqdm import tqdm
import numpy as np
import warnings
from scipy.misc import imread

class SetList(object):
    """docstring for SetList."""
    def __init__(self, source=''):
        super(SetList, self).__init__()
        self.source = source
        if source != '':
            self.load()

    def load(self):
        open(self.source, 'a').close()
        with open(self.source) as f:
            self.list = f.read().splitlines()

    def save(self):
        with open(self.source, 'w') as f:
            for row in self.list:
                f.write("{}\n".format(row))
                print('List {} written...'.format(self.source))

    def addPreSuffix(self, prefix, suffix):
        self.list = [prefix + x + suffix for x in self.list]

    def rmPreSuffix(self, prefix, suffix):
        self.list = [x[len(prefix):-len(suffix)] for x in self.list]

    def calculate_mean(self):
        self.mean = [[],[],[]]
        for row in tqdm(self.list):
            im = imread(row)
            self.mean[0].append(np.mean(im[...,0]))
            self.mean[1].append(np.mean(im[...,1]))
            self.mean[2].append(np.mean(im[...,2]))
        self.mean = np.mean(self.mean, axis=1)
        return self.mean

    def genPartList(self, classname, parts):
        print('generate Parts list for {} in {}'.format(parts, classname))
        bn, en = os.path.splitext(self.source)
        plist = SetList('_'.join([bn, classname]) + '_' + '_'.join(parts) + en)
        for i in tqdm(range(len(self.list) - 1)):
            pp = PascalPart(self.list[i])
            if classname and pp.classname != classname:
                continue

            if not any(x in pp.parts for x in parts):
                continue

            plist.content.append(self.list[i])

        return plist

    def each(self, callback):
        if not callable(callback):
            warnings.warn('Not callable object')
            return
        print('Calling each object in SetList....')
        for row in tqdm(self.list):
            callback(row)
