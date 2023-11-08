import cv2 as cv
from pandas import DataFrame, read_csv
import numpy as np
import json
from pathlib import Path
import torch
import torch.nn as nn
import torchvision.models as models
from os.path import isfile
import matplotlib.pyplot as plt

from PIL import Image
from typing import Union, List, Tuple, Optional
import random
from torch import Tensor

import torchvision.transforms as transforms
import torchvision.transforms.functional as F
from torchvision.transforms import InterpolationMode


class Compose(object):
    """Apply a list of semantic segmentation transforms to an image and label
    mask.

    Args:
        transforms: Transforms to apply to image and mask in order.

    Attributes:
        transforms (list): List of transforms.
    
    """
    def __init__(self, transforms: list):
        self.transforms = transforms
        
    def __call__(self, image: Image):
        """
        Args:
            image: Image.
            mask: Label mask.

        Returns:
            Image and mask after transformations.
        
        """
        for transform in self.transforms:
            image = transform(image)
            
        return image


class ToTensor(object):
    """Transform image and mask to tensor.     
    
    """
    def __call__(self, image):
        """    
        Args:
            image: Image.
            mask: Label mask.

        Returns:
            Image and mask as tensors.
        
        """
        # convert image to tensor
        transform = transforms.ToTensor()
        image = transform(image)
        
        return image


class Normalize(object):
    """Color normalize an image, label mask is passed but not normalized.
    
    Args:
        mean: RGB mean.
        std: RGB standard deviation.
        
    Attributes:
        transform (torchvision.transforms.Normalize): Normailze transform.
        
    """
    def __init__(self, mean: [int, int, int], std: [int, int, int]):
        self.transform = transforms.Normalize(mean=mean, std=std)
        
    def __call__(self, image):
        """
        Args:
            image: Image.
            mask: Label mask.

        Returns:
            Image and mask as tensors.
        
        """
        return self.transform(image)


class Resize(object):
    """Resize input image or tensor and its label mask. Label mask is always
    resized with nearest exact interpolation to keep only unique labels.
    
    Args:
        size: Size to resize input to.
        interpolation: Interpolation method for image, see docstring for 
            torchvision.transforms.Resize for details.
        antialias: Apply antialias to the image, see docstring for 
            torchvision.transforms.Resize for details.

    Attributes:
        transform (torchvision.transforms.Resize): Transform applied to image.
        label_transform (torchvision.transforms.Resize): Transform applied to
            label masks.
            
    """
    def __init__(
        self, 
        size: int , 
        interpolation: InterpolationMode = InterpolationMode.BILINEAR, 
        antialias: bool = True
    ):
        self.transform = transforms.Resize(size, interpolation=interpolation,
                                           antialias=antialias)
        self.label_transform = transforms.Resize(
            size, interpolation=InterpolationMode.NEAREST_EXACT
        )

    def __call__(self, image):
        """
        Args:
            image: Image.
            mask: Label mask.

        Returns:
            Image and mask as tensors.

        """
        return self.transform(image)


size = 512

norm_mean = [0.485, 0.456, 0.406]
norm_std = [0.229, 0.224, 0.225]

val_transforms = Compose([
    ToTensor(),
    Resize(size),
    Normalize(mean=norm_mean, std=norm_std)
])

class uNetResNet(nn.Module):
    def __init__(self, in_channels, out_channels, pretrained=True):
        super(uNetResNet, self).__init__()   
        # Load the ResNet-34 model
        resnet = models.resnet34(pretrained=pretrained)        
        self.encoder = nn.Sequential(
            resnet.conv1,
            resnet.bn1,
            resnet.relu,
            resnet.layer1,
            resnet.layer2,
            resnet.layer3,
            resnet.layer4
        )
        self.decoder = nn.Sequential(
            nn.Conv2d(512, 256, kernel_size=1),  
            nn.ConvTranspose2d(256, 128, kernel_size=4, stride=2, padding=1),  
            nn.ReLU(),
            nn.Conv2d(128, 128, kernel_size=3, padding=1),
            nn.ConvTranspose2d(128, 64, kernel_size=4, stride=2, padding=1),  
            nn.ReLU(),
            nn.Conv2d(64, 64, kernel_size=3, padding=1),
            nn.ConvTranspose2d(64, out_channels, kernel_size=4, stride=2, padding=1)  
        )
    
    def forward(self, x):
        x1 = self.encoder(x)
        x2 = self.decoder(x1)
        return x2

class uNet(nn.Module):
    def __init__(self, in_channels, out_channels):
        super(uNet, self).__init__()

        self.encoder = nn.Sequential(
            nn.Conv2d(in_channels, 64, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(64, 64, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2)
        )

        self.bottleneck = nn.Sequential(
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(128, 128, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2)
        )

        self.decoder = nn.Sequential(
            nn.Conv2d(128, 64, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(64, 64, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.ConvTranspose2d(64, out_channels, kernel_size=2, stride=2)
        )

    def forward(self, x):
        enc1 = self.encoder(x)
        bottle = self.bottleneck(enc1)
        dec1 = self.decoder(bottle)
        return dec1
