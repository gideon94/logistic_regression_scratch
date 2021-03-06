import numpy as np
import pandas as pd 
from math import ceil
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix 
from sklearn.preprocessing import LabelBinarizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score,roc_auc_score,roc_curve,auc

#Loading Data
hazel_df = pd.read_csv("hazelnuts.txt",sep="\t",header=None)
hazel_df = hazel_df.transpose()
hazel_df.columns = ["sample_id","length","width","thickness","surface_area","mass","compactness",
                    "hardness","shell_top_radius","water_content","carbohydrate_content","variety"]
hazel_df.head()

#Feature Selection
all_features = hazel_df.drop(["variety","sample_id"],axis=1) 
target_feature = hazel_df["variety"]
all_features.head()

#Normalizing values
from sklearn import preprocessing
x = all_features.values.astype(float) #returns a numpy array of type float
min_max_scaler = preprocessing.MinMaxScaler()
x_scaled = min_max_scaler.fit_transform(x)
scaled_features = pd.DataFrame(x_scaled)
scaled_features.head()

#Preprocessing dataset for algorithm
Y=list()
X=np.array(scaled_features)
y=np.array(target_feature)
label_dict = {'c_avellana':0, 'c_americana':1, 'c_cornuta':2}
_label_dict = {0 :'c_avellana' , 1 :'c_americana' , 2 :'c_cornuta'}
for i in y:
    Y.append(label_dict[i])
y=np.array(Y,dtype=int)
y_unique = np.unique(y) 

#Sigmoid function
def sigmoid(z):
    return 1.0 / (1 + np.exp(-z))
    
#Cost function
def costFunc(theta, X, y, lr = 0.001):
    h = sigmoid(X.dot(theta))
    r = (lr/(2 * len(y))) * np.sum(theta**2)
    return (1 / len(y)) * (-y.T.dot(np.log(h)) - (1 - y).T.dot(np.log(1 - h))) + r
    
#Gradient descent function
def gradientFunc(theta, X, y, lr = 0.001):
    m, n = X.shape
    theta = theta.reshape((n, 1))
    y = y.reshape((m, 1))
    h = sigmoid(X.dot(theta))
    r = lr * theta /m
    return ((1 / m) * X.T.dot(h - y)) + r

#Modelling logistic regression
def logisticRegression(X, y,theta,num_iter):
    #Finding best theta
    for i in range(num_iter):
        lineq = np.dot(X, theta)
        h = sigmoid(lineq)
        #Calculating cost function of each class
        cost = costFunc(theta, X,y) 
        cost = cost.sum(axis = 0)
        #Applying gradient descent to find new theta
        delta = gradientFunc(theta,X,y) 
        theta = theta - delta    
    return theta 

#Model training
score = list()
missclass =0 

#KFold cross validation
for fold in range(10):
    X_train,X_test,y_train,y_test = train_test_split(X,y,test_size=0.33)
    #OneVsRest
    i,k,n= 0,3,10 #No of classes and features
    all_theta = np.zeros((k, n))
    for hazelnut in y_unique:
        np_y_train = np.array(y_train == hazelnut, dtype = int)
        best_theta = logisticRegression(X_train, np_y_train, np.zeros((n,1)),10000)
        all_theta[i] = best_theta.T
        i += 1   
    #Predictions
    prediction = sigmoid(X_test.dot(all_theta.T))
    prediction = prediction.tolist()
    pred = list()
    act = list()
    for _i,i in enumerate(prediction):
        pred.append(_label_dict[ i.index(max(i)) ])
        if _label_dict[ i.index(max(i)) ] !=  _label_dict[y_test[_i]] :
            missclass += 1
        act.append(_label_dict[y_test[_i]]) 
    score.append(round(accuracy_score(pred, act)*100,2))
    print("The score for Logistic Regression for fold",fold+1,"is: ",score[fold] ,'%', " No of misclassfied",missclass)
print("The overall score for Logistic Regression is: ", round(sum(score)/len(score),2),'%')

#Writing actual labels and predicted labels to csv file
output=list()
for i in range(len(pred)):
    output.append([pred[i],act[i], 'Matched' if pred[i] == act[i] else 'Unmatched'])
    Result = pd.DataFrame(output, columns=["Predicted Values", "Actual Value", "Matched/Unmatched"])
Result.to_csv('output.csv', header=True, index=False)

#Multiclass roc estimation referenced from scikit learn
def roc_estimation(y_test, y_pred , y_pred_proba, average="macro",num_class=3):  
    y_test = list(y_test)
    y_pred = list(y_pred)
    lb = LabelBinarizer()
    lb.fit(y_test)
    y_test = lb.transform(y_test)
    y_pred = lb.transform(y_pred)
    # print(y_test)
    fpr = dict()
    tpr = dict()
    roc_auc = dict()

    # print(num_class)
    for i in range(num_class):
        # print(i)
        y__ = [y[i] for y in y_pred_proba ]
        fpr[i], tpr[i], _ = roc_curve(y_test[:, i], y__)
        roc_auc[i] = auc(fpr[i], tpr[i])
    return roc_auc_score(y_test, y_pred, average=average) , (fpr,tpr,roc_auc)

#Plotting ROC curve
def plotting_roc(fpr, tpr, roc):
    all_fpr = np.unique(np.concatenate([fpr[i] for i in range(k)]))
    mean_tpr = np.zeros_like(all_fpr)
    for i in range(k):
        mean_tpr += np.interp(all_fpr, fpr[i], tpr[i])
    mean_tpr /= k
    fpr["macro"] = all_fpr
    tpr["macro"] = mean_tpr
    roc["macro"] = auc(fpr["macro"], tpr["macro"])
    for i in range(k):
        plt.plot(fpr[i],tpr[i],label='ROC = for %s %s' % (list(label_dict.keys())[i] , roc[i] * 100))
    plt.plot(fpr["macro"], tpr["macro"],
         label='macro-average ROC curve (area = {0:0.2f})'
               ''.format(roc["macro"]),
         color='navy', linestyle=':', linewidth=4)
    plt.legend(loc="top right")
    plt.show()
    
roc, add_roc = roc_estimation(y_test,pred,prediction,average="macro")
fpr,tpr,roc_auc = add_roc
plotting_roc(fpr,tpr,roc_auc)

#Confusion Matrix for our model
from sklearn.metrics import confusion_matrix #for confusion matrix
sns.heatmap(confusion_matrix(pred,act),annot=True,fmt='3.0f',cmap="summer")
plt.title('Our model Confusion Matrix', y=1.05, size=15)

