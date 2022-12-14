import cv2
import numpy as np
import object_detection.cut_utils as cut_utils
import opt


def test_opencv(image=None, demo=None, bg=None, size=None):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    #  threshold as background type
    if bg == "black":
        _, thresh = cv2.threshold(gray, 0.1, 255, 0)
    elif bg == "white":
        _, thresh = cv2.threshold(gray, opt.THRESH_EXTENT, 255, cv2.THRESH_BINARY)
        thresh = cv2.bitwise_not(thresh)
    else:
        _, thresh = cv2.threshold(gray, opt.THRESH_EXTENT, 255, cv2.THRESH_BINARY)
        thresh = cv2.bitwise_not(thresh)

    kernel = np.ones((3, 3), np.uint8)
    if bg == "black":
        thresh = cv2.morphologyEx(
            thresh, cv2.MORPH_OPEN, kernel, iterations=opt.OPENING_ITER_NUM
        )

    if bg == "white" or bg == "black":
        thresh = cv2.dilate(thresh, kernel, iterations=opt.DILATE_ITER_NUM)
    if bg == "classic":
        thresh = cv2.copyMakeBorder(
            thresh[:, 10:-10],
            0,
            0,
            10,
            10,
            borderType=cv2.BORDER_CONSTANT,
            value=[0, 0, 0],
        )
    contours, _ = cv2.findContours(thresh, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)

    hull_lists = []
    img_h, img_w, _ = np.array(image).shape
    canvas = np.zeros((img_h, img_w), dtype=np.uint8)
    for i in contours:
        area = cv2.contourArea(i)
        hull = cv2.convexHull(i, clockwise=True)
        if bg == "white" and area < size:
            continue  # size filtering for cut candidate
        hull_lists.append(hull)
    new_contours = cut_utils.remove_noise_convexhull(
        canvas, hull_lists
    )  # remove all inner contours
    cuts, dets_cut = cut_utils.alpha_blend_cut(
        image, new_contours
    )  # add transparent attribute by alpha-blending
    vis_img, rect_cuts = cut_utils.draw_cut_convexhull(
        image, demo, new_contours
    )  # draw convexHull

    return vis_img, cuts
