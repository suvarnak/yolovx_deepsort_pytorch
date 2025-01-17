import numpy as np
import torch

from .deep.feature_extractor import Extractor, FastReIDExtractor
# from .deep.feature_extractor import Extractor
from .sort.nn_matching import NearestNeighborDistanceMetric
from .sort.preprocessing import non_max_suppression
from .sort.detection_w_classname import Detection
from .sort.tracker_w_classname import Tracker

__all__ = ['DeepSort']

class DeepSort(object):
    def __init__(self, model_path, model_config=None, max_dist=0.2, min_confidence=0.3, nms_max_overlap=1.0, max_iou_distance=0.7, max_age=70, n_init=3, nn_budget=100, use_cuda=True):
        self.min_confidence = min_confidence
        self.nms_max_overlap = nms_max_overlap

        if model_config is None:
            self.extractor = Extractor(model_path, use_cuda=use_cuda)
        else:
            self.extractor = FastReIDExtractor(model_config, model_path, use_cuda=use_cuda)

        max_cosine_distance = max_dist
        metric = NearestNeighborDistanceMetric("cosine", max_cosine_distance, nn_budget)
        self.tracker = Tracker(metric, max_iou_distance=max_iou_distance, max_age=max_age, n_init=n_init)

    def update(self, bbox_xywh, confidences, class_ids, ori_img):
        self.height, self.width = ori_img.shape[:2]     # ------------生成detections
        # generate detections
        features = self._get_features(bbox_xywh, ori_img)   # reid网络，提取每个bbox的feature
        
        bbox_tlwh = self._xywh_to_tlwh(bbox_xywh)           # [cx,cy,w,h] -> [x1,y1,w,h]
        bbox_x1y1x2y2 = [ (self._xywh_to_xyxy(box))  for box in bbox_xywh ]
        detections = [Detection(bbox_tlwh[i], conf, bbox_x1y1x2y2[i], class_ids[i], features[i]) for i,conf in enumerate(confidences) if conf>self.min_confidence]  
        #detections = [Detection(bbox_tlwh[i], conf, bbox_x1y1x2y2[i], "None", features[i]) for i,conf in enumerate(confidences) if conf>self.min_confidence]  
        
        # run on non-maximum supression     # ---->  对检测框进行 non_max_suppression
        boxes = np.array([d.tlwh for d in detections])          # 获取所有检测框
        scores = np.array([d.confidence for d in detections])   # 获取所有检测框对应的得分
        indices = non_max_suppression(boxes, self.nms_max_overlap, scores)
        #detections = [(detections[i], scores[i]) for i in indices]           
        detections = [detections[i] for i in indices]           
        scores = [scores[i] for i in indices]           # to retain the scores of detection after NMS
        self.tracker.predict()          
        self.tracker.update(detections, scores) 

        # output bbox identities
        outputs = []
        #print("~~~~~~~~~~~~",boxes, scores, self.tracker.tracks) #track.class_name)
        for track in self.tracker.tracks:
            if not track.is_confirmed() or track.time_since_update > 1:
                continue
            box = track.to_tlwh()
            x1,y1,x2,y2 = self._tlwh_to_xyxy(box)
            track_id = track.track_id
            outputs.append(np.array([x1,y1,x2,y2,track_id, track.class_name, track.score]))      
        if len(outputs) > 0:
            outputs = np.stack(outputs,axis=0)
        confirmed_tracks = [i for i in self.tracker.tracks if i.is_confirmed]
        tentative_tracks = [i for i in self.tracker.tracks if i.is_tentative]
        print("Confirmed tracks ", len(confirmed_tracks))
        print("Tentative tracks ", len(tentative_tracks))
        return outputs, detections, len(confirmed_tracks), len(tentative_tracks)


    """
    TODO:
        Convert bbox from xc_yc_w_h to xtl_ytl_w_h
    Thanks JieChen91@github.com for reporting this bug!
    """
    @staticmethod
    def _xywh_to_tlwh(bbox_xywh):
        if isinstance(bbox_xywh, np.ndarray):
            bbox_tlwh = bbox_xywh.copy()
        elif isinstance(bbox_xywh, torch.Tensor):
            bbox_tlwh = bbox_xywh.clone()
        bbox_tlwh[:,0] = bbox_xywh[:,0] - bbox_xywh[:,2]/2.
        bbox_tlwh[:,1] = bbox_xywh[:,1] - bbox_xywh[:,3]/2.

        return bbox_tlwh

    def _xywh_to_xyxy(self, bbox_xywh):
        x,y,w,h = bbox_xywh
        x1 = max(int(x-w/2),0)
        x2 = min(int(x+w/2),self.width-1)
        y1 = max(int(y-h/2),0)
        y2 = min(int(y+h/2),self.height-1)
        return x1,y1,x2,y2

    def _tlwh_to_xyxy(self, bbox_tlwh):
        """
        TODO:
            Convert bbox from xtl_ytl_w_h to xc_yc_w_h
        Thanks JieChen91@github.com for reporting this bug!
        """
        x,y,w,h = bbox_tlwh
        x1 = max(int(x),0)
        x2 = min(int(x+w),self.width-1)
        y1 = max(int(y),0)
        y2 = min(int(y+h),self.height-1)
        return x1,y1,x2,y2

    def _xyxy_to_tlwh(self, bbox_xyxy):
        x1,y1,x2,y2 = bbox_xyxy

        t = x1
        l = y1
        w = int(x2-x1)
        h = int(y2-y1)
        return t,l,w,h
    
    def _get_features(self, bbox_xywh, ori_img):
        im_crops = []
        for box in bbox_xywh:
            x1,y1,x2,y2 = self._xywh_to_xyxy(box)
            im = ori_img[y1:y2,x1:x2]
            im_crops.append(im)
        if im_crops:
            features = self.extractor(im_crops)
        else:
            features = np.array([])
        return features


