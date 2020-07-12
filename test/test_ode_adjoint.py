import torch.utils.data as data
import torchdyn; from torchdyn.models import *; from torchdyn.datasets import *
import torch ; import torch.nn as nn
from torch.distributions import *

def test_adjoint_autograd():
    """Compare ODE Adjoint vs Autograd gradients, s := [0, 1], adaptive-step"""
    d = ToyDataset()
    X, yn = d.generate(n_samples=512, dataset_type='moons', noise=.4)
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    X_train = torch.Tensor(X).to(device)
    y_train = torch.LongTensor(yn.long()).to(device)
    train = data.TensorDataset(X_train, y_train)
    trainloader = data.DataLoader(train, batch_size=len(X), shuffle=False)    

    f = nn.Sequential(
            nn.Linear(2, 64),
            nn.Tanh(), 
            nn.Linear(64, 2))
    
    model = NeuralDE(f, solver='dopri5', sensitivity='adjoint', atol=1e-6, rtol=1e-6).to(device)
    x, y = next(iter(trainloader)) 
    # adjoint gradients
    y_hat = model(x)   
    loss = nn.CrossEntropyLoss()(y_hat, y)
    loss.backward()
    adj_grad = torch.cat([p.grad.flatten() for p in model.parameters()])
    # autograd gradients
    model.zero_grad()
    model.sensitivity= 'autograd'
    y_hat = model(x)   
    loss = nn.CrossEntropyLoss()(y_hat, y)
    loss.backward()
    bp_grad = torch.cat([p.grad.flatten() for p in model.parameters()])
    assert (torch.abs(bp_grad - adj_grad) <= 1e-4).all()
    
if __name__ == '__main__':
    print(f'Testing regular CNF with autograd trace...')
    test_adjoint_autograd()