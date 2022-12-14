import file_utils
import imgproc
import opt
import torch
from text_recognition import ltr_utils


def test_net(model=None, mapper=None, spaces=None, load_from=None, save_to=None):
    device = "cuda" if opt.cuda else "cpu"
    with torch.no_grad():
        image_name_nums = []
        res = []
        img_lists, _, _, name_list = file_utils.get_files(load_from)
        for name in name_list:
            image_name_nums.append(name.split("_")[0])
        for k, in_path in enumerate(img_lists):
            # data pre-processing for passing net
            image = imgproc.loadImage(in_path)
            image = imgproc.cvtColorGray(image)
            image = imgproc.tranformToTensor(image, opt.RECOG_TRAIN_SIZE).unsqueeze(0)
            image = image.to(device)
            y = model(image)
            _, pred = torch.max(y.data, 1)
            res.append(mapper[0][pred])
        # method for saving result, MODE: file | stdout | all
        ltr_utils.display_stdout(
            chars=res,
            space=spaces,
            img_name=image_name_nums,
            MODE="file",
            save_to=save_to,
        )
