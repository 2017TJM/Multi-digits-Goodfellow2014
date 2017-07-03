"""
Created on 2017.6.29 15:15
Author: Victoria
Email: wyvictoria1@gmail.com
"""
import time
import gc
import matplotlib.pyplot as plt
from load_data import generate_dataset, SVHNDataset
from net import MultiDigitsNet
from loss import loss
from accuracy import accu

import torch
from torch.autograd import Variable
import torch.optim as optim
import torch.nn.init as init
            
def train(data_aug, rand_num, batch_size, epochs, lr, momentum, log_interval, cuda, path, early_stopping=None):
    """
    Training model with data provided.
    Input:
        data_aug:
        rand_num:
        batch_size:
        epochs:
        lr:
        momentum:
        log_interval: how many batches to wait before logging training status.
        early_stopping: patient iters
        cuda: 
        path: path to save trained model
    """
    print "training..."
    print "cuda: ", cuda
    torch.manual_seed(1)
    if cuda:
        torch.cuda.manual_seed(1)
        
    train_data = generate_dataset(train="train", data_aug=data_aug, rand_num=rand_num)
    print "len of image: ", len(train_data[0])
    train_dataset = SVHNDataset(train_data[0], train_data[1]) 
    kwargs = {'num_workers': 1, 'pin_memory': True}  if cuda else {}
    train_loader = torch.utils.data.DataLoader(train_dataset, batch_size=batch_size, **kwargs)                

    model = MultiDigitsNet() 
    model.apply(weights_init)   
    model.train()   
    if cuda:
        model.cuda() #save all params to GPU
        
    #optimizer = optim.Adagrad(self.parameters(), lr=lr)#self.parameters() 
    optimizer = optim.SGD(model.parameters(), lr=lr, momentum=momentum)  
    
    loss_history = []  
    for epoch in range(epochs):
        for batch_idx, (data, target) in enumerate(train_loader):
            print lr
            data, target = Variable(data), Variable(target)
            if cuda:
                data, target = data.cuda(), target.cuda()
            data = data.float()    
            optimizer.zero_grad()
            output = model(data)
            losses = loss(output, target, cuda) 
            
            losses.backward()
            #print model.conv1.weight.data[0, 0]
            #print model.conv1.weight.grad.data[0, 0]    
            optimizer.step()
            
            accuracy = accu(output, target, cuda)
            if batch_idx % log_interval == 0:
                print "epoch: {} [{}/{}], loss: {}, accuracy: {}".format(epoch, batch_idx*len(data), len(train_loader.dataset), losses.data[0], accuracy.data[0])
            gc.collect()    
        if (epoch+1)%30==0:
            lr = lr * 0.9
            optimizer = optim.SGD(model.parameters(), lr=lr, momentum=momentum)
        loss_history.append(losses.data[0])    
    torch.save(model.state_dict(), path)     
    plt.figure()
    plt.plot(range(len(loss_history)), loss_history)  
    plt.savefig("figure/train_losses.png")  
        
def weights_init(m):
    if isinstance(m, torch.nn.Conv2d):
        init.kaiming_uniform(m.weight)
        init.constant(m.bias, 0.01)
    if isinstance(m, torch.nn.Linear):
        init.xavier_uniform(m.weight)
        init.constant(m.bias, 0.01)     
        
if __name__=="__main__":
    torch.manual_seed(1)
    torch.cuda.manual_seed(1)
    train_data = generate_dataset(train="test", data_aug=False)
    print "len of image: ", len(train_data[0])
    train_dataset = SVHNDataset(train_data[0], train_data[1]) 
    kwargs = {'num_workers': 1, 'pin_memory': True}  
    train_loader = torch.utils.data.DataLoader(train_dataset, batch_size=4, shuffle=True, **kwargs)                

    model = MultiDigitsNet()
    model.cuda()
    for batch_idx, (data, target) in enumerate(train_loader):
        data, target = data.cuda(), target.cuda()
        data, target = Variable(data), Variable(target)
        model.double()
        data = data.double()
        grad_check(model, data, target, cuda=True)    
        