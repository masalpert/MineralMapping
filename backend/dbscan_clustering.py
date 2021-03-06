# import libraries
from sklearn.cluster import DBSCAN as dbscan
import pandas as pd
import numpy as np
from sklearn import metrics
import matplotlib.pyplot as plt
import matplotlib.colors
from sklearn.decomposition import PCA
from pathlib import Path
from skimage.io import imread, imshow
import numpy.ma as ma
from collections import Counter

# read the csv of mineral standards
standards = pd.read_csv('challenge_data/mineral_standards.csv')
# read the csv of predicted percent weights
df = pd.read_csv('challenge_data/predicted_percentweight_standard.csv')
# change NA values to 0
df = df.fillna(0)
x = df.values
# run DBSCAN Clustering
# Need to play with the eps and min_samples parameters to get reasonable results
# Future solution should loop through various parameter values to find reasonable obj1_minerals
# In general, to consolidate to fewer clusters, increase the parameters, and vicee versa
db = dbscan(eps = 10, min_samples = 20).fit(x)

core_samples_mask = np.zeros_like(db.labels_, dtype = bool)
core_samples_mask[db.core_sample_indices_] = True
labels = db.labels_
n_clusters_ = len(set(labels)) - (1 if -1 in labels else 0)
n_noise_ = list(labels).count(-1)

# See number of clusters and number of unclustered (noise) points
print('Estimated number of clusters: %d' % n_clusters_)
print('Estimated number of noise points: %d' % n_noise_)

# create a PCA for visualization
pca = PCA(n_components = 2)
principleComponents = pca.fit_transform(x)
principalDf= pd.DataFrame(data = principleComponents, columns = ['name1', 'name2'])
finalDf = pd.concat([principalDf, pd.Series(labels)], axis = 1)
final_minerals = pd.concat([principalDf, standards['mineral']], axis = 1)

mn = list(set(standards['mineral'].values))
color_dict = {}
for i, val in enumerate(mn):
    color_dict[val] = i
standards['mineral'].map(color_dict)

# add a cluster column
finalDf['cluster'] = labels

# plot PCA showing the different clusters
fig = plt.figure(figsize = (14,9))
ax1 = fig.add_subplot(1,1,1)
ax1.set_xlabel('Principal Component 1', fontsize = 15)
ax1.set_ylabel('Principal Component 2', fontsize = 15)
ax1.set_title('2 component PCA', fontsize = 20)
for c in np.unique(labels):
    ax1.scatter(finalDf['name1'][finalDf['cluster'] == c], finalDf['name2'][finalDf['cluster'] == c], label = c, s=40)
ax1.legend()
plt.savefig('./images/pca_predicteddata.png')

# add a mineral column
finalDf['mineral'] = standards['mineral']

# plot PCA showing the location of the actual minerals
np.unique(finalDf['mineral'])
fig = plt.figure(figsize = (14,9))
ax1 = fig.add_subplot(1,1,1)
ax1.set_xlabel('Principal Component 1', fontsize = 15)
ax1.set_ylabel('Principal Component 2', fontsize = 15)
ax1.set_title('2 component PCA', fontsize = 20)
# ax = fig.add_subplot(1,1,1)
for m in np.unique(finalDf['mineral']):
    ax1.scatter(finalDf['name1'][finalDf['mineral'] == m], finalDf['name2'][finalDf['mineral'] == m], label = m, s = 40)
ax1.legend()
plt.savefig('./images/pca_realdata.png')

# Clustering on object 1
# read csv of predicteed percent weights for object 1
df_obj1 = pd.read_csv('challenge_data/predicted_percentweight_obj1.csv')
df_obj1 = df_obj1.fillna(0)
df_obj1.drop('Unnamed: 0', axis = 1, inplace = True)
x = df_obj1.values
# Set cells with a percent weight lower than 5 to 0
# Could consider what a realistic cleaning threshold is
x[x < 5] = 0
# Run dbscan on object 1
# May need to adjust eps and min_samples for different images
db = dbscan(eps = 3, min_samples = 15).fit(x)

core_samples_mask = np.zeros_like(db.labels_, dtype = bool)
core_samples_mask[db.core_sample_indices_] = True
labels = db.labels_
n_clusters_ = len(set(labels)) - (1 if -1 in labels else 0)
n_noise_ = list(labels).count(-1)

# see number of clusters and noise
print('Estimated number of clusters: %d' % n_clusters_)
print('Estimated number of noise points: %d' % n_noise_)
unique_labels = set(labels)
colors = [plt.cm.Spectral(each) for each in np.linspace(0,1,len(unique_labels))]
for k, col in zip(unique_labels, colors):
    if k == -1:
        #Black used for n_noise_
        col = [0, 0, 0, 1]
    class_member_mask = (labels == k)

pca = PCA(n_components = 2)
principleComponents = pca.fit_transform(x)
principalDf= pd.DataFrame(data = principleComponents, columns = ['name1', 'name2'])
finalDf = pd.concat([principalDf, pd.Series(labels)], axis = 1)
finalDf['cluster'] = labels

# visualize clusters in PCA
fig = plt.figure(figsize = (14,9))
ax1 = fig.add_subplot(1,1,1)
ax1.set_xlabel('Principal Component 1', fontsize = 15)
ax1.set_ylabel('Principal Component 2', fontsize = 15)
ax1.set_title('2 component PCA', fontsize = 20)
for c in np.unique(labels):
    ax1.scatter(finalDf['name1'][finalDf['cluster'] == c], finalDf['name2'][finalDf['cluster'] == c], label = c, s=40)
ax1.legend()


root = Path("/Users/hellenfellows/OneDrive - AMNH/BridgeUp/HackathonRepo/MineralMapping/challenge_data/")
image_path = root / "dataset_1_opaques"
mask = imread(root / "dataset_1_opaques/obj1_mask.tif")
mask.sum()
# make mask binary
mask[mask > 0] = 1
mask = mask.astype('int64')
obj1_cluster = mask.copy()
# adjust cluster numbers so that nothing is <= 0
obj1_cluster[obj1_cluster == 1] = finalDf['cluster'] + 2

def get_cmap(n, name='hsv'):
    '''Returns a function that maps each index in 0, 1, ..., n-1 to a distinct
    RGB color; the keyword argument name must be a standard mpl colormap name.'''
    return plt.cm.get_cmap(name, n)

def discrete_cmap(N, base_cmap=None):
    """Create an N-bin discrete colormap from the specified input map"""
    # Note that if base_cmap is a string or None, you can simply do
    #    return plt.cm.get_cmap(base_cmap, N)
    # The following works for string, None, or a colormap instance:
    base = plt.cm.get_cmap(base_cmap)
    color_list = base(np.linspace(0, 1, N))
    cmap_name = base.name + str(N)
    return base.from_list(cmap_name, color_list, N)

# mask for object 1
obj1_cluster_masked = ma.masked_array(obj1_cluster, ~mask.astype(bool))

# show location of clusters on actual image of object 1
fig = plt.figure(figsize = (14,9))
plt.imshow(obj1_cluster_masked, cmap = 'tab10')
plt.savefig('./images/obj1_cluster_pred.png')

df_obj1['cluster'] = finalDf['cluster']
df_obj1.to_csv("df_obj1_cluster.csv")


# Clustering on object 2

df_obj2 = pd.read_csv('challenge_data/predicted_percentweight_obj2.csv')
df_obj2 = df_obj2.fillna(0)
df_obj2.drop('Unnamed: 0', axis = 1, inplace = True)
x = df_obj2.values
x[x < 5] = 0
# Run dbscan on object 2
db = dbscan(eps = 3, min_samples = 15).fit(x)

core_samples_mask = np.zeros_like(db.labels_, dtype = bool)
core_samples_mask[db.core_sample_indices_] = True
labels = db.labels_
n_clusters_ = len(set(labels)) - (1 if -1 in labels else 0)
n_noise_ = list(labels).count(-1)

print('Estimated number of clusters: %d' % n_clusters_)
print('Estimated number of noise points: %d' % n_noise_)

pca = PCA(n_components = 2)
principleComponents = pca.fit_transform(x)
principalDf= pd.DataFrame(data = principleComponents, columns = ['name1', 'name2'])
finalDf = pd.concat([principalDf, pd.Series(labels)], axis = 1)
finalDf['cluster'] = labels

fig = plt.figure(figsize = (14,9))
ax1 = fig.add_subplot(1,1,1)
ax1.set_xlabel('Principal Component 1', fontsize = 15)
ax1.set_ylabel('Principal Component 2', fontsize = 15)
ax1.set_title('2 component PCA', fontsize = 20)
for c in np.unique(labels):
    ax1.scatter(finalDf['name1'][finalDf['cluster'] == c], finalDf['name2'][finalDf['cluster'] == c], label = c, s=40)
ax1.legend()


root = Path("/Users/hellenfellows/OneDrive - AMNH/BridgeUp/HackathonRepo/MineralMapping/challenge_data/")
image_path = root / "dataset_1_opaques"
mask = imread(root / "dataset_1_opaques/obj2_mask.tif")
mask.sum()
mask[mask > 0] = 1
finalDf['cluster'].dtypes
mask = mask.astype('int64')
obj2_cluster = mask.copy()
obj2_cluster[obj2_cluster == 1] = finalDf['cluster'] + 2

def get_cmap(n, name='hsv'):
    '''Returns a function that maps each index in 0, 1, ..., n-1 to a distinct
    RGB color; the keyword argument name must be a standard mpl colormap name.'''
    return plt.cm.get_cmap(name, n)

def discrete_cmap(N, base_cmap=None):
    """Create an N-bin discrete colormap from the specified input map"""
    # Note that if base_cmap is a string or None, you can simply do
    #    return plt.cm.get_cmap(base_cmap, N)
    # The following works for string, None, or a colormap instance:
    base = plt.cm.get_cmap(base_cmap)
    color_list = base(np.linspace(0, 1, N))
    cmap_name = base.name + str(N)
    return base.from_list(cmap_name, color_list, N)


obj2_cluster_masked = ma.masked_array(obj2_cluster, ~mask.astype(bool))


fig = plt.figure(figsize = (14,9))
plt.imshow(obj2_cluster_masked, cmap = 'tab10')
plt.legend(obj2_cluster_masked)
plt.savefig('./images/obj2_cluster_pred.png')

# create csv with predicted weights and clusters
df_obj2['cluster'] = finalDf['cluster']
df_obj2.to_csv("df_obj2_cluster.csv")
