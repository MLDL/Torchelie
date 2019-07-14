import torch
import torch.nn as nn
import torch.nn.functional as F
from .layers import Conv2d
from .batchnorm import ConditionalBN2d


def Conv2dNormReLU(in_ch, out_ch, ks, norm, leak=0):
    layer = [
            Conv2d(in_ch, out_ch, ks),
            norm,
    ]

    if leak != 0:
        layer.append(nn.LeakyReLU(leak))
    else:
        layer.append(nn.ReLU())

    nn.init.kaiming_normal_(layer[0].weight, a=leak)
    nn.init.constant_(layer[0].bias, 0)

    return nn.Sequential(*layer)


def Conv2dBNReLU(in_ch, out_ch, ks, leak=0):
    return Conv2dNormReLU(in_ch, out_ch, ks, nn.BatchNorm2d(out_ch), leak=leak)


class Conv2dCondBNReLU(nn.Module):
    def __init__(self, in_ch, out_ch, cond_ch, ks, leak=0):
        super(Conv2dCondBNReLU, self).__init__()
        self.conv = Conv2d(in_ch, out_ch, ks)
        self.cbn = ConditionalBN2d(out_ch, cond_ch)
        self.leak = leak

    def condition(self, z):
        self.cbn.condition(z)

    def forward(self, x, z=None):
        x = self.conv(x)
        x = self.cbn(x, z)
        if self.leak == 0:
            x = F.relu(x)
        else:
            x = F.leaky_relu(x, self.leak)
        return x
