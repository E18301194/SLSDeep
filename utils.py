import torch
import numpy as np
import torch.nn as nn
from skimage import filters
import torch.nn.functional as F

class AverageMeter(object):
    """Computes and stores the average and current value"""
    def __init__(self):
        self.initialized = False
        self.val = None
        self.avg = None
        self.sum = None
        self.count = None

    def initialize(self, val, weight):
        self.val = val
        self.avg = val
        self.sum = val * weight
        self.count = weight
        self.initialized = True

    def update(self, val, weight=1):
        if not self.initialized:
            self.initialize(val, weight)
        else:
            self.add(val, weight)

    def add(self, val, weight):
        self.val = val
        self.sum += val * weight
        self.count += weight
        self.avg = self.sum / self.count

    def value(self):
        return self.val

    def average(self):
        return self.avg


def unique(ar, return_index=False, return_inverse=False, return_counts=False):
    ar = np.asanyarray(ar).flatten()

    optional_indices = return_index or return_inverse
    optional_returns = optional_indices or return_counts

    if ar.size == 0:
        if not optional_returns:
            ret = ar
        else:
            ret = (ar,)
            if return_index:
                ret += (np.empty(0, np.bool),)
            if return_inverse:
                ret += (np.empty(0, np.bool),)
            if return_counts:
                ret += (np.empty(0, np.intp),)
        return ret
    if optional_indices:
        perm = ar.argsort(kind='mergesort' if return_index else 'quicksort')
        aux = ar[perm]
    else:
        ar.sort()
        aux = ar
    flag = np.concatenate(([True], aux[1:] != aux[:-1]))

    if not optional_returns:
        ret = aux[flag]
    else:
        ret = (aux[flag],)
        if return_index:
            ret += (perm[flag],)
        if return_inverse:
            iflag = np.cumsum(flag) - 1
            inv_idx = np.empty(ar.shape, dtype=np.intp)
            inv_idx[perm] = iflag
            ret += (inv_idx,)
        if return_counts:
            idx = np.concatenate(np.nonzero(flag) + ([ar.size],))
            ret += (np.diff(idx),)
    return ret


def colorEncode(labelmap, colors):
    labelmap = labelmap.astype('int')
    labelmap_rgb = np.zeros((labelmap.shape[0], labelmap.shape[1], 3),
                            dtype=np.uint8)
    for label in unique(labelmap):
        if label < 0:
            continue
        labelmap_rgb += (labelmap == label)[:, :, np.newaxis] * \
            np.tile(colors[label],
                    (labelmap.shape[0], labelmap.shape[1], 1))
    return labelmap_rgb


def accuracy(batch_data, pred):
    (imgs, segs, infos) = batch_data
    _, preds = torch.max(pred.data.cpu(), dim=1)
    valid = (segs >= 0)
    acc = 1.0 * torch.sum(valid * (preds == segs)) / (torch.sum(valid) + 1e-10)
    return acc, torch.sum(valid)


def EPE(predicted_edge, gt_edge, sparse=False, mean=True):
    EPE_map = torch.norm(gt_edge-predicted_edge,2,1)
    if sparse:
        EPE_map = EPE_map[gt_edge != 0]
    if mean:
        return EPE_map.mean()
    else:
        return EPE_map.sum()

def getEdge(batch):
    edgeslist=[]
    for kk in range(batch.size(0)):
        x=batch[kk]
        # print(x.size())   
        x=x.cpu().data.numpy()
        if len(x.shape)>2:
            x=np.transpose(x,(1,2,0))
            x=rgb2gray(x)
        edges = filters.sobel(x)
        edgeslist.append(edges)
    edgeslist=np.array(edgeslist)
    edgeslist=torch.Tensor(edgeslist).cuda()
    edgeslist=F.Variable(edgeslist)
    return  edgeslist



