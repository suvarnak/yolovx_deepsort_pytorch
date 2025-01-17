# vim: expandtab:ts=4:sw=4
import numpy as np
import repository.yolovx_deepsort_pytorch.detector.YOLOV6.yolov6.utils.events as events
#import detector.YOLOV6.yolov6.utils.events 

class_names = events.load_yaml("./aim/hbm/repository/yolovx_deepsort_pytorch/detector/YOLOV6/data/coco.yaml")['names']

class Detection(object):
    """
    This class represents a bounding box detection in a single image.

    Parameters
    ----------
    tlwh : array_like
        Bounding box in format `(x, y, w, h)`.
    confidence : float
        Detector confidence score.
    feature : array_like
        A feature vector that describes the object contained in this image.

    Attributes
    ----------
    tlwh : ndarray
        Bounding box in format `(top left x, top left y, width, height)`.
    confidence : ndarray
        Detector confidence score.
    class_name : ndarray
        Detector class.
    feature : ndarray | NoneType
        A feature vector that describes the object contained in this image.

    """

    def __init__(self, tlwh, confidence, x1y1x2y2, cls_id, feature):
        self.tlwh = np.asarray(tlwh, dtype=np.float)
        self.x1y1x2y2 = x1y1x2y2
        self.confidence = float(confidence)
        self.class_name = class_names[cls_id]
        self.feature = np.asarray(feature, dtype=np.float32)

    def get_class(self):
        return self.class_name

    def to_tlbr(self):
        """Convert bounding box to format `(min x, min y, max x, max y)`, i.e.,
        `(top left, bottom right)`.
        """
        ret = self.tlwh.copy()
        ret[2:] += ret[:2]
        return ret

    def to_xyah(self):
        """Convert bounding box to format `(center x, center y, aspect ratio,
        height)`, where the aspect ratio is `width / height`.
        """
        ret = self.tlwh.copy()
        ret[:2] += ret[2:] / 2
        ret[2] /= ret[3]
        return ret