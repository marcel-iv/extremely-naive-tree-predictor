import numpy as np
import pandas as pd
import statistics
import math
import sklearn.model_selection as model_selection

from scipy.stats import spearmanr
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score
from sklearn import metrics
from sklearn.feature_selection import VarianceThreshold, SelectKBest, SelectPercentile, r_regression

# Data preprocessing, copied from the server
data_read = pd.read_csv("../../03_Data/demographic_IgG_PBMC_cytokine.tsv", sep="\t")

data = data_read

# split into training and testing (also remove id data because its not needed)
# Columns: 0-2 IDs, 3-5 is demographic data, 6 is target, 7-45 is PBMCs
Features_pre = data.iloc[:, 3:121]
Features = Features_pre.drop(["Monocytes_D1"], axis=1)
Response = data[["Monocytes_D1"]]

features_train, features_test, response_train, response_test = train_test_split(Features, Response, test_size = 0.2, random_state=101)

# Feature engineering - Failure
#selector = VarianceThreshold(0.9*(1-0.9))
#Features_engineered = selector.fit_transform(Features)
#Features_engineered2 = SelectKBest(score_func=r_regression, k=10).fit_transform(Features, Response)
#Features_engineered3 = SelectPercentile(score_func=r_regression, percentile=50).fit_transform(Features, Response)
#features_train_e, features_test_e, response_train_e, response_test_e = train_test_split(Features_engineered3, Response, test_size= 0.2, random_state=103)

# Train the forest
RandomForest = RandomForestRegressor(n_estimators=500, max_depth=10, max_features="log2", random_state=101)
RandomForest.fit(features_train, response_train)

predictions = RandomForest.predict(features_test)

# Spearman Scoring Method
def spearman(x,y):
    corr, pval = spearmanr(x,y)
    return(corr)

spearman_scorer = metrics.make_scorer(score_func=spearman, response_method='predict', greater_is_better=True)

# Cross Validation
forest_CV = model_selection.KFold(n_splits=5, shuffle = True, random_state=101)
#print("Spearman correlations over 5-fold CV")
#print(model_selection.cross_val_score(RandomForest, features_train, response_train, cv=forest_CV, scoring=spearman_scorer))

# Grid Search
parameter_grid = {'n_estimators': [100, 500, 1000],
                  'max_depth': [5, 10, 15],
                  'criterion': ["squared_error", "friedman_mse", "poisson"],
                  'max_features': [0.1, "sqrt", "log2", None]}
grid = model_selection.GridSearchCV(estimator = RandomForest, param_grid=parameter_grid, scoring=spearman_scorer)
grid.fit(features_train, response_train)
print("Best Hyperparameters")
print(grid.best_params_)

# With Full data (non-engineered): poisson, 5, None, 500

RandomForest_ideal = RandomForestRegressor(n_estimators=500, criterion="poisson", max_depth=5, max_features=None, random_state=101)

# Helpers
def get_quals(estimator, x_test, y_test):
    y_predicted = estimator.predict(x_test)
    print(estimator.get_params())
    print("Spearman:", spearman(y_test, y_predicted))

RandomForest_ideal.fit(features_train, response_train)

# Evaluation
r2 = r2_score(response_test.values.ravel(), predictions)
spearman_correlation, p_value = spearmanr(response_test, predictions)
print("Spearman values across 5-fold CV for the Ideal forest")
print(model_selection.cross_val_score(RandomForest_ideal, features_train, response_train, cv=forest_CV, scoring=spearman_scorer))

print("Spearman value for ideal forest on test features:")
get_quals(RandomForest_ideal, features_test, response_test)

# 0.778 for 500, poisson, 5, none.
# 0.734 for 500, poisson, 5, log2.
# 0.737 for 1000, poisson, 10, log2

print("R^2 Value (Single):")
print(r2)
print("Spearman Correlation (Single):")
print(spearman_correlation)

# Calculate fold/log change 
# takes two inputs (which should be numbers) and returns their logarithmised fold change
def fold_change(value1, value2):
    ratio = (value2/value1)
    log_change = math.log2(ratio)
    return log_change


