from glob import glob
import os.path
import sys
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt

class Bunch(object):
    '''Serves as a dictionary in the form of an object.'''
    def __init__(self, adict):
        '''Construct a bunch

        Args:
            adict (dict): The dictionary to build the object from
        '''
        self.__dict__.update(adict)

    def __str__(self):
        '''Get the string representation for the bunch (inherit from dict..)

        Returns:
            The string representation
        '''
        return self.__dict__.__str__()

def apply_overlay(image, overlay, path, label=''):
    '''Overlay overlay onto image and add label as text
    and save to path (full path with extension!)

    Args:
        image (image): The image to use as 'background'.
        overlay (image): The image to overly over the image.
        path (str): The path to save the result to.
        label (str, optional): A label for the heatmap.
    '''
    xS = 3
    yS = xS / image.shape[1] * image.shape[0]
    fig = plt.figure(frameon=False, figsize=(xS,yS), dpi=image.shape[1]/xS)
    plt.axis('off')
    ax = plt.Axes(fig, [0.,0.,1.,1.])
    ax.set_axis_off()
    fig.add_axes(ax)
    plt.imshow(image, interpolation='none')
    plt.imshow(overlay, cmap='viridis', alpha=0.5, interpolation='none')
    if label != '':
        patch = mpatches.Patch(color='yellow', label=label)
        plt.legend(handles=[patch])
    fig.savefig(path, pad_inches=0, dpi=fig.dpi)
    plt.close(fig)


def query_boolean(question, default='yes', defaulting=False):
    '''Ask a yes/no question via input() and return their answer.

    Args:
        question (str): Is a string that is presented to the user.
        default (str, optional): Is the presumed answer if the user just
            hits <Enter>. It must be 'yes' (the default), 'no' or None
            (meaning an answer is required of the user).
        defaulting (bool, optional): If we should just do the default

    Returns:
        True for 'yes' or False for 'no'.
    '''
    valid = {'yes': True, 'y': True, 'ye': True, 'j': True, 'ja': True,
             'no': False, 'n': False, 'nein': False}
    if default is None:
        prompt = ' (y/n) '
    elif default == 'yes':
        prompt = ' ([Y]/n) '
    elif default == 'no':
        prompt = ' (y/[N]) '
    else:
        raise ValueError('invalid default answer: {}'.format(default))
    if defaulting:
        return valid[default]
    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == '':
            print(default)
            return valid[default]
        elif choice in valid:
            print(choice)
            return valid[choice]
        else:
            print('Please respond with "yes" or "no" '
                  '(or "y" or "n").')


def query_overwrite(path, default='yes', defaulting=False):
    '''Checks with the user if a file shall be overwritten

    Args:
        path (str): The path to the file

    Returns:
        bool: True if write over, False if not
    '''

    if not os.path.exists(path):
        return True
    question = ('File {} does exist.\n'
                'Overwrite it?'.format(path))
    return query_boolean(question, default=default, defaulting=defaulting)


def touch(path, clear=False):
    '''Touches a filepath (dir or file...)

    Args:
        path (str): The path to touch
        clear (bool): If the file shall be truncated
    '''
    dir_ = os.path.dirname(path)
    if dir_ != '':
        os.makedirs(dir_, exist_ok=True)
    if not os.path.isdir(path):
        open(path, 'a').close()
        if clear:
            open(path, 'w').close()


def prevalentExtension(path):
    '''Looks at a directory and returns the most prevalent file extension of
    the files in this directory.

    Args:
        path (str): The path to the directory

    Returns:
        the extension without leading full stop
    '''
    path = os.path.normpath(path) + '/'
    exts = [os.path.splitext(x)[1][1:] for x in glob(path + '*')]
    exts = [x for x in exts if x]
    return max(set(exts), key=exts.count)

def sliding_window(image, stride, kernel_size):
    '''Slides a quadratic window over an image.

    Args:
        image (image): The image to use
        stride (int): The step size for the sliding window
        kernel_size (int): Width of the window
    '''
    for y in range(0, image.shape[0], stride):
        for x in range(0, image.shape[1], stride):
            yield (x, y, image[y:y + kernel_size, x:x + kernel_size])
