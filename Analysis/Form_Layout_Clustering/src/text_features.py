import os
import pickle
import re

from fuzzywuzzy import fuzz, process
from sklearn.decomposition import PCA
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler


def clean_text(text, findall="[a-zA-Z]+", keep='all', min_words_count=0):
    """
    Performs cleaning of text coming from OCR results.

    Args:
        text (str):
            Text to be cleaned up.
        findall (str, optional):
            Regex to use for characters whitelisting.
            Defaults to "[a-zA-Z&]+".
        keep (str, optional):
            'header' - take top 1/3 of the text
            'header+bottom' - take top 1/3 and bottom 1/3 of the text
            'all' - take all the text
            Defaults to 'all'.
        min_words_count (int, optional):
            Threshold for minimum words present.
            Returns empty string if below threshold.
            Defaults to 0.

    Returns:
        str:
            Clean ouput text
    """
    assert(keep in ['all', 'header', 'header+bottom'])
    # leave letter chars only
    text = " ".join(re.findall(findall, text))
    # single white space between words
    text = " ".join(text.split())
    # lower case
    text = text.lower()

    # reduce amount of text to remove noisy features
    if keep == 'header':
        words_list = text.split()
        words_count = len(words_list)
        # take top 1/3 of ocr text
        text = " ".join(words_list[:words_count//3])
    elif keep == 'header+bottom':
        words_list = text.split()
        words_count = len(words_list)
        # take top 1/3 and bottom 1/3 of ocr text
        words_list[words_count//3:(words_count//3)*2] = []
        text = " ".join(words_list)

    # if number of words to small just empty text
    # TODO: consider returning np.NaN here instead
    if len(text.split()) < min_words_count:
        text = ""

    return text


def fuzzy_search(
        query_string,
        options_dict,
        scorer=fuzz.QRatio,
        score_cutoff=81):
    """
    Uses fuzzy search to find best matches for the `query_string` in
    `options_dict`

    Args:
        query_string (str):
            String used to search for matches
        options_dict (list):
            List of options to find matches in.
        scorer (fuzz.Scorer, optional):
            Strategy to use when searching for matches.
            Defaults to fuzz.QRatio.
        score_cutoff (int, optional):
            Similarity score cutoff threshold.
            Defaults to 81.

    Returns:
        array:
            Array of matching words
    """

    fuzzy_results = process.extractBests(
        query_string,
        options_dict,
        scorer=fuzz.QRatio,
        score_cutoff=score_cutoff
    )

    return fuzzy_results


def fuzzy_replace(
        words_list,
        query_list,
        threshold=81,
        return_string=True,
        scorer=fuzz.QRatio,
        whitelist=False):
    """
    Function to perform fuzzy replacing based on `words_list` (vocabulary)
    and similarity `threshold`.

    Args:
        words_list (list):
            List of words list (vocabulary) to match against
        query_list (list):
            List of query strings
        threshold (int, optional)
            Similarity threshold used fot cutoff when fuzzy matching.
            Defaults to 81.
        return_string (bool, optional):
            Return string or list of strings
            Defaults to True.
        scorer (fuzz.Scorer, optional):
            Matching algorithm used by fuzzywuzzy.
            Defaults to fuzz.QRatio.
        whitelist (bool, optional):
            Whitelist output words based on vocabulary.
            Defaults to False.

    Returns:
        string or list of strings:
            Single string representing whole output text or
            a list of single words
    """
    # moving forward we want to work with a list of strings
    # convert string to list of strings based using split
    if type(words_list) is str:
        words_list = words_list.lower().split()
    # convert list of strings to dict to capture index
    words_dict = {idx: el for idx, el in enumerate(words_list)}
    # run fuzzy search for each query vs whole words_dict
    fuzzy_results = [
        (
            query, fuzzy_search(
                query, words_dict,
                scorer=scorer, score_cutoff=threshold)
        ) for query in query_list
    ]
    # iterate through search results
    for res in fuzzy_results:
        # if result is not empty list
        if res[1] != []:
            # iterate through all fuzzy matches
            for word in res[1]:
                # get dict key and update (replace) value
                words_dict[word[2]] = words_dict[word[2]].replace(
                    word[0], res[0])
    result = ""
    if whitelist:
        # keep/remove strings based on words list
        result = [
            text if text in query_list else ""
            for text in words_dict.values()
        ]
    else:
        result = list(words_dict.values())

    if return_string:
        # join list of string into a single string obj
        result = " ".join(result)

    return result


class TFIDFProcessor(object):
    """
    Single class to fit and apply transformation for
    TFIDF features and related pipeline.

    Args:
        tfidf_path (str, optional):
            Path used to serialize or deserialize TFIDF object.
            Defaults to None.
        ngram_range (tuple, optional):
            Defines range of ngrams to be used by TFIDF.
            Defaults to (1, 2).
        max_feat (int, optional):
            Max features number to be used by TFIDF.
            Defaults to 3000.
        pca_path (str, optional):
            Path used to serialize or deserialize TFIDF object.
            Defaults to None.
        use_pca (bool, optional):
            Use PCA in processing pipelie.
            Defaults to True.
        pca_components (int, optional):
            Output number of components for PCA.
            Defaults to 15.
        scaler_path (str, optional):
            Path used to serialize or deserialize TFIDF object.
            Defaults to None.
        use_scaler (bool, optional):
            Use StandardScaler in the pipeline or not.
            Defaults to True.
        verbose (int, optional):
            0 - nothing,
            1 - errors, top importance
            2 - all msgs
            Defaults to 2.

    Returns:
        TFIDFProcessor:
            Instance of TFIDFProcessor
    """
    def __init__(
            self,
            tfidf_path=None, ngram_range=(1, 2), max_feat=3000,
            pca_path=None, use_pca=True, pca_components=15,
            scaler_path=None, use_scaler=True,
            verbose=2):

        self.tfidf_path = tfidf_path
        self.ngram_range = ngram_range
        self.max_feat = max_feat

        self.pca_path = pca_path
        self.use_pca = use_pca
        self.pca_components = pca_components

        self.scaler_path = scaler_path
        self.use_scaler = use_scaler

        self.verbose = verbose

        self.tfidf = None
        self.pca = None
        self.scaler = None

    def fit_pipeline(self, X, **kwargs):

        for key, value in kwargs.items():
            setattr(self, key, value)

        self.tfidf, X = self.fit_tfidf(
            X,
            ngram_range=self.ngram_range,
            max_feat=self.max_feat,
            save_path=self.tfidf_path)
        if self.verbose > 0:
            print('TFIDF shape:', X.shape)

        if self.use_pca:
            self.pca, X = self.fit_pca(
                X,
                n_components=self.pca_components,
                save_path=self.pca_path)
            if self.verbose > 0:
                print('PCA shape:', X.shape)

        if self.use_scaler:
            self.scaler, X = self.fit_scaler(
                X,
                save_path=self.scaler_path)

        return X

    def fit_tfidf(
            self,
            X,
            save_path=None,
            **kwargs):

        for key, value in kwargs.items():
            setattr(self, key, value)

        tfidf = TfidfVectorizer(
            # sublinear_tf=True,
            max_features=self.max_feat,
            norm='l2',
            encoding='latin-1',
            ngram_range=self.ngram_range,
            stop_words='english')

        tfidf, X = self.fit_transformer(X, tfidf, save_path)
        return tfidf, X.toarray()

    def fit_pca(self, X, save_path=None, **kwargs):

        for key, value in kwargs.items():
            setattr(self, key, value)

        pca = PCA(n_components=self.pca_components)
        return self.fit_transformer(X, pca, save_path)

    def fit_scaler(self, X, save_path=None):
        scaler = StandardScaler()
        return self.fit_transformer(X, scaler, save_path)

    def fit_transformer(self, X, transformer, save_path=None):
        X = transformer.fit_transform(X)

        if save_path is not None:
            pickle.dump(transformer, open(save_path, "wb"))
            if self.verbose > 0:
                print('Saved transformer to file:', save_path)

        return transformer, X

    def apply_pipeline(self, X, load_from_paths=False, **kwargs):

        for key, value in kwargs.items():
            setattr(self, key, value)

        if load_from_paths:
            self.tfidf = self.tfidf_path
            self.pca = self.pca_path
            self.scaler = self.scaler_path

        X = self.apply_tfidf(X, self.tfidf)
        if self.verbose > 0:
            print('TFIDF shape:', X.shape)

        if self.pca is not None:
            X = self.apply_pca(X, self.pca)
            if self.verbose > 0:
                print('PCA shape:', X.shape)

        if self.scaler is not None:
            X = self.apply_scaler(X, self.scaler)

        return X

    def apply_pca(self, X, pca):
        # assert(type(pca) is str or type(pca) is PCA)
        return self.apply_transform(X, pca)

    def apply_tfidf(self, X, tfidf):
        # assert(type(tfidf) is str or type(tfidf) is TfidfVectorizer)
        return self.apply_transform(X, tfidf).toarray()

    def apply_scaler(self, X, scaler):
        # assert(type(scaler) is str or type(scaler) is TfidfVectorizer)
        return self.apply_transform(X, scaler)

    def apply_transform(self, data, transformer):
        if type(transformer) is str:
            assert(os.path.exists(transformer))

            if self.verbose > 1:
                print('Loading transformer from exisiting file:', transformer)

            transformer = pickle.load(open(transformer, "rb"))

        return transformer.transform(data)
