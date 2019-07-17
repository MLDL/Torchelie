import torch

class PixelNorm(torch.nn.Module):
    def forward(self, x):
        return x / (x.mean(dim=1, keepdim=True).sqrt() + 1e-8)
