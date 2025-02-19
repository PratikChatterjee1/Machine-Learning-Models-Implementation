# -*- coding: utf-8 -*-
"""EEG Confusion Analysis.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1iyVxM4oQPTr1YUix_kbs10nLMJE0MVSp
"""

# Commented out IPython magic to ensure Python compatibility.
# EDA pkgs
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
# %matplotlib inline
import seaborn as sns
sns.set(style='darkgrid', color_codes=True)

eeg_data = pd.read_csv("EEG_data.csv")
demographic_data = pd.read_csv("demographic_info.csv")

eeg_data

demographic_data

"""### Data

These data are collected from ten students, each watching ten videos. Therefore, it can be seen as only 100 data points for these 12000+ rows. If you look at this way, then each data point consists of 120+ rows, which is sampled every 0.5 seconds (so each data point is a one minute video). Signals with higher frequency are reported as the mean value during each 0.5 second.

- EEG_data.csv: Contains the EEG data recorded from 10 students

- demographic.csv: Contains demographic information for each student

## Narrative:
We will merge the dataframe with respect to Subject ID.

- Unique identifer needs to be removed from the feature as in future this model can be generalize for any video.

## Merging DataFrame
"""

demographic_data.rename(columns={"subject ID": "SubjectID"}, inplace = True)

data = demographic_data.merge(eeg_data, on='SubjectID')

data

"""### Narrative:
- We are going to remove the Unique Identifier from the data.
- We will drop "predefinedlabel" from the data as this is a function which hints the model for predictions. Our target is "userdefinedlabeln" that we need to predict if a student will be confused or not after watching a video.
"""

data.info()

data.isna().sum()

"""## No missing value

# Data preparation
"""

from sklearn.preprocessing import OneHotEncoder
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

from sklearn.ensemble import RandomForestClassifier

from sklearn.metrics import classification_report, plot_confusion_matrix, matthews_corrcoef

def preprocess_inputs(df):
  df = df.copy()

  #drop unnecessary columns
  df = df.drop(["SubjectID", "VideoID", "predefinedlabel"], axis=1)

  #rename columns name 
  df.rename(columns={' age': 'Age', ' ethnicity': 'Ethnicity', ' gender': 'Gender', 'user-definedlabeln': 'Label'}, inplace=True)

  #binary encoding the Gender column
  df['Gender'] = df['Gender'].apply(lambda x: 1  if x == 'M' else 0)

  #X and y
  X = df.drop("Label", axis=1)
  y = df['Label']

  #split the data
  X_train, X_test, y_train, y_test = train_test_split(X,y, train_size=0.7, shuffle=True, random_state=1)

  return X_train, X_test, y_train, y_test

"""## Narrative:
- Need to Onehot encode "Ethnicity" column.
- Rest of the columns are well settled and numerical. 

- We can scale the data if we are not using any tree-based models. Tree-based models don't require Scaled data.

- feature: all except "Label"
"""

X_train, X_test, y_train, y_test = preprocess_inputs(data)

X_train

y_train

print(len(X_train))
print(len(X_test))
print(len(y_train))
print(len(y_test))

"""## Model Pipeline"""

nominal_transformer = Pipeline(steps=[
                                      ("onehot", OneHotEncoder(sparse=False))
])

preprocessor = ColumnTransformer(transformers=[
                                               ("nominal", nominal_transformer, ['Ethnicity'])
], remainder = 'passthrough')


model = Pipeline(steps=[
                        ('preprocessor', preprocessor),
                        ('classifier', RandomForestClassifier())
])

clf = model.fit(X_train, y_train)
print(clf)

score = clf.score(X_test, y_test)
print("Score is: ", np.round(score*100), "%")

y_pred = clf.predict(X_test)
y_pred

matthews_corrcoef_score = matthews_corrcoef(y_test, y_pred)
print(matthews_corrcoef_score)

plot_confusion_matrix(clf, X_test, y_test, labels=clf.classes_)

clr = classification_report(y_test, y_pred, labels=clf.classes_)
print(clr)

"""## We are doing very bad. In general, this data is very challenging and complex as mentioned on the Kaggle. We will try something else for evaluation and interpretation.

# PyCaret to identify the best model.
"""

!pip install pycaret

import pycaret.classification as pyc

"""# Data Preparation for PyCaret"""

def data_preparation(df):
  df = df.copy()

  #drop unnecessary columns
  df = df.drop(["SubjectID", "VideoID", "predefinedlabel"], axis=1)

  #rename columns name 
  df.rename(columns={' age': 'Age', ' ethnicity': 'Ethnicity', ' gender': 'Gender', 'user-definedlabeln': 'Label'}, inplace=True)

  #binary encoding the Gender column
  df['Gender'] = df['Gender'].apply(lambda x: 1  if x == 'M' else 0)


  return df

X = data_preparation(data)

X

pyc.setup(
    data = X,
    target = 'Label',
    train_size = 0.7,
    normalize = True
)

pyc.compare_models()

"""## In Pipeline, we used RandomForestClassifier(), as it works well on the most of the classification problems but interpretation is little difficult than Logistic or Decision Tree. It is "Accuracy-Interpretation" trade-off.

Using PyCaret compare models function, we can quickly see which model is doing good. ExtraTree for example in this case.
"""

best_model = pyc.create_model('et')

pyc.evaluate_model(best_model)

pyc.save_model(best_model, "eeg_confusion_model")

"""# Using Neural Net

We will do an ANN.
"""

import tensorflow as tf
from sklearn.preprocessing import StandardScaler

def data_inputs_tf(df):
  #drop unnecessary columns
  df = df.drop(["SubjectID", "VideoID", "predefinedlabel"], axis=1)

  #rename columns name 
  df.rename(columns={' age': 'Age', ' ethnicity': 'Ethnicity', ' gender': 'Gender', 'user-definedlabeln': 'Label'}, inplace=True)

  #binary encoding the Gender column
  df['Gender'] = df['Gender'].apply(lambda x: 1  if x == 'M' else 0)

  #one hot encode the "Ethnicity column"
  ethnicity_dummies = pd.get_dummies(df['Ethnicity'])
  df = pd.concat([df, ethnicity_dummies], axis=1)
  df = df.drop('Ethnicity', axis=1)


  #X and y
  X = df.drop("Label", axis=1)
  y = df['Label']

  # Scale the data as all the columns will be in same range (mean of 0 and variance of 1)
  scaler = StandardScaler()
  X = scaler.fit_transform(X)

  #split the data
  X_train, X_test, y_train, y_test = train_test_split(X,y, train_size=0.7, shuffle=True, random_state=1)
 

  return X_train, X_test, y_train, y_test

X_train, X_test, y_train, y_test = data_inputs_tf(data)

X_train

y_train

"""# Model architecture"""

inputs = tf.keras.Input(shape=(X_train.shape[1]))
x = tf.keras.layers.Dense(256, activation='relu')(inputs)
x = tf.keras.layers.Dense(256, activation='relu')(x)
outputs = tf.keras.layers.Dense(1, activation='sigmoid')(x)

model = tf.keras.Model(inputs, outputs)


model.compile(
    optimizer='adam',
    loss='binary_crossentropy',
    metrics=[
        'accuracy',
        tf.keras.metrics.AUC(name='auc')
    ]
)

batch_size = 32
epochs = 50

history = model.fit(
    X_train,
    y_train,
    validation_split=0.2,
    batch_size=batch_size,
    epochs=epochs,
    callbacks=[
        tf.keras.callbacks.ReduceLROnPlateau()
    ]
)

plt.figure(figsize=(16, 10))

plt.plot(range(epochs), history.history['loss'], label="Training Loss")
plt.plot(range(epochs), history.history['val_loss'], label="Validation Loss")

plt.xlabel("Epoch")
plt.ylabel("Loss")
plt.title("Loss Over Time")
plt.legend()

plt.show()

model.evaluate(X_test, y_test)

y_true = np.array(y_test)

y_pred = np.squeeze(model.predict(X_test))
y_pred = np.array(y_pred >= 0.5, dtype=np.int)

from sklearn.metrics import confusion_matrix

cm = confusion_matrix(y_true, y_pred)

plt.figure(figsize=(4, 4))

sns.heatmap(cm, annot=True, fmt='g', vmin=0, cbar=False)

plt.xlabel("Predicted")
plt.ylabel("Actual")
plt.title("Confusion Matrix")

plt.show()

print(classification_report(y_true, y_pred))

