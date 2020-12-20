from Evaluation import Evaluation
from Evaluation import EvaluationMethods
import time
import settings
from MySearcher import MySearcher
import numpy as np
from IndexRepository import IndexRepository
import matplotlib.pyplot as plt

index = IndexRepository(settings.index_instance_location, settings.mongo_database_location, settings.database_name)
field_params = np.array([0.33, 0.33, 0.0, 0.0, 0.34])
smoothing = np.arange(0,1.05,0.05)
x = [1,2,3]
y = [[3,4],[5,4],[6,3]]

#for i in smoothing:
#    s = np.array([i, i, 0.0, 0.0, i])
#    eval = Evaluation(EvaluationMethods.NDCG.value, s, field_params, index, '2000 ')
#    x.append(i)
#    y.append(eval.evaluate())
#    print(i)

x = np.array(x)
y = np.array(y)
plt.figure()
p1, = plt.plot(x,y.T[0], label='R')
p2, = plt.plot(x,y.T[1], label='R and PR')
plt.legend(handles=[p1,p2])
plt.xlabel('Smoothing value')
plt.ylabel('NDCG')
plt.title('Normalized Discounted Culumative Gain with different smoothing parameters')
plt.savefig('mrr.png')
plt.show()




