import importlib
import os
import sys
from pathlib import Path
from typing import Any

import numpy as np
from munch import Munch
from torch import nn

from app.util import add_sys_path, singleton

root = Path(__file__).resolve().parent.parent

with add_sys_path(root / "ocr"):
    file_utils = importlib.import_module("file_utils")
    net_utils = importlib.import_module("net_utils")
    imgproc = importlib.import_module("imgproc")
    opt = importlib.import_module("opt")
    bubble_detect = importlib.import_module("object_detection.bubble").test_net
    cut_detect = importlib.import_module("object_detection.cut").test_opencv
    line_text_detect = importlib.import_module("text_detection.line_text").test
    line_text_recognize = importlib.import_module("text_recognition.line_text").test_net
    gen_text_to_image = importlib.import_module("text_recognition.ltr_utils").gen_txt_to_image
    papago_translation = importlib.import_module("translation.papago").translation


@singleton
class ModelManager:
    def __init__(self) -> None:
        self._models = None

    def load(
        self,
        text_detector: str = str(root / "weights" / "Line-Text-Detector.pth"),
        text_recognizer: str = str(root / "weights" / "Line-Text-Detector.pth"),
        object_detector: str = str(root / "weights" / "Speech-Bubble-Detector.pth"),
    ) -> None:
        net_cfg = Munch(
            object=True,
            ocr=True,
            text_detector=text_detector,
            text_recognizer=text_recognizer,
            object_detector=object_detector,
        )
        self._models = net_utils.load_net(net_cfg)

    @property
    def models(self) -> dict[str, nn.Module]:
        if self._models is None:
            self.load()
        return self._models

text_warp_items = []

def run_ocr(
    img: np.ndarray,
    bg_type: str = "white",
    bubble_threshold: float = 0.995,
    box_threshold: int = 7000,
) -> Any:
    """img: 0-255 uint8 height x width x 3 image"""
    img_blob, img_scale = imgproc.getImageBlob(img)
    models = ModelManager().models
    f_RCNN_param = [img_blob, img_scale, opt.LABEL]

    demo, image, bubbles, dets_bubbles = bubble_detect(
        model=models["bubble_detector"],
        image=img,
        params=f_RCNN_param,
        cls=bubble_threshold,
        bg=bg_type,
    )
    demo, cuts = cut_detect(image=image, demo=demo, bg=bg_type, size=box_threshold)

    demo, space, warps = line_text_detect(
        model=models["text_detector"],
        demo=demo,
        bubbles=imgproc.cpImage(bubbles),
        dets=dets_bubbles,
        img_name="img",  # ???
        save_to="./result/chars/",  # disable saving
    )

    text_warp_items += warps

    label_mapper = file_utils.makeLabelMapper(
        load_from=str(root / "text_recognition" / "labels-2213.txt")
    )

    line_text_recognize(
        model=models["text_recognizer"],
        mapper=label_mapper,
        spaces=space,
        load_from="./result/chars/",
        save_to="./result/ocr.txt",
    )

def papago():
    papago_translation(
        load_from="./result/ocr.txt",
        save_to="./result/english_ocr.txt",
        id=opt.PAPAGO_ID,
        pw=opt.PAPAGO_PW,
    )
    gen_text_to_image(load_from="./result/english_ocr.txt", warp_item=text_warp_items)

