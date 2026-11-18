import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer

df = pd.read_csv('german_credit_data.csv')

# Since the dataset has no target column, let's check all columns again just in case
print(df.columns.tolist())

# Create a synthetic/derived target for demonstration, e.g., Credit_Approved based on realistic credit scoring logic or median threshold
# Wait: usually in German credit data without 'Risk', people define a target or use a standard rule/median.
# Let's define a clear, transparent binary target variable: e.g., Favorable Outcome (1) = Credit amount <= median (or < 3500) & good accounts, or simply Credit amount >= median (or <= 3000) to simulate credit approval/low risk, OR let's train a baseline model on a derived target and explain clearly!
# Let's check what happens if we define Target = 1 (Bajo Riesgo / Aprobado) when Credit amount <= 3000 (or based on a standard risk heuristic) and train a Logistic Regression model to get predicted outcomes (y_pred) so we can compute Favorable Outcome Rate (Selection Rate), TPR, and FPR!