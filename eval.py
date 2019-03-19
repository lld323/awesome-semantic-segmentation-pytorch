from __future__ import print_function

import os
import argparse

import torch
import torch.utils.data as data

from data_loader.transforms import TestTransform
from data_loader.voc import VOCSegmentation
from models.model_zoo import get_model
from utils.score import SegmentationMetric
from utils.visualize import get_color_pallete

parser = argparse.ArgumentParser(
    description='Semantic Segmentation Evaluation')
parser.add_argument('--model', type=str, default='fcn32s_vgg16',
                    help='model name (default: fcn32)')
parser.add_argument('--save-folder', default='./weights',
                    help='Directory for saving checkpoint models')
parser.add_argument('--dataset_root', default='./datasets',
                    help='Dataset root directory path')
parser.add_argument('--dataset', default='VOC2012', choices=['VOC2007', 'VOC2012'],
                    type=str, help='VOC2007 or VOC2012')
parser.add_argument('--num_classes', default=21, type=int,
                    help='Number of classes.')
parser.add_argument('--save-result', default=False,
                    help='save the predict')
parser.add_argument('--outdir', default='./eval', type=str,
                    help='path to save the predict result')
args = parser.parse_args()


def eval(config):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    # output folder
    if config.save_result:
        if not os.path.exists(config.outdir):
            os.makedirs(config.outdir)
    # image transform
    input_transform = TestTransform([.485, .456, .406], [.229, .224, .225])

    # dataset and dataloader
    test_dataset = VOCSegmentation(root=args.dataset_root,
                                   year=args.dataset[3:],
                                   image_set='val',
                                   transform=input_transform)

    test_loader = data.DataLoader(dataset=test_dataset,
                                  batch_size=1,
                                  shuffle=False)

    # create network
    model = get_model(config.model, num_classes=config.num_classes).to(device)
    model.load_state_dict(torch.load(os.path.join(config.save_folder, config.model + '_' + config.dataset + '.pth'),
                                     map_location='cpu'))
    print('Finished loading model!')

    metric = SegmentationMetric(config.num_classes)

    model.eval()
    for i, (image, label) in enumerate(test_loader):
        image = image.to(device)

        outputs = model(image)

        pred = torch.argmax(outputs, 1)
        pred = pred.data.numpy()
        label = label.numpy()

        metric.update(pred, label)
        pixAcc, mIoU = metric.get()
        print('pixAcc: %.3f%%, mIoU: %.3f%%' % (pixAcc * 100, mIoU * 100))

        if config.save_result:
            predict = pred.squeeze(0)
            mask = get_color_pallete(predict, config.dataset)
            mask.save(os.path.join(config.outdir, 'seg_' + str(i) + '_.png'))


if __name__ == '__main__':
    print('Testing model: ', args.model)
    eval(args)
