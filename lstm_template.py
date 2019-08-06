"""
Minimal character-level LSTM model. Written by Ngoc Quan Pham
Code structure borrowed from the Vanilla RNN model from Andreij Karparthy @karparthy.
BSD License
"""
import numpy as np
from random import uniform
import sys


# Since numpy doesn't have a function for sigmoid
# We implement it manually here
def sigmoid(x):
  return 1 / (1 + np.exp(-x))


# The derivative of the sigmoid function
def dsigmoid(y):
    return y * (1 - y)


# The derivative of the tanh function
def dtanh(x):
    return 1 - x*x


# The numerically stable softmax implementation
def softmax(x):
    e_x = np.exp(x - np.max(x))
    return e_x / e_x.sum()


# data I/O
data = open('data/input.txt', 'r').read() # should be simple plain text file
chars = list(set(data))
data_size, vocab_size = len(data), len(chars)
print('data has %d characters, %d unique.' % (data_size, vocab_size))
char_to_ix = { ch:i for i,ch in enumerate(chars) }
ix_to_char = { i:ch for i,ch in enumerate(chars) }
std = 0.1

option = sys.argv[1]

# hyperparameters
emb_size = 4
hidden_size = 32  # size of hidden layer of neurons
seq_length = 64  # number of steps to unroll the RNN for
learning_rate = 5e-2
max_updates = 500000

concat_size = emb_size + hidden_size

# model parameters
# char embedding parameters
Wex = np.random.randn(emb_size, vocab_size)*std # embedding layer

# LSTM parameters
Wf = np.random.randn(hidden_size, concat_size) * std # forget gate
Wi = np.random.randn(hidden_size, concat_size) * std # input gate
Wo = np.random.randn(hidden_size, concat_size) * std # output gate
Wc = np.random.randn(hidden_size, concat_size) * std # c term

bf = np.zeros((hidden_size, 1)) # forget bias
bi = np.zeros((hidden_size, 1)) # input bias
bo = np.zeros((hidden_size, 1)) # output bias
bc = np.zeros((hidden_size, 1)) # memory bias

# Output layer parameters
Why = np.random.randn(vocab_size, hidden_size)*0.01 # hidden to output
by = np.zeros((vocab_size, 1)) # output bias


def forward(inputs, targets, memory):
    """
    inputs,targets are both list of integers.
    hprev is Hx1 array of initial hidden state
    returns the loss, gradients on model parameters, and last hidden state
    """

    # The LSTM is different than the simple RNN that it has two memory cells
    # so here you need two different hidden layers
    hprev, cprev = memory

    # Here you should allocate some variables to store the activations during forward
    # One of them here is to store the hiddens and the cells
    hs, cs, xs, wes, zs, fs, ins, cands, otan, ogs, os, ps, ys = {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}

    hs[-1] = np.copy(hprev)
    cs[-1] = np.copy(cprev)

    loss = 0
    # forward pass
    for t in range(len(inputs)):
        xs[t] = np.zeros((vocab_size,1)) # encode in 1-of-k representation
        xs[t][inputs[t]] = 1

        # convert word indices to word embeddings
        wes[t] = np.dot(Wex, xs[t])

        # LSTM cell operation
        # first concatenate the input and h
        # This step is irregular (to save the amount of matrix multiplication we have to do)
        # I will refer to this vector as [h X]
        zs[t] = np.row_stack((hs[t-1], wes[t]))

        # YOUR IMPLEMENTATION should begin from here

        # compute the forget gate
        # f_gate = sigmoid (W_f \cdot [h X] + b_f)
        fs[t] = sigmoid((np.dot(Wf, zs[t]) + bf))

        # compute the input gate
        # i_gate = sigmoid (W_i \cdot [h X] + b_i)
        ins[t] = sigmoid((np.dot(Wi, zs[t]) + bi))

        # compute the candidate memory
        # \hat{c} = tanh (W_c \cdot [h X] + b_c])
        cands[t] = np.tanh(np.dot(Wc, zs[t]) + bc)

        # new memory: applying forget gate on the previous memory
        # and then adding the input gate on the candidate memory
        # c_new = f_gate * prev_c + i_gate * \hat{c}
        cs[t] = fs[t] * cs[t-1] + ins[t] * cands[t]

        # output gate
        # o_gate = sigmoid (Wo \cdot [h X] + b_o)
        ogs[t] = sigmoid(np.dot(Wo, zs[t]) + bo)

        # new hidden state for the LSTM
        # h = o_gate * tanh(c_new)
        otan[t] = np.tanh(cs[t])
        hs[t] = ogs[t] * otan[t]

        # DONE LSTM
        # output layer - softmax and cross-entropy loss
        # unnormalized log probabilities for next chars

        # o = Why \cdot h + by
        os[t] = np.dot(Why, hs[t]) + by

        # softmax for probabilities for next chars
        # p = softmax(o)
        ps[t] = softmax(os[t])


        # cross-entropy loss
        # cross entropy loss at time t:
        # create an one hot vector for the label y
        ys[t] = np.zeros((len(vocab_size), 1))
        ys[t][targets[t]] = 1

        # and then cross-entropy (see the elman-rnn file for the hint)
        loss_t = np.sum(-np.log(ps[t] * ys[t]))

        loss += loss_t

    # define your activations
    activations = hs, cs, xs, wes, zs, fs, ins, cands, ogs, os, ps, ys
    memory = (hs[len(inputs)-1], cs[len(inputs)-1])

    return loss, activations, memory


def backward(activations, clipping=True):

    # backward pass: compute gradients going backwards
    # Here we allocate memory for the gradients
    dWex, dWhy = np.zeros_like(Wex), np.zeros_like(Why)
    dby = np.zeros_like(by)
    dWf, dWi, dWc, dWo = np.zeros_like(Wf), np.zeros_like(Wi),np.zeros_like(Wc), np.zeros_like(Wo)
    dbf, dbi, dbc, dbo = np.zeros_like(bf), np.zeros_like(bi),np.zeros_like(bc), np.zeros_like(bo)

    hs, cs, xs, wes, zs, fs, ins, cands, otan,  ogs, os, ps, ys = activations

    # similar to the hidden states in the vanilla RNN
    # We need to initialize the gradients for these variables
    dhnext = np.zeros_like(hs[0])
    dcnext = np.zeros_like(cs[0])

    # back propagation through time starts here
    for t in reversed(range(len(inputs))):

        # IMPLEMENT YOUR BACKPROP HERE
        # refer to the file elman_rnn.py for more details

        # dE/do = prob - label
        do = ps[t] - ys[t]

        # dE/dWhy = dE/do * do/dWhy
        dWhy = np.dot(do, hs[t].T)
        dby = do

        dh = dhnext + np.dot(Why.T, do)

        dog = dhnext * otan[t]
        dWo = np.dot((dsigmoid(ogs[t]) * zs[t]).T, dog)
        dbo = dog * dsigmoid(ogs[t])
        dz = np.dot(Wo.T, dog)

        dotan = dh * ogs[t]
        dc = dcnext + dotan * dtanh(otan[t])

        df = dc * cs[t-1]
        dcnext = dc * fs[t]
        din = dc * cands[t]
        dcand = dc * ins[t]

        dWf = np.dot((dsigmoid(fs[t]) * zs[t]).T, df)
        dbf = df * dsigmoid(fs[t])
        dz += np.dot((dsigmoid(fs[t]) * Wf).T, df)

        dWi = np.dot((dsigmoid(ins[t]) * zs[t]).T, din)
        dbi = din * dsigmoid(ins[t])
        dz += np.dot((dsigmoid(ins[t]) * Wi).T, din)

        dWc = np.dot((dtanh(cands[t]) * zs[t]).T, dcand)
        dbc = dcand * dtanh(cands[t])
        dz += np.dot((dtanh(cands[t]) * Wc).T, dcand)

        length_h = dhnext.shape
        dhnext = dz[:length_h]
        dx = dz[length_h:]

        dWex = np.dot(dx, xs[t].T)


    if clipping:
        # clip to mitigate exploding gradients
        for dparam in [dWex, dWf, dWi, dWo, dWc, dbf, dbi, dbo, dbc, dWhy, dby]:
            np.clip(dparam, -5, 5, out=dparam)

    gradients = (dWex, dWf, dWi, dWo, dWc, dbf, dbi, dbo, dbc, dWhy, dby)

    return gradients


def sample(memory, seed_ix, n):
    """
    sample a sequence of integers from the model
    h is memory state, seed_ix is seed letter for first time step
    """
    h, c = memory
    x = np.zeros((vocab_size, 1))
    x[seed_ix] = 1
    generated_chars = []

    for t in range(n):
        # IMPLEMENT THE FORWARD FUNCTION ONE MORE TIME HERE
        # BUT YOU DON"T NEED TO STORE THE ACTIVATIONS

        # convert word indices to word embeddings
        we = np.dot(Wex, x[t])

        # LSTM cell operation
        # first concatenate the input and h
        # This step is irregular (to save the amount of matrix multiplication we have to do)
        # I will refer to this vector as [h X]
        z = np.row_stack((h, we))

        # YOUR IMPLEMENTATION should begin from here

        # compute the forget gate
        # f_gate = sigmoid (W_f \cdot [h X] + b_f)
        f = sigmoid((np.dot(Wf, z) + bf))

        # compute the input gate
        # i_gate = sigmoid (W_i \cdot [h X] + b_i)
        ing = sigmoid((np.dot(Wi, z) + bi))

        # compute the candidate memory
        # \hat{c} = tanh (W_c \cdot [h X] + b_c])
        cand = np.tanh(np.dot(Wc, z) + bc)

        # new memory: applying forget gate on the previous memory
        # and then adding the input gate on the candidate memory
        # c_new = f_gate * prev_c + i_gate * \hat{c}
        c = f * c + ing * cand

        # output gate
        # o_gate = sigmoid (Wo \cdot [h X] + b_o)
        og = sigmoid(np.dot(Wo, z) + bo)

        # new hidden state for the LSTM
        # h = o_gate * tanh(c_new)
        otan = np.tanh(c)
        h = og * otan

        # DONE LSTM
        # output layer - softmax and cross-entropy loss
        # unnormalized log probabilities for next chars

        # o = Why \cdot h + by
        o = np.dot(Why, h) + by

        # softmax for probabilities for next chars
        # p = softmax(o)
        p = softmax(o)

        # we randomly samples char from distribution, parametrized by p
        ix = np.random.multinomial(1, p.ravel())
        c = np.zeros((vocab_size, 1))

        for j in range(len(ix)):
            if ix[j] == 1:
                index = j
        c[index] = 1
        generated_chars.append(index)

    return generated_chars

if option == 'train':

    n, p = 0, 0
    n_updates = 0

    # momentum variables for Adagrad
    mWex, mWhy = np.zeros_like(Wex), np.zeros_like(Why)
    mby = np.zeros_like(by) 

    mWf, mWi, mWo, mWc = np.zeros_like(Wf), np.zeros_like(Wi), np.zeros_like(Wo), np.zeros_like(Wc)
    mbf, mbi, mbo, mbc = np.zeros_like(bf), np.zeros_like(bi), np.zeros_like(bo), np.zeros_like(bc)

    smooth_loss = -np.log(1.0/vocab_size)*seq_length # loss at iteration 0
    
    while True:
        # prepare inputs (we're sweeping from left to right in steps seq_length long)
        if p+seq_length+1 >= len(data) or n == 0:
            hprev = np.zeros((hidden_size,1)) # reset RNN memory
            cprev = np.zeros((hidden_size,1))
        p = 0 # go from start of data
        inputs = [char_to_ix[ch] for ch in data[p:p+seq_length]]
        targets = [char_to_ix[ch] for ch in data[p+1:p+seq_length+1]]

        # sample from the model now and then
        if n % 100 == 0:
            sample_ix = sample((hprev, cprev), inputs[0], 200)
            txt = ''.join(ix_to_char[ix] for ix in sample_ix)
            print ('----\n %s \n----' % (txt, ))

        # forward seq_length characters through the net and fetch gradient
        loss, activations, memory = forward(inputs, targets, (hprev, cprev))
        gradients = backward(activations)

        hprev, cprev = memory
        dWex, dWf, dWi, dWo, dWc, dbf, dbi, dbo, dbc, dWhy, dby = gradients
        smooth_loss = smooth_loss * 0.999 + loss * 0.001
        if n % 100 == 0: print ('iter %d, loss: %f' % (n, smooth_loss)) # print progress

        # perform parameter update with Adagrad
        for param, dparam, mem in zip([Wf, Wi, Wo, Wc, bf, bi, bo, bc, Wex, Why, by],
                                    [dWf, dWi, dWo, dWc, dbf, dbi, dbo, dbc, dWex, dWhy, dby],
                                    [mWf, mWi, mWo, mWc, mbf, mbi, mbo, mbc, mWex, mWhy, mby]):
            mem += dparam * dparam
            param += -learning_rate * dparam / np.sqrt(mem + 1e-8) # adagrad update

        p += seq_length # move data pointer
        n += 1 # iteration counter
        n_updates += 1
        if n_updates >= max_updates:
            break

elif option == 'gradcheck':

    p = 0
    inputs = [char_to_ix[ch] for ch in data[p:p+seq_length]]
    targets = [char_to_ix[ch] for ch in data[p+1:p+seq_length+1]]

    delta = 0.001

    hprev = np.zeros((hidden_size, 1))
    cprev = np.zeros((hidden_size, 1))

    memory = (hprev, cprev)

    loss, activations, _ = forward(inputs, targets, memory)
    gradients = backward(activations, clipping=False)
    dWex, dWf, dWi, dWo, dWc, dbf, dbi, dbo, dbc, dWhy, dby = gradients

    for weight, grad, name in zip([Wf, Wi, Wo, Wc, bf, bi, bo, bc, Wex, Why, by], 
                                   [dWf, dWi, dWo, dWc, dbf, dbi, dbo, dbc, dWex    , dWhy, dby],
                                   ['Wf', 'Wi', 'Wo', 'Wc', 'bf', 'bi', 'bo', 'bc', 'Wex', 'Why', 'by']):

        str_ = ("Dimensions dont match between weight and gradient %s and %s." % (weight.shape, grad.shape))
        assert(weight.shape == grad.shape), str_

        print(name)
        for i in range(weight.size):
      
            # evaluate cost at [x + delta] and [x - delta]
            w = weight.flat[i]
            weight.flat[i] = w + delta
            loss_positive, _, _ = forward(inputs, targets, memory)
            weight.flat[i] = w - delta
            loss_negative, _, _ = forward(inputs, targets, memory)
            weight.flat[i] = w  # reset old value for this parameter

            grad_analytic = grad.flat[i]
            grad_numerical = (loss_positive - loss_negative) / ( 2 * delta )

            # compare the relative error between analytical and numerical gradients
            rel_error = abs(grad_analytic - grad_numerical) / abs(grad_numerical + grad_analytic)

            if rel_error > 0.01:
                print ('WARNING %f, %f => %e ' % (grad_numerical, grad_analytic, rel_error))