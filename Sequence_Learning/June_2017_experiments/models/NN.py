

#Neural Network

import tensorflow as tf
import numpy as np


class NN(object):

    def __init__(self, network_architecture, act_func, batch_size):
        
        #Model hyperparameters
        self.act_func = act_func
        self.input_size = network_architecture[0]
        self.output_size = network_architecture[-1]
        self.net = network_architecture
        self.batch_size = batch_size

        self.Ws = self.init_weights()




    def init_weights(self):

        Ws = []

        for layer_i in range(len(self.net)-1):

            input_size_i = self.net[layer_i]+1 #plus 1 for bias
            output_size_i = self.net[layer_i+1] #plus 1 because we want layer i+1

            #Define variables [IS,OS]
            Ws.append(tf.Variable(xavier_init(input_size_i, output_size_i)))

        return Ws





    def weight_decay(self):

        l2 = 0
        for weight_layer in self.Ws:

            l2 += tf.reduce_sum(tf.square(weight_layer))

        return l2




    def feedforward(self, x):
        '''
        x: [B,X]
        y_hat: [B,O]
        '''

        net = self.net

        #[B,X]
        cur_val = x

        for layer_i in range(len(net)-1):

            W = self.Ws[layer_i]

            #Concat 1 to input for biases  [B,P,X]->[B,P,X+1]
            cur_val = tf.concat([cur_val,tf.ones([self.batch_size, 1])], axis=1)

            if layer_i != len(net)-2:
                cur_val = self.act_func(tf.matmul(cur_val, W))
            else:
                cur_val = tf.matmul(cur_val, W)

        return cur_val















