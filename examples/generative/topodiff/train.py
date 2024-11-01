import torch 
from torch.optim import AdamW
from tqdm import trange
import numpy as np
import time, os 


import hydra 
from hydra.utils import to_absolute_path 
from omegaconf import DictConfig

from modulus.models.topodiff import TopoDiff, Diffusion
from modulus.models.topodiff import UNetEncoder
from modulus.launch.logging import (
    PythonLogger, 
    initialize_wandb
)
from utils import load_data_topodiff, load_data

@hydra.main(version_base="1.3", config_path="conf", config_name="config")
def main(cfg: DictConfig) -> None: 
    
    logger = PythonLogger("main") # General Python Logger 
    logger.log("Job start!")

    device = torch.device('cuda:0')
    model = TopoDiff(64, 6, 1, model_channels=128, attn_resolutions=[16,8]).to(device)
    diffusion = Diffusion(n_steps=1000,device=device)
    
    
    topologies = load_data(cfg.path_training_data_diffusion, cfg.prefix_topology_file, '.png', 0,30000)
    vfs_stress_strain = load_data(cfg.path_training_data_diffusion,cfg.prefix_pf_file, '.npy', 0,30000)
    load_imgs = load_data(cfg.path_training_data_diffusion, cfg.prefix_load_file, '.npy', 0,30000)
    
    batch_size = cfg.batch_size
    data = load_data_topodiff(
        topologies, vfs_stress_strain, load_imgs, batch_size= batch_size,deterministic=False
    )

    lr = cfg.lr
    optimizer = AdamW(model.parameters(), lr=lr)
    logger.log("Start training!")
    
    prog = trange(cfg.epochs)

    for step in prog: 
    
        tops, cons = next(data) 
    
        tops = tops.float().to(device) 
        cons = cons.float().to(device)
    
    
        losses = diffusion.train_loss(model, tops, cons) 
    
        optimizer.zero_grad()
        losses.backward() 
        optimizer.step() 
    
        if step % 100 == 0: 
            logger.info("epoch: %d, loss: %.5f" % (step, losses.item()))
        
    torch.save(model.state_dict(), cfg.model_path + "topodiff_model.pt")
    logger.info("Training completed!")


# ----------------------------------------------------------------------------

if __name__ == "__main__":
    main()

# ----------------------------------------------------------------------------