import numpy as np
import torch
import torch.nn as nn

def _rfft2d_freqs(h, w):
    fy = np.fft.fftfreq(h)[:, None]
    fx = np.fft.fftfreq(w)[:w//2+(1 if w % 2 == 0 else 2)]
    return np.sqrt(fx*fx + fy*fy)


class PixelImage(nn.Module):
    def __init__(self, shape, sd=0.01):
        super(PixelImage, self).__init__()
        ch, h, w = shape
        self.pixels = torch.nn.Parameter(sd * torch.randn(1, ch, h, w))

    def forward(self):
        return self.pixels


class SpectralImage(nn.Module):
    def __init__(self, shape, sd=0.01, decay_power=1):
        super(SpectralImage, self).__init__()
        self.shape = shape
        ch, h, w = shape
        freqs = _rfft2d_freqs(h, w)
        fh, fw = freqs.shape
        self.decay_power = decay_power

        init_val = sd * torch.randn(ch, fh, fw, 2)
        spectrum_var = torch.nn.Parameter(init_val)
        self.spectrum_var = spectrum_var

        spertum_scale = 1.0 / np.maximum(
                freqs[..., None], 1.0 / max(h, w)) ** self.decay_power
        spertum_scale *= np.sqrt(w * h)
        spertum_scale = torch.FloatTensor(spertum_scale)
        self.register_buffer('spertum_scale', spertum_scale)


    def forward(self):
        ch, h, w = self.shape

        scaled_spectrum = self.spectrum_var * self.spertum_scale

        img = torch.irfft(scaled_spectrum, 3, onesided=True)

        img = img[:ch, :h, :w]
        return img.unsqueeze(0) / 4.


class CorrelateColors(torch.nn.Module):
    def __init__(self, jitter=0.01, sigmoid=False):
        super(CorrelateColors, self).__init__()
        self.jitter = jitter
        self.sigmoid = sigmoid
        color_correlation_svd_sqrt = torch.FloatTensor([
            [0.26, 0.09, 0.02],
            [0.27, 0.00, -0.05],
            [0.27, -0.09, 0.03]])

        max_norm_svd_sqrt = float(
            np.max(np.linalg.norm(color_correlation_svd_sqrt, axis=0)))

        self.register_buffer('color_correlation', color_correlation_svd_sqrt /
                max_norm_svd_sqrt)


    def forward(self, t):
        t_flat = t.view(t.shape[0], 3, -1).transpose(2, 1)
        t_flat = torch.matmul(t_flat, self.color_correlation.transpose(1, 0))
        t = t_flat.transpose(2, 1).view(t.shape)
        t += torch.randn_like(t) * self.jitter
        if self.sigmoid:
            return torch.sigmoid(t)
        else:
            return (t + 0.5).clamp(min=0, max=1)