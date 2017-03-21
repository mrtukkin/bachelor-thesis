#!/usr/bin/env python3
from ba.experiment import Experiment
import sys

DATASET = 'pascpart'
DSSSOURCE = 'data/datasets/pascalparts/Annotations_Part/'

def main(args):
    e = Experiment(argv=args)
    if e.sysargs.data:
        e.generate_data(DATASET, DSSSOURCE)
    if e.sysargs.prepare:
        e.prepare()
    if e.sysargs.tofcn:
        e.convert_to_FCN()
    if e.sysargs.train:
        e.train()
    if e.sysargs.test:
        e.test()
    e.exit()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('No arguments given')
        sys.exit()
    main(sys.argv[1:])
