import ba.utils
from functools import lru_cache as cache
import ba.plt
import copy
from matplotlib import pyplot as plt
import numpy as np
import skimage.transform as tf
from scipy.ndimage import distance_transform_cdt
from scipy.misc import imread
from tqdm import tqdm


def extract_mean_evals(itemlist, evalf):
    '''Extracting the mean evaluations for a set of results.

    Args:
        itemlist (list): A list of datum indices
        evalf (str): The path to the YAML file containing hte results.

    Returns:
        meanIOU, meanDistErr, meanScalErr, len(evals)
    '''
    evals = ba.utils.load(evalf)
    _evals = copy.deepcopy(evals)
    for e in _evals:
        if e not in itemlist:
            del evals[e]
    meanIOU = float(np.mean([i['iOU'] for i in evals.values()]))
    meanDistErr = float(np.mean([i['disterr'] for i in evals.values()]))
    meanScalErr = float(np.mean([i['scalingerr'] for i in evals.values()]))
    return meanIOU, meanDistErr, meanScalErr, len(evals)


def evalDect(predf, gtf):
    '''Evaluate detection for a result file.

    Args:
        predf (str): The path to the YAML file conataining the predictions
        gtf (str): The path to the YAML file conataining the ground truth

    Returns:
        precision, recall, thresholds
    '''
    def hits(rect, targets):
        return any([intersectOverLeft(rect, target) >= 0.7 for
                    target in targets])

    predicted_slices = ba.utils.load(predf)
    if predicted_slices is None:
        return
    ground_truth_slices = ba.utils.load(gtf)
    outputfile = '.'.join(predf.split('.')[:-2] + ['results', 'mp'])
    tqdm.write('Evaluating detection {}'.format(predf))
    hitted_labels = []
    pred_labels = []
    for idx, pred in tqdm(predicted_slices.items()):
        rects = pred['region']
        scores = pred['score']

        # Get the ground truth:
        ground_truth = ground_truth_slices[idx]
        gt_rects = [(s[0].start, s[1].start,
                     s[0].stop, s[1].stop) for s in ground_truth]

        # Evaluate it:
        hitted_labels.extend([int(hits(rect, gt_rects)) for rect in rects])
        pred_labels.extend(scores)
    ba.utils.save(outputfile,
                  {'hitted_labels': hitted_labels,
                   'pred_labels': pred_labels})


def evalYAML(predf, gtf, images, heatmaps=None):
    '''Evaluates the predicted regions from a test run. Writes the performances
    to an other YAML file.

    Args:
        predf (str): The path to the YAML file containing the predictions
        gtf (str): The path to the YAML file containing ground truth regions
        images (str): The path to the original images
        heatmaps (str, optional): The path to the original heatmaps
    '''
    preds = ba.utils.load(predf)
    gts = ba.utils.load(gtf)
    outputfile = '.'.join(predf.split('.')[:-2] + ['evals', 'yaml'])
    outputdir = ba.utils.touch('.'.join(predf.split('.')[:-2]) + '/evals/')
    results = {}
    ext_img = ba.utils.prevalent_extension(images)
    if heatmaps is not None:
        ext_hm = ba.utils.prevalent_extension(heatmaps)
    print('Evaluating {}'.format(predf))
    for idx, pred in tqdm(preds.items()):
        rect = pred['region']
        score = pred['score']
        im = imread('{}{}.{}'.format(images, idx, ext_img))
        if heatmaps is not None:
            hm = imread('{}{}.{}'.format(heatmaps, idx, ext_hm))
            hm = tf.resize(hm, im.shape[:-1], mode='reflect')
        imout = outputdir + idx + '.png'
        # Get the ground truth:
        gtslice = gts[idx]
        gtrect = (gtslice[0].start, gtslice[1].start,
                  gtslice[0].stop, gtslice[1].stop)

        # Evaluate it:
        iOU = intersectOverUnion(rect, gtrect)
        l2dist = rectDistance(rect, gtrect)
        diagonal = np.linalg.norm(im.shape[:-1])
        disterr = float(l2dist / diagonal)
        scalingerr = float(np.linalg.norm(
            [(rect[2] - rect[0]) / (gtrect[2] - gtrect[0]),
             (rect[3] - rect[1]) / (gtrect[3] - gtrect[1])]))
        results[idx] = {'iOU': iOU, 'disterr': disterr,
                        'scalingerr': scalingerr}

        # Save overlay image:
        if heatmaps is None:
            ba.plt.apply_rect(im, [rect, gtrect], imout, ['red', 'green'],
                              [score, ''])
        else:
            fig = ba.plt._prepareImagePlot(im)
            ba.plt.apply_overlay(im, hm, imout, fig=fig)
            ba.plt.apply_rect(im, [rect, gtrect], imout, ['red', 'green'],
                              [score, ''], fig=fig)
            fig.savefig(imout, pad_inches=0, dpi=fig.dpi)
            plt.close(fig)

    ba.utils.save(outputfile, results)
    return outputfile


def rectDistance(a, b):
    '''Calculates the distance between the centers of two rectangles.

    Args:
        a (tuple): (xmin ymin xmax ymax)
        b (tuple): (xmin ymin xmax ymax)

    Returns the iOU
    '''
    aCenter = np.array([(a[0] + a[2]) / 2.0, (a[1] + a[3]) / 2.0])
    bCenter = np.array([(b[0] + b[2]) / 2.0, (b[1] + b[3]) / 2.0])
    return np.linalg.norm(aCenter - bCenter)


def intersectOverLeft(a, b):
    area = intersectArea(a, b)
    if area == 0:
        return area
    aArea = (a[2] - a[0]) * (a[3] - a[1])
    return area / aArea


def intersectOverUnion(a, b):
    '''Calculates the intersect over Union of two rectangles.

    Args:
        a (tuple): (xmin ymin xmax ymax)
        b (tuple): (xmin ymin xmax ymax)

    Returns the iOU
    '''
    area = intersectArea(a, b)
    if area == 0:
        return area
    aArea = (a[2] - a[0]) * (a[3] - a[1])
    bArea = (b[2] - b[0]) * (b[3] - b[1])
    iOU = area / float(aArea + bArea - area)
    return iOU


def intersectArea(a, b):
    '''Calculates the area of the intersecting area of two rectangles.

    Args:
        a (tuple): (xmin ymin xmax ymax)
        b (tuple): (xmin ymin xmax ymax)

    Returns the area
    '''
    dx = min(a[2], b[2]) - max(a[0], b[0])
    dy = min(a[3], b[3]) - max(a[1], b[1])
    if dx >= 0 and dy >= 0:
        return dx * dy
    else:
        return 0.0


@cache(maxsize=32)
def _generic_box(shape, scales=(2, 7, 15,), cache=True):
    '''Returns a generic grid of boxes for an image. A little bit like done
    on YOLO

    Args:
        shape (ndarray): The shape of the image
        scales (tupel, optional): The scales as dividents of the img size to
            generate boxes for
        cache (bool, optional): Whether to use the cache

    Returns:
        a list of regions
    '''
    def generic_regions(shape, width, height, stride=1):
        steps = (int(height * stride), int(width * stride))
        for x1, x2 in ba.utils.sliding_slice(shape, steps, (height, width)):
            yield ((x1, x2), (x1 + height, x2 + width))

    # if cache and shape in _generic_box.boxsets:
    #     return _generic_box.boxsets[shape]
    h, w = shape
    areas = []
    starts = []
    ends = []
    basel = 100
    scales = np.mat([1, 1.5, 2])
    ascpect_ratios = np.mat([1, 4 / 3, 1.6180, 2, 2.76])
    widths = np.dot(scales.T, ascpect_ratios).flat
    i = np.vstack(len(widths) * [widths])
    sizes = (np.vstack(([i], [i.T])).T * basel).reshape(-1, 2).astype(int)
    for _h, _w in sizes:
        # _h = int(h / scale)
        # _w = int(w / scale)
        _area = _h * _w
        for (x1, y1), (x2, y2) in generic_regions(shape, _w, _h, 0.5):
            rec = False
            if x2 >= h:
                rec = True
                x2 = h - 1
            if y2 >= w:
                rec = True
                y2 = w - 1
            if rec:
                continue
                area = (x2 - x1) * (y2 - y1)
                if area == 0:
                    continue
                areas.append(area)
            else:
                areas.append(_area)
            starts.append((x1, y1))
            ends.append((x2, y2))
    # _generic_box.boxsets[shape] = (np.array(starts),
    #                                np.array(ends),
    #                                np.array(areas))
    # return _generic_box.boxsets[shape]
    return (np.array(starts), np.array(ends), np.array(areas))


def nms(starts, ends, scores, thresh=0.5):
    '''Non maximum suppression.
    See Discriminatively Trained Deformable Part Models, Release 5
        http://www.rossgirshick.info/latent/

    Args:
        starts (iterable of 2-tuples): The coordinates of the left-top points
        ends (iterable of 2-tuples): The coordinates of the right-bottom points
        scores (iterable): The scores of the boxes
        thresh (float, optional): The threshold to remove regions.

    Returns:
        The indices of picked boxes.
    '''

    starts = np.array(starts).astype(float)
    ends = np.array(ends).astype(float)

    # grab the coordinates of the bounding boxes
    x1 = starts[:, 0]
    y1 = starts[:, 1]
    x2 = ends[:, 0]
    y2 = ends[:, 1]

    area = (x2 - x1 + 1) * (y2 - y1 + 1)
    idxs = np.argsort(scores)

    picks = []
    while len(idxs) > 0:
        last = len(idxs) - 1
        highest_indice = idxs[last]
        picks.append(highest_indice)

        xx1 = np.maximum(x1[highest_indice], x1[idxs[:last]])
        yy1 = np.maximum(y1[highest_indice], y1[idxs[:last]])
        xx2 = np.minimum(x2[highest_indice], x2[idxs[:last]])
        yy2 = np.minimum(y2[highest_indice], y2[idxs[:last]])

        w = np.maximum(0, xx2 - xx1 + 1)
        h = np.maximum(0, yy2 - yy1 + 1)

        overlap = (w * h) / area[idxs[:last]]

        idxs = np.delete(idxs, np.concatenate(
            ([last], np.where(overlap > thresh)[0])))

    return picks


def scoreToRegion(hm):
    '''Reudces a heatmap to a bounding box by searching through regions of the
    image generated by the generic box generator.

    Args:
        hm (ndarray): The map of un-normalized scores

    Returns:
        The maximum bounding box (x_start, y_start, x_end, y_end)
    '''
    scales = (2, 5, 7,)
    starts, ends, areas = _generic_box(hm.shape, scales=scales)
    if len(starts) == 0:
        return np.array([]), np.array([])

    # Add distance base negative penalty:
    # thres = 0.3
    # negative_hm = distance_transform_cdt(hm < thres).astype(float)
    # if negative_hm.max() > 0:
    #   negative_hm /= negative_hm.max()
    #   negative_hm *= 1
    # hm -= negative_hm

    # import scipy.ndimage
    # gradient = scipy.ndimage.gaussian_gradient_magnitude(hm, 1)
    # gradient /= gradient.max()
    # Construct the integral image
    # ii = gradient
    # for i in range(ii.ndim):
    #     ii = ii.cumsum(axis=i)

    # Calculates the sum of an box
    def ii_rect(s, e):
        return ii[s[0], s[1]] + ii[e[0],
                                   e[1]] - ii[s[0], e[1]] - ii[e[0], s[1]]
    # gradient_volumes = np.array([ii_rect(s, e) for s, e in zip(starts, ends)])

    # import scipy.ndimage
    # sub_hm = ((hm < 0.3) * -1).astype(float)
    # sub_hm = scipy.ndimage.filters.gaussian_filter(sub_hm, 8)
    # hm += sub_hm

    # Construct the integral image
    ii = hm
    for i in range(ii.ndim):
        ii = ii.cumsum(axis=i)

    # Calculates the sum of an box
    volumes = np.array([ii_rect(s, e) for s, e in zip(starts, ends)])

    # # Get the score densities
    densities = np.divide(volumes, areas)
    # gradient_densities = np.divide(gradient_volumes, areas)
    bbscores = densities  # * gradient_densities
    picks = bbscores > (0.2 * bbscores.max())
    if any(picks):
        bbscores = bbscores[picks]
        starts = starts[picks]
        ends = ends[picks]
        # from os import _exit as e; import ipdb; ipdb.set_trace()
        picks = nms(starts, ends, bbscores)
        bbscores = bbscores[picks]
        starts = starts[picks]
        ends = ends[picks]
    elif len(bbscores) > 0:
        picks = bbscores.argmax()
        bbscores = np.array([bbscores[picks]])
        starts = np.array([starts[picks]])
        ends = np.array([ends[picks]])

    if len(bbscores) > 0:
        return np.concatenate((starts, ends), axis=1), bbscores
    else:
        return np.array([]), np.array([])
