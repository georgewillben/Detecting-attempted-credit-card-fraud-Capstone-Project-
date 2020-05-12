def removeOutliers(X_train, y_train):
    """
    Removes outliers from training data where values are more than four standard deviations from the mean.
    Data must be in the form of a pandas DataFrame. 
    
    1) Copy train data
    2) Iterate through each column in the X data
    3) Find mean and standard deviation of each column
    4) Record indices from each column where values in the column are more than 4 standard deviations away from the mean
    5) Find all the indices from all the different columns
    6) Drop said indices from X and y train data
    7) Return new train data
    """
    # Copy data
    new_X_train = X_train.copy()
    new_y_train = y_train.copy()

    # Create list to store indices to drop per column
    col_indices = []

    # Create list of all indices to drop
    indices = []
    for col in new_X_train.columns:

        # Record columns mean and std
        mean_ = new_X_train[col].mean()
        std_ = new_X_train[col].std()
    
        # Append column's outlier indices to the indices list
        # outlier is any value more than three stardard deviations from its column's mean
        col_indices.append(new_X_train[ (new_X_train[col] < mean_ - 4*std_) | (new_X_train[col] > mean_ + 4*std_) ].index)

        # Take values from col_indices and form them into one list
        for list_ in col_indices:
            for item in list_:
                indices.append(item)
            
    # Set indices equal to its unique values
    indices = list(set(indices))
        
    # Drop all rows with outliers
    new_X_train = new_X_train.drop(indices, axis=0)
    new_y_train = new_y_train.drop(indices, axis=0)
    
    # Raise an error if the lengths do not match
    if len(new_X_train) != len(new_y_train):
        print("!"*40)
        print("Error")
        print("!"*40)
        
    return new_X_train, new_y_train

def customCV(clf, X, y, scaler, resampler, outlier_removal=False ,pca=None, print_splits=False):
    """
    Transforms data during cross validation and returns mean cross validated recall, precision, and f1 scores. Meant for imbalanced data.
    X and y must be pandas dataframe and/or series.
    
    Parameters:
    
    clf (object): a machine learning classifier with .fit and .predict methods
    X (object): Features, must be in form of pandas DataFrame
    y (object): Target, must be in form of pandas DataFrame
    scaler (object): a scaler from sklearn.preprocessing
    resampler (object): a resampling method such as SMOTE or NearMiss to make the data balanced during cross validation
        Must already be instantiated.
    outlier_removal (boolean, optional): if set to true will remove outliers that are more than four standard deviations 
        away from their columns mean
    pca (object, optional): an instantiated PCA object can be placed here to perform PCA on the data during cross validation
    print_splits (boolean, optional): if set to true function will print out scores on each of the cross validation folds
    
    1) Split data using StratifiedKFold
    2) Apply scaling to the data
    3) Resample data
    4) Remove outliers (optional)
    5) Apply PCA (optional)
    6) Fit and predict using clf
    7) Print and return results
    
    
    """
    from sklearn.model_selection import StratifiedKFold
    import numpy as np
    import pandas as pd
    from sklearn.metrics import classification_report
     
    # Create a list to store scores for each fold
    scores = []
    
    # Create folds using StratifiedKFold. 
    # StratifiedKFold is important to use on imbalanced data 
    # it ensures there is an equal ratio of the class values amoung folds
    skf = StratifiedKFold()
    for train_index, test_index in skf.split(X, y):
        X_train, X_test = X.iloc[train_index], X.iloc[test_index]
        y_train, y_test = y.iloc[train_index], y.iloc[test_index]
        
        # Scale data
        X_train_s = scaler.fit_transform(X_train)
        X_test_s = scaler.transform(X_test)
        X_train_s, X_test_s = pd.DataFrame(X_train_s, columns=X.columns), pd.DataFrame(X_test_s, columns=X.columns)
            
        # Resample
        # Uses resampler passed in as parameter
        X_train_s_r, y_train_r = resampler.fit_resample(X_train_s, y_train)
        X_train_s_r = pd.DataFrame(X_train_s_r, columns=X_train_s.columns)
        y_train_r = pd.Series(y_train_r, name='Class')
            
        # Remove outliers
        # see removeOutliers function in this file
        if outlier_removal:
            X_train_s_r_o, y_train_final = removeOutliers(X_train_s_r, y_train_r)
        else:
            X_train_s_r_o, y_train_final = X_train_s_r, y_train_r
        
        # PCA
        # Uses PCA object passed in as parameter
        if pca:
            X_train_final = pca.fit_transform(X_train_s_r_o)
            X_test_final = pca.transform(X_test_s)
        else:
            X_train_final = X_train_s_r_o
            X_test_final = X_test_s
            
        # Fit and Predict
        fit_clf = clf.fit(X_train_final, y_train_final)
        y_pred = fit_clf.predict(X_test_final)
        
        # Append results to the list "scores"
        scores.append([
            classification_report(y_test, y_pred, output_dict=True)['1']['recall'],
            classification_report(y_test, y_pred, output_dict=True)['1']['precision'],
            classification_report(y_test, y_pred, output_dict=True)['1']['f1-score']
        ])
        
    # Print results for each split    
    if print_splits:    
        for i, n in zip(scores, range(1, 6)):
            print("split", n)
            print("recall:", round(i[0], 4))
            print("precision:", round(i[1], 4))
            print("f1:", round(i[2], 4))
    
    # Find mean of all the split's scores
    recall = np.mean([i[0] for i in scores])
    precision = np.mean([i[1] for i in scores])
    f1 = np.mean([i[2] for i in scores])
    
    # Print mean results
    if print_splits:
        print("Mean Scores:")
        print("Mean recall:", round(recall, 4))
        print("Mean precision:", round(precision, 4))
        print("Mean f1:", round(f1, 4), '\n')
    
    return [recall, precision, f1]
    
    
    
def customGridSearchCV(clf, param_grid, X, y, scoring, scaler, resampler, outlier_removal=False, pca=None):
    from sklearn.model_selection import StratifiedKFold
    import numpy as np
    import pandas as pd
    from sklearn.preprocessing import MinMaxScaler, StandardScaler, RobustScaler
    from sklearn.metrics import classification_report
    """
    Grid searches parameters to find the combination of parameters with the optimal results. 
    Makes use of several helper functions.
    X and y must be pandas dataframe and/or series.
    parameter_grid must have 5 or less keys.
    
    Parameters
    clf (class): machine learning class with .fit and .predict methods. Do not use an instantiated object
    param_grid (dict): a dictionary with names of parameters as keys (max 5) and values to try out as values.
    X (object): features. Must be in form of pandas dataframe or series
    y (object): target. Must be in form of pandas dataframe or series
    scoring (string): If set to 'recall', 'precision', or 'f1' will return parameter combination with best relevent score.
        If set to 'custom' will return all parameter sets and score that have over 70% recall and over 30^ precision.
    scaler (sting): a scaler object from sklearn.preprocessing
    resampler (object): instantiated resampler object. Used during cross validation to make the data balanced. E.g. SMOTE or NearMiss
    outlier_removal (boolean, optional): tells function whether or not to remove outliers. Used during cross validation
    pca (object, optional): pass an instantiated PCA object to apply PCA during cross validation
    
    
    """
    
    # Generate a sorted list from the param_grid's keys
    param_keys = sorted(param_grid.keys())
    
    # Record length of param_keys
    len_ = len(param_keys)
    
    # Create a dict to hold scores for each parameter combination
    scores = {}
    
    # Current Params
    current_params = {}
    
    # customCV_params
    customCV_params = {
     'X' : X,
     'y' : y, 
     'scaler' : scaler, 
     'resampler' : resampler, 
     'outlier_removal' : outlier_removal ,
     'pca' : pca   
    }
          
    # Iterate through all combinations of parameters
    for value in param_grid[param_keys[0]]:
        current_params[param_keys[0]] = value
        if len_ == 1: 
            customCV_params['clf'] = clf(**current_params)
            scores[str(current_params)] = customCV(**customCV_params)
        else:
            for value2 in param_grid[param_keys[1]]:
                current_params[param_keys[1]] = value2
                if len_ == 2:
                    customCV_params['clf'] = clf(**current_params)
                    scores[str(current_params)] = customCV(**customCV_params)
                else:
                    for value3 in param_grid[param_keys[2]]:
                        current_params[param_keys[2]] = value3
                        if len_ == 3:
                            customCV_params['clf'] = clf(**current_params)
                            scores[str(current_params)] = customCV(**customCV_params)
                        else:
                            for value4 in param_grid[param_keys[3]]:
                                current_params[param_keys[3]] = value4
                                if len_ == 4:
                                    customCV_params['clf'] = clf(**current_params)
                                    scores[str(current_params)] = customCV(**customCV_params)
                                else:
                                    for value5 in param_grid[param_keys[4]]:
                                        current_params[param_keys[4]] = value5
                                        if len_ == 5:
                                            customCV_params['clf'] = clf(**current_params)
                                            scores[str(current_params)] = customCV(**customCV_params)
          
    # Find the best params based on scoring parameter
    # And return those params along with the scores
    if scoring == "all":
        for key in sorted(scores.keys()):
            print('\n', key, '\n recall', scores[key][0], '\n precision:', scores[key][1], '\n f1-score:', scores[key][2], '\n')
            return scores
    if scoring == 'custom':
        for key in sorted(scores.keys()):
            if (scores[key][0] > 0.5) & (scores[key][1] > 0.2):
                print('\n', key, '\n recall', scores[key][0], '\n precision:', scores[key][1], '\n f1-score:', scores[key][2], '\n')
        return scores
    if scoring == 'recall':
        max_score = max([i[0] for i in scores.values()])
        for key in scores.keys():
            if scores[key][0] == max_score:
                print(scaler_str, '\n recall:', scores[key][0], '\n precision:', scores[key][1], '\n f1-score:', scores[key][2], '\n')
                return (key, scores[key], scaler_str, resampler, outlier_removal, pca)
    elif scoring == 'precision':
        max_score == max([i[1] for i in scores.values()])
        for key in scores.keys():
            if scores[key][1] == max_score:
                print(scaler_str, '\n recall:', scores[key][0], '\n precision:', scores[key][1], '\n f1-score:', scores[key][2], '\n')
                return (key, scores[key], scaler_str, resampler, outlier_removal, pca)
    elif scoring == 'f1':
        max_score = max([i[2] for i in scores.values()])
        for key in scores.keys():
            if scores[key][2] == max_score:
                print(scaler_str, '\n recall:', scores[key][0], '\n precision:', scores[key][1], '\n f1-score:', scores[key][2], '\n')
                return (key, scores[key], scaler_str, resampler, outlier_removal, pca)
          
          
