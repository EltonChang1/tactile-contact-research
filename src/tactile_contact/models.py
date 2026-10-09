"""Numerical starter code from the user-provided refined implementation guide."""


import torch
from torch import nn

class ContactPredictor(nn.Module):
    def __init__(self, support_dim=101, output_dim=96, latent_dim=16):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(support_dim, 128), nn.ReLU(),
            nn.Linear(128, 64), nn.ReLU(),
            nn.Linear(64, latent_dim),
        )
        self.predictor = nn.Sequential(
            nn.Linear(latent_dim + 4 + 1, 128), nn.ReLU(),
            nn.Linear(128, 64), nn.ReLU(),
            nn.Linear(64, output_dim),
        )

    def forward(self, support, support_mask, query_condition):
        if support.ndim != 3 or support.shape[-1] != self.encoder[0].in_features:
            raise ValueError("Expected [batch, slots, support_dim]")
        if support_mask.shape != support.shape[:2]:
            raise ValueError("Support mask must match batch and slots")
        if query_condition.shape != (support.shape[0], 4):
            raise ValueError("Expected four query-condition features per episode")
        if not torch.all((support_mask == 0) | (support_mask == 1)):
            raise ValueError("Support mask must contain only zero or one")
        if not torch.isfinite(support).all() or not torch.isfinite(query_condition).all():
            raise ValueError("Inputs must be finite; use finite zero padding")
        mask = support_mask.to(device=support.device, dtype=support.dtype)
        count = mask.sum(dim=1, keepdim=True)
        if torch.any(count <= 0):
            raise ValueError("Every episode needs at least one support contact")
        encoded = self.encoder(support)
        z = (encoded * mask.unsqueeze(-1)).sum(dim=1) / count
        context = torch.cat([z, query_condition, count / 2.0], dim=1)
        return self.predictor(context), z
