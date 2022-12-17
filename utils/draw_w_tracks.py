import numpy as np
import cv2
from detector.YOLOV6.yolov6.utils import events 

class_names = events.load_yaml("detector/YOLOV6/data/coco.yaml")['names']
palette = (2 ** 11 - 1, 2 ** 15 - 1, 2 ** 20 - 1)


def compute_color_for_labels(label):
    """
    Simple function that adds fixed color depending on the class
    """
    color = [int((p * (label ** 2 - label + 1)) % 255) for p in palette]
    return tuple(color)

def compute_class_name_for_label(id):
    return class_names[id]

def draw_boxes(img, bbox, identities=None, class_names=None, offset=(0,0), score = []):
    for i,box in enumerate(bbox):
        x1,y1,x2,y2 = [int(i) for i in box]
        x1 += offset[0]
        x2 += offset[0]
        y1 += offset[1]
        y2 += offset[1]
        # box text and bar
        id = int(identities[i]) if identities is not None else 0    
        classname = class_names[i] if class_names is not None else "Unknown"    
        color = compute_color_for_labels(id)
        label = '{}{:d}'.format(classname, id )
        # score = score
        t_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_PLAIN, 1 , 1)[0]
        cv2.rectangle(img,(x1, y1),(x2,y2),color,2)
        cv2.rectangle(img,(x1, y1),(x1+t_size[0]+3,y1+t_size[1]+4), color,-1)
        #label = str(compute_class_name_for_label(label)+label)
        cv2.putText(img,label,(x1,y1+t_size[1]+4), cv2.FONT_HERSHEY_PLAIN, 1, [255,255,255], 1)
        if len(score) != 0:
            cv2.putText(img,str(score[i]),(x1,y1+t_size[1]+10), cv2.FONT_HERSHEY_PLAIN, 2, [255,255,255], 2)

    return img



if __name__ == '__main__':
    pass
    # for i in range(82):
    #     print(compute_color_for_labels(i))
