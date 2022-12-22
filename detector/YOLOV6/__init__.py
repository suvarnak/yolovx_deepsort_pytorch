import sys
sys.path.append("detector/YOLOV6")
sys.path.append('yolov6/')


from .detector import YOLOv6
from . import tools
from . import yolov6
__all__ = ['YOLOv6',
            'tools',
            'yolov6'
            ]



