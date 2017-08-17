







import time






import numpy as np
import pickle
from os.path import expanduser
home = expanduser("~")

# import matplotlib.pyplot as plt


import torch
from torch.autograd import Variable
import torch.utils.data
import torch.optim as optim
import torch.nn as nn
import torch.nn.functional as F

from utils import lognormal2 as lognormal
from utils import log_bernoulli

from bnn_pytorch import BNN





def train(model, train_x, train_y, valid_x=[], valid_y=[], 
            path_to_load_variables='', path_to_save_variables='', 
            epochs=10, batch_size=20, display_epoch=2, k=1):
    

    if path_to_load_variables != '':
        model.load_state_dict(torch.load(path_to_load_variables))
        print 'loaded variables ' + path_to_load_variables

    traindata = torch.utils.data.TensorDataset(train_x, train_y)
    train_loader = torch.utils.data.DataLoader(traindata, batch_size=batch_size, shuffle=True)

    validdata = torch.utils.data.TensorDataset(valid_x, valid_y)
    valid_loader = torch.utils.data.DataLoader(validdata, batch_size=batch_size, shuffle=False)


    optimizer = optim.Adam(model.parameters(), lr=.001)

    if torch.cuda.is_available():
        print 'GPU available, loading cuda'
        model.cuda()



    times_not_beaten_best = 0
    finished = 0
    best_valid_elbo = -1
    for epoch in range(1, epochs + 1):

        for batch_idx, (data, target) in enumerate(train_loader):

            if torch.cuda.is_available():
                data = Variable(data.cuda())#, Variable(target)#.type(torch.cuda.LongTensor)
            else:
                data = Variable(data)#, Variable(target)

            optimizer.zero_grad()
            elbo, logpx, logpz, logqz, logpW, logqW = model.forward(data, k=k, s=1)
            loss = -(elbo)
            loss.backward()
            optimizer.step()

            if epoch%display_epoch==0 and batch_idx == 0:
                print 'Train Epoch: {}/{}'.format(epoch, epochs), \
                    'Loss:{:.3f}'.format(loss.data[0]), \
                    'logpx:{:.3f}'.format(logpx.data[0]), \
                    'logpz:{:.3f}'.format(logpz.data[0]), \
                    'logqz:{:.3f}'.format(logqz.data[0]), \
                    'logpW:{:.3f}'.format(logpW.data[0]), \
                    'logqW:{:.3f}'.format(logqW.data[0])



                if len(valid_x) > 0:

                    valid_elbos = []
                    for batch_idx_valid, (data, target) in enumerate(valid_loader):

                        if torch.cuda.is_available():
                            data = Variable(data.cuda())#, Variable(target)#.type(torch.cuda.LongTensor)
                        else:
                            data = Variable(data)#, Variable(target)

                        valid_elbo = model.predictive_elbo(data, k=20, s=3)
                        valid_elbos.append(valid_elbo.data[0])

                    current_valid_elbo = np.mean(valid_elbos)
                    

                    if current_valid_elbo > best_valid_elbo or best_valid_elbo == -1:

                        best_valid_elbo = current_valid_elbo
                        times_not_beaten_best = 0
                        #save model
                        if path_to_save_variables != '':
                            torch.save(model.state_dict(), path_to_save_variables)
                            print 'validation ' + str(current_valid_elbo) + ' Saved variables to ' + path_to_save_variables
                    else:
                        times_not_beaten_best += 1
                        print 'validation ' + str(current_valid_elbo), times_not_beaten_best
                        if times_not_beaten_best > 2:
                            finished = 1
                            break

        if finished ==1:
            break

    return best_valid_elbo




# def test(model, data_x, path_to_load_variables='', batch_size=20, display_epoch=4, k=10):
    

#     if path_to_load_variables != '':
#         model.load_state_dict(torch.load(path_to_load_variables))
#         print 'loaded variables ' + path_to_load_variables

#     elbos = []
#     data_index= 0
#     for i in range(len(data_x)/ batch_size):

#         batch = data_x[data_index:data_index+batch_size]
#         data_index += batch_size

#         elbo, logpx, logpz, logqz = model(Variable(batch), k=k)
#         elbos.append(elbo.data[0])

#         if i%display_epoch==0:
#             print i,len(data_x)/ batch_size, elbo.data[0]

#     return np.mean(elbos)


# self.module_list = nn.ModuleList()
# for i in range(5):
#     self.module_list += make_sequence()



class BVAE(nn.Module):
    def __init__(self, qW_weight):
        super(BVAE, self).__init__()

        if torch.cuda.is_available():
            self.dtype = torch.cuda.FloatTensor
        else:
            self.dtype = torch.FloatTensor
            
        self.qW_weight = qW_weight

        self.z_size = 2
        self.input_size = 784

        #Encoder
        self.fc1 = nn.Linear(self.input_size, 200)
        self.fc2 = nn.Linear(200, self.z_size*2)
        #Decoder
        self.decoder = BNN([self.z_size, 200, 784], [F.relu, F.relu])

    def encode(self, x):
        h1 = F.relu(self.fc1(x))
        h2 = self.fc2(h1)
        mean = h2[:,:self.z_size]
        logvar = h2[:,self.z_size:]
        return mean, logvar

    def sample_z(self, mu, logvar, k):
        eps = Variable(torch.FloatTensor(k, self.B, self.z_size).normal_().type(self.dtype)) #[P,B,Z]
        z = eps.mul(torch.exp(.5*logvar)) + mu  #[P,B,Z]
        logpz = lognormal(z, Variable(torch.zeros(self.B, self.z_size).type(self.dtype)), 
                            Variable(torch.zeros(self.B, self.z_size)).type(self.dtype))  #[P,B]

        logqz = lognormal(z, mu, logvar)
        return z, logpz, logqz

    def sample_W(self):

        Ws, log_p_W_sum, log_q_W_sum = self.decoder.sample_weights()
        return Ws, log_p_W_sum, log_q_W_sum


    def decode(self, Ws, z):
        k = z.size()[0]
        z = z.view(-1, self.z_size)
        x = self.decoder.forward(Ws, z)
        x = x.view(k, self.B, self.input_size)
        return x


    def forward(self, x, k, s):

        self.B = x.size()[0] #batch size
        # self.k = k  #number of z samples aka particles P
        # self.s = s  #number of W samples

        elbo1s = []
        logprobs = [[] for _ in range(5)]
        for i in range(s):

            Ws, logpW, logqW = self.sample_W()  #_ , [1], [1]

            mu, logvar = self.encode(x)  #[B,Z]
            z, logpz, logqz = self.sample_z(mu, logvar, k=k) #[P,B,Z], [P,B]

            x_hat = self.decode(Ws, z) #[P,B,X]
            logpx = log_bernoulli(x_hat, x)  #[P,B]

            elbo = logpx + logpz - logqz #[P,B]
            if k>1:
                max_ = torch.max(elbo, 0)[0] #[B]
                elbo1 = torch.log(torch.mean(torch.exp(elbo - max_), 0)) + max_ #[B]
            elbo = elbo + (logpW*.000001) - (logqW*self.qW_weight) #[B], logp(x|W)p(w)/q(w)
            elbo1s.append(elbo)
            logprobs[0].append(torch.mean(logpx))
            logprobs[1].append(torch.mean(logpz))
            logprobs[2].append(torch.mean(logqz))
            logprobs[3].append(torch.mean(logpW))
            logprobs[4].append(torch.mean(logqW))




        elbo1s = torch.stack(elbo1s) #[S,B]
        if s>1:
            max_ = torch.max(elbo1s, 0)[0] #[B]
            elbo1 = torch.log(torch.mean(torch.exp(elbo1s - max_), 0)) + max_ #[B]            

        elbo = torch.mean(elbo1s) #[1]

        #for printing
        # logpx = torch.mean(logpx)
        # logpz = torch.mean(logpz)
        # logqz = torch.mean(logqz)
        # self.x_hat_sigmoid = F.sigmoid(x_hat)

        logprobs2 = [torch.mean(torch.stack(aa)) for aa in logprobs]

        return elbo, logprobs2[0], logprobs2[1], logprobs2[2], logprobs2[3], logprobs2[4]



    def predictive_elbo(self, x, k, s):
        # No pW or qW

        self.B = x.size()[0] #batch size
        # self.k = k  #number of z samples aka particles P
        # self.s = s  #number of W samples

        elbo1s = []
        for i in range(s):

            Ws, logpW, logqW = self.sample_W()  #_ , [1], [1]

            mu, logvar = self.encode(x)  #[B,Z]
            z, logpz, logqz = self.sample_z(mu, logvar, k=k) #[P,B,Z], [P,B]

            x_hat = self.decode(Ws, z) #[P,B,X]
            logpx = log_bernoulli(x_hat, x)  #[P,B]

            elbo = logpx + logpz - logqz #[P,B]
            if k>1:
                max_ = torch.max(elbo, 0)[0] #[B]
                elbo = torch.log(torch.mean(torch.exp(elbo - max_), 0)) + max_ #[B]
            # elbo1 = elbo1 #+ (logpW - logqW)*.00000001 #[B], logp(x|W)p(w)/q(w)
            elbo1s.append(elbo)

        elbo1s = torch.stack(elbo1s) #[S,B]
        if s>1:
            max_ = torch.max(elbo1s, 0)[0] #[B]
            elbo1 = torch.log(torch.mean(torch.exp(elbo1s - max_), 0)) + max_ #[B]            

        elbo = torch.mean(elbo1s) #[1]
        return elbo#, logprobs2[0], logprobs2[1], logprobs2[2], logprobs2[3], logprobs2[4]






print 'Loading data'
with open(home+'/Documents/MNIST_data/mnist.pkl','rb') as f:
    mnist_data = pickle.load(f)

train_x = mnist_data[0][0]
train_y = mnist_data[0][1]
valid_x = mnist_data[1][0]
valid_y = mnist_data[1][1]
test_x = mnist_data[2][0]
test_y = mnist_data[2][1]

train_x = torch.from_numpy(train_x)
train_y = torch.from_numpy(train_y)
valid_x = torch.from_numpy(valid_x)
valid_y = torch.from_numpy(valid_y)
test_x = torch.from_numpy(test_x)
test_y = torch.from_numpy(test_y)

print train_x.shape
print test_x.shape
print train_y.shape

qW_weights = [.000000001, .000001, .0001]
qW_weight_scores = [0,0,0]

for i in range(len(qW_weights)):

    model = BVAE(qW_weights[i])

    path_to_load_variables=''
    # path_to_load_variables=home+'/Documents/tmp/pytorch_bvae.pt'
    path_to_save_variables=home+'/Documents/tmp/pytorch_bvae'+str(i)+'.pt'
    # path_to_save_variables=''

    best_valid_score = train(model=model, train_x=train_x, train_y=train_y, valid_x=valid_x, valid_y=valid_y, 
                path_to_load_variables=path_to_load_variables, 
                path_to_save_variables=path_to_save_variables, 
                epochs=300, batch_size=100, display_epoch=2, k=1)

    qW_weight_scores[i] = best_valid_score
    print 'scores', qW_weight_scores

# print test(model=model, data_x=test_x, path_to_load_variables='', 
#             batch_size=20, display_epoch=100, k=1000)

print 'Done.'



#Reulls scores 
#[-148.14850021362304, -146.89197433471679, -152.84082611083986]
# qW_weights = [.000000001, .000001, .0001]


# training elbo: 
# 1: 116/300 Loss:153.175 logpx:-146.690 logpz:-1.800 logqz:4.666 logpW:-18463.871 logqW:616290.312
# 2: 104/300 Loss:148.872 logpx:-142.097 logpz:-1.209 logqz:5.088 logpW:-26428.045 logqW:452337.312
# 3: 94/300 Loss:134.635 logpx:-149.966 logpz:-0.951 logqz:4.851 logpW:-4931132.500 logqW:-260631.391


# next: 2 figues, 1) the true posteriors 2) the image uncertainty. 








