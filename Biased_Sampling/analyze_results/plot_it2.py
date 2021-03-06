


import numpy as np

import plotly
import plotly.graph_objs as go

import pickle
from os.path import expanduser
home = expanduser("~")


means = []

datas = ['results_regular_10', 'results_regular_weighted_10', 'results_squared_10', 'results_BF_10', 'results_densities2_10'] 

for model in datas:

	with open(home + '/Documents/Bias_Sampling/'+ model + '.pkl', 'rb') as f:

		results = pickle.load(f)

	print len(results)

	print len(results[0][0])

	print results[0][0]



	model_means =[]
	stds = []
	# for data_split in range(len(results[0][0])):
	for data_split in range(2,3):

		temp = []
		for rep in range(len(results)):
			temp2 = []
			for bias in range(len(results[0])):
				temp2.append(results[rep][bias][data_split])
			temp.append(np.array(temp2))
		temp = np.array(temp)

		# for bias in range(len(temp.T)):
		aaa =  np.argsort(temp, axis=0)
		for i in range(len(temp.T)):
			temp.T[i] = temp.T[i][aaa.T[i]]
		
		temp2 = temp[5:]
		temp = temp2

		means.append(np.mean(temp, axis=0))
		stds.append(np.std(temp, axis=0))


	# model_means = np.array(model_means)
	# print model_means
	# fsaf
	# stds = np.array(stds)

	# means.append(model_means)

	# print means.shape
	# print stds.shape


	# print means

# fdsada

# means = np.array(means)
# print means.shape
# fdsaf



# training_acc = []
# for bias in range(len(results[0])):
# 	training_acc.append(results[0][bias][0][0])

# print training_acc

# training_acc = []
# for bias in range(len(results[0])):
# 	training_acc.append(results[1][bias][0][0])

# print training_acc

# training_acc = []
# for bias in range(len(results[0])):
# 	training_acc.append(results[2][bias][0][0])

# print training_acc

# print 

# valid_acc = []
# for bias in range(len(results[0])):
# 	valid_acc.append(results[0][bias][1][0])

# print valid_acc

# valid_acc = []
# for bias in range(len(results[0])):
# 	valid_acc.append(results[1][bias][1][0])

# print valid_acc

# valid_acc = []
# for bias in range(len(results[0])):
# 	valid_acc.append(results[2][bias][1][0])

# print valid_acc

# print 

# test_acc = []
# for bias in range(len(results[0])):
# 	test_acc.append(results[0][bias][2][0])

# print test_acc

# test_acc = []
# for bias in range(len(results[0])):
# 	test_acc.append(results[1][bias][2][0])

# print test_acc

# test_acc = []
# for bias in range(len(results[0])):
# 	test_acc.append(results[2][bias][2][0])

# print test_acc



# fsafsa

bias_values = [.5,.6,.7,.8,.9]


# trace0 = go.Scatter(
# 	x = [0,l],
# 	y = [0,l],
# 	mode = 'lines',
# 	name = 'Diagonal'
# )

data = [
	go.Scatter(
		x = bias_values,
		y = means[0],
		mode = 'lines',
		name = 'Regular',

	),
	go.Scatter(
		x = bias_values,
		y = means[1],
		mode = 'lines',
		name = 'Weighted',

	),
	go.Scatter(
		x = bias_values,
		y = means[2],
		mode = 'lines',
		name = 'Squared',

	),
	go.Scatter(
		x = bias_values,
		y = means[3],
		mode = 'lines',
		name = 'BF',

	),
	go.Scatter(
		x = bias_values,
		y = means[4],
		mode = 'lines',
		name = 'KDE',

	),
]

# data = [trace1,trace2,trace3]

layout = go.Layout(
	xaxis=dict(
		title='Bias'
		# range=[0,l],
		# type='linear',
		# dtick=20,
	),
	yaxis=dict(
		title='Accuracy',
		range=[0.4,1.],
		# type='linear',
		# dtick=20,
		# autorange=False,
		# showgrid=True,
		# zeroline=False,
		# showline=False,
		# autotick=True,
		# ticks='',
		# showticklabels=False
	),

	# width=950,
	# height=800
)


fig = go.Figure(data=data, layout=layout)
plotly.offline.plot(fig, filename=home + '/Documents/Bias_Sampling/accuracies_all.html')

print 'saved plot'
