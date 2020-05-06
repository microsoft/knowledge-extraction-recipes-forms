import matplotlib.pyplot as plt
import numpy as np
from sklearn import metrics
from sklearn.cluster import DBSCAN
from sklearn.manifold import TSNE


def fit_dbscan(X_fit, eps=0.55, min_samples=8, plot=False, n_jobs=None):
    """Runs DBSCAN based clustering.

    Args:
        X_fit (array):
            Array of feature vectors
        eps (float, optional): 
            The maximum distance between two samples for one to be considered as in the neighborhood of the other.  # NOQA E501
            This is not a maximum bound on the distances of points within a cluster.  # NOQA E501
            This is the most important DBSCAN parameter to choose appropriately for your data set and distance function.  # NOQA E501
            Defaults to 0.55.
        min_samples (int, optional):
            The number of samples (or total weight) in a neighborhood for a point to be considered as a core point.  # NOQA E501
            This includes the point itself.
            Defaults to 8.
        plot (bool, optional): Plot visual representation of clustering results.
            Defaults to False.
        n_jobs (int or None):
            The number of parallel jobs to run.
            None means 1 unless in a joblib.parallel_backend context. -1 means using all processors.
            Defaults to None.

    Returns:
        (array, sklearn.cluster.DBSCAN):
            Array of labels assigned through clustering and DBSCAN class instance
    """
    # Compute DBSCAN
    db = DBSCAN(eps=eps, min_samples=min_samples).fit(X_fit)

    core_samples_mask = np.zeros_like(db.labels_, dtype=bool)
    core_samples_mask[db.core_sample_indices_] = True
    labels = db.labels_
    # labels[~core_samples_mask] = -1
    # Number of clusters in labels, ignoring noise if present.
    n_clusters_ = len(set(labels)) - (1 if -1 in labels else 0)
    n_noise_ = list(labels).count(-1)

    print(
        'Estimated number of clusters: %d' % n_clusters_)
    print(
        'Estimated number of noise points: %d' % n_noise_)

    # Black removed and is used for noise instead.
    unique_labels = set(labels)
    if plot:
        colors = [
            plt.cm.Spectral(each)
            for each in np.linspace(0, 1, len(unique_labels))]

        plt.figure(figsize=(5, 5))
        for k, col in zip(unique_labels, colors):
            if k == -1:
                # Black used for noise.
                col = [0, 0, 0, 1]

            class_member_mask = (labels == k)
            digits_proj = TSNE(random_state=1).fit_transform(X_fit)

            xy = digits_proj[class_member_mask & core_samples_mask]
            plt.plot(
                xy[:, 0], xy[:, 1],
                'o', markerfacecolor=tuple(col),
                markeredgecolor='k', markersize=12)

            xy = digits_proj[class_member_mask & ~core_samples_mask]
            plt.plot(
                xy[:, 0], xy[:, 1],
                'o', markerfacecolor=tuple(col),
                markeredgecolor='k', markersize=6)

        plt.title('Estimated number of clusters: %d' % n_clusters_)
        plt.show()

    labels = labels.astype('str')
    labels = np.asarray(list(map(lambda x: "{:02d}".format(int(x)), labels)))

    # for i in np.unique(labels):
    #     print('Cluster %s count: ' % i, sum(labels == i))
    return labels, db


def change_labels(labels, cluster_name, idx_to_change, target_labels):
    """Helper function to change specific labels for a specific cluster/class
    and replace them with values provided as `target_labels`

    Args:
        labels (array):
            Collection of labels as strings
        cluster_name (str):
            Cluster/class that will be modified
        idx_to_change (array):
            Collection of idices with labels to be updated.
        target_labels (array):
            Collection of target labels to be used with `idx_to_change`

    Returns:
        array: Updated labels array
    """
    assert(type(idx_to_change) == list)
    assert(type(target_labels) == list)
    assert(len(idx_to_change) == len(target_labels))

    sub_list = labels[labels == cluster_name]

    for idx, target in zip(idx_to_change, target_labels):
        sub_list[idx] = target

    labels[labels == cluster_name] = sub_list

    return labels
