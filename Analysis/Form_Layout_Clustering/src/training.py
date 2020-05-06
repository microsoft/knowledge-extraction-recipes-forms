import pickle

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split

from text_features import TFIDFProcessor


def get_threshold_mask(predicted_proba, threshold):
    """
    Creates a bool mask for all the predictions with
    confidence/probability score above the threshold

    Args:
        predicted_proba (array):
            Array with predicted per class probabilities.
            Shape: (n_samples, n_classes)
        threshold (float):
            Confidence/probability threshold to use for cutoff

    Returns:
        array:
            Bool threshold mask of shape (n_samples, )
    """
    y_pred_argmax = np.argmax(predicted_proba, axis=-1)
    print("Total predictions: ", len(y_pred_argmax))
    top_conf_list = [x[0][x[1]] for x in zip(predicted_proba, y_pred_argmax)]
    threshold_mask = np.asarray(top_conf_list) > threshold
    print("Predictions above threshold (%s): " % threshold, sum(threshold_mask))
    return threshold_mask


class TFIDFModel(object):
    """
    Single class to train, evaluate and run predictions using TFIDF features.

    Args:
        model_path (str, optional):
            Path used to save/load trained model object.
            If set to None - model won't be saved.
            Defaults to None.
        test_size (float, optional):
            How much data to hold out for evaluation. Defaults to 0.33.
        tfidf_path (str, optional):
            Path used to save/load fitted TFIDFVectorizer object.
            If set to None - object won't be saved.
            Defaults to None.
        ngram_range (tuple, optional):
            TFIDF param: Decides which ngrams to use.
            Defaults to (1, 2).
        max_feat (int, optional):
            TFIDF param: Max size of features vector. Defaults to None.
        use_pca (bool, optional):
            Defaults to True.
        pca_path (str, optional):
            Path used to save/load fitted PCA object.
            If set to None - PCA won't be saved.
            Defaults to None.
        pca_components (int, optional):
            PCA param: Reduces number of features/components to this value.
            Defaults to 100.
        use_scaler (bool, optional):
            Defaults to True.
        scaler_path (str, optional):
            Path used to save/load StandardScaler object.
            If set to None - scaler won't be saved.
            Defaults to None.
        random_state (int, optional):
            Random state value to be used.
            Defaults to 0.
        verbose (int, optional):
            0 - no msgs,
            1 - print out only error messages,
            2 - print everything.
            Defaults to 2.

    Raises:
        ValueError: `model` is None when model was not trained
                    or loaded before running predictions
    """
    def __init__(
            self,
            model_path=None, test_size=0.33,
            tfidf_path=None, ngram_range=(1, 2), max_feat=10000,
            use_pca=True, pca_path=None, pca_components=100,
            use_scaler=True, scaler_path=None,
            random_state=0, verbose=2):

        self.model_path = model_path

        self.tfidf_path = tfidf_path
        self.ngram_range = ngram_range
        self.max_feat = max_feat

        self.use_pca = use_pca
        self.pca_path = pca_path
        self.pca_components = pca_components

        self.use_scaler = use_scaler
        self.scaler_path = scaler_path

        self.random_state = random_state
        self.verbose = verbose
        self.test_size = test_size

        self.tfidf_processor = TFIDFProcessor(
            tfidf_path=self.tfidf_path, ngram_range=self.ngram_range, max_feat=self.max_feat,  # NOQA E501
            pca_path=self.pca_path, use_pca=self.use_pca, pca_components=self.pca_components,  # NOQA E501
            scaler_path=self.scaler_path, use_scaler=self.use_scaler,
            verbose=2)

        self.model = None

    def train_from_df(
            self, df,
            x_col='TextProc', y_col='Cluster',
            **kwargs):
        """Training of TFIDFModel based on pandas.DataFrame input

        Args:
            df (pandas.DataFrame):
                DataFrame with features and labels
            x_col (str, optional):
                Name of the column with text. Defaults to 'TextProc'.
            y_col (str, optional):
                Name of the column with labels. Defaults to 'Cluster'.
            **kwargs:
                You can use any of the Init params for TFIDFModel here

        Returns:
            RandomForestClassifier: Trained model
        """

        for key, value in kwargs.items():
            setattr(self, key, value)

        if self.verbose == 2:
            print("Layout type distribution:")
            print(df[y_col].value_counts())
            print("===========================")

        df_train, df_test = self.split_df(df)

        X_train = df_train[x_col].values
        X_test = df_test[x_col].values
        X_train = self.fit_transform(X_train)
        X_test = self.transform(X_test)

        y_train = df_train[y_col].values
        y_test = df_test[y_col].values

        self.model = self.train(X_train, y_train)

        self.evaluate(X_test, y_test)

        return self.model

    def split_df(self, df, **kwargs):
        """Split DataFrame into train and test subsets

        Args:
            df (pandas.DataFrame):
                DataFrame with all the data
            **kwargs:
                You can use any of the Init params for TFIDFModel here

        Returns:
            df_train, df_test
        """

        for key, value in kwargs.items():
            setattr(self, key, value)

        # split df into train/test
        df_train, df_test = train_test_split(
            df, test_size=self.test_size, random_state=self.random_state)

        return df_train, df_test

    def train_from_np(self, X, y, **kwargs):
        """Training of TFIDFModel based on numpy array inputs

        Args:
            X (numpy.ndarray):
                Text values that will be featurized
            y (numpy.ndarray):
                Labels used for training and validation
            **kwargs:
                You can use any of the Init params for TFIDFModel here
        """

        for key, value in kwargs.items():
            setattr(self, key, value)

        X_train, X_test, y_train, y_test = self.split_np(X, y)

        X_train = self.fit_transform(X_train)
        X_test = self.transform(X_test)

        self.model = self.train(X_train, y_train)

        self.evaluate(X_test, y_test, self.model)

    def split_np(self, X, y, **kwargs):
        """Splits data into train and test subsets

        Args:
            X (numpy.ndarray):
                Text values that will be featurized
            y (numpy.ndarray):
                Labels used for training and validation
            **kwargs:
                You can use any of the Init params for TFIDFModel here

        Returns:
            X_train, X_test, y_train, y_test
        """

        for key, value in kwargs.items():
            setattr(self, key, value)

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=self.test_size, random_state=self.random_state)

        return X_train, X_test, y_train, y_test

    def fit_transform(self, X_train, **kwargs):
        """Fit data into transformers

        Args:
            X_train (numpy.ndarray):
                Training set of features
            **kwargs:
                You can use any of the Init params for TFIDFModel here

        Returns:
            numpy.ndarray: Data after applying transformations
        """

        for key, value in kwargs.items():
            setattr(self, key, value)

        X_train = self.tfidf_processor.fit_pipeline(
            X_train,
            tfidf_path=self.tfidf_path,
            ngram_range=self.ngram_range,
            pca_path=self.pca_path,
            use_pca=self.use_pca,
            pca_components=self.pca_components,
            scaler_path=self.scaler_path,
            use_scaler=self.use_scaler
        )

        return X_train

    def transform(self, X, **kwargs):
        """Applies pipeline from TFIFDProcessor instance

        Args:
            X (numpy.ndarray):
                Data to apply transformations
            **kwargs:
                You can use any of the Init params for TFIDFModel here

        Returns:
            numpy.ndarray: Data after transformations
        """

        for key, value in kwargs.items():
            setattr(self, key, value)

        X = self.tfidf_processor.apply_pipeline(
            X,
            tfidf_path=self.tfidf_path,
            pca_path=self.pca_path if self.use_pca else None,
            scaler_path=self.scaler_path if self.use_scaler else None
        )

        return X

    def train(self, X_train, y_train, **kwargs):
        """Universal train function

        Args:
            X_train (numpy.ndarray):
                Training features array
            y_train (numpy.ndarray):
                Training labels array
            **kwargs:
                You can use any of the Init params for TFIDFModel here

        Returns:
            Model: Trained model
        """

        for key, value in kwargs.items():
            setattr(self, key, value)

        model = RandomForestClassifier(
            n_estimators=1000,
            random_state=self.random_state)
        model.fit(X_train, y_train)

        # save model if model_path is provided
        if self.model_path is not None:
            pickle.dump(model, open(self.model_path, "wb"))

        return model

    def predict(self, X, model=None, **kwargs):
        """Outputs predicted classes for each row

        Args:
            X (numpy.ndarray):
                Features to run prediction on
            model (sklearn classifier object, optional):
                Trained instance of a model to run evaluation on.
                If None it will try to use class level variable.
                Defaults to None.
            **kwargs:
                You can use any of the Init params for TFIDFModel here

        Raises:
            ValueError:
                `model` is None when model is not trained or set

        Returns:
            numpy.ndarray:
                Array with predicted classes per row of data
        """

        for key, value in kwargs.items():
            setattr(self, key, value)

        self.model = self.model if model is None else model
        if self.model is None:
            raise ValueError("'model' is None")

        predicted = self.model.predict(X)
        return predicted

    def predict_proba(self, X, model=None, **kwargs):
        """Outputs per class probability for each row

        Args:
            X (numpy.ndarray):
                Features to run prediction on
            model (sklearn classifier object, optional):
                Trained instance of a model to run evaluation on.
                If None it will try to use class level variable.
                Defaults to None.
            **kwargs:
                You can use any of the Init params for TFIDFModel here

        Raises:
            ValueError:
                `model` is None when model is not trained or set

        Returns:
            numpy.ndarray:
                Array with predicted probabilities per class
        """

        for key, value in kwargs.items():
            setattr(self, key, value)

        self.model = self.model if model is None else model
        if self.model is None:
            raise ValueError("'model' is None")

        predicted_proba = self.model.predict_proba(X)
        return predicted_proba

    def evaluate(self, X, y, model=None, **kwargs):
        """Runs evaluation fro each row of X and y.
        If verbose == 2 it will print classification report

        Args:
            X (numpy.ndarray):
                Features to run prediction on
            y (numpy.ndarray):
                Labels to use for evaluation
            model (sklearn classifier object, optional):
                Trained instance of a model to run evaluation on.
                If None it will try to use class level variable.
                Defaults to None.
            **kwargs:
                You can use any of the Init params for TFIDFModel here

        Raises:
            ValueError:
                `model` is None when model is not trained or set
        """

        for key, value in kwargs.items():
            setattr(self, key, value)

        self.model = self.model if model is None else model
        if self.model is None:
            raise ValueError("'model' is None")

        predicted = self.predict(X, self.model)
        if self.verbose > 0:
            print("===========================")
            print("Mean validation accuracy: ", np.mean(predicted == y))
            if self.verbose == 2:
                print(classification_report(y, predicted))
            print("===========================")
