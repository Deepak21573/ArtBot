from fastai.vision import ImageList, imagenet_stats, get_transforms, ImageDataBunch
from fastai.vision.image import Transform
from lshash import LSHash
import matplotlib.pyplot as plt
from PIL import Image
import numpy as np
from pathlib import Path
from typing import Union, List
##################################################
# Notebook helper functions
##################################################


def get_data_from_folder(path: Union[Path, str], bs: int, img_size: int, tfms: Transform = None,
                         extensions: List[str] = [".jpg"]) -> ImageDataBunch:
    """Takes Imagenet style folder structure of test/train/valid and returns DataBunch with different
    batch and image sizes to train with PyTorch.

    Args:
        path : path to folder with data in train/valid/test folder structure
        bs : batch size
        img_size : resize to img_size for training
        tfms : transformations to do
        extensions : extensions to grab from the folder path

    Returns:
        data : Train/Test data organized in Fastai DataBunch

    """
    if tfms is None:
        tfms = get_transforms()

    data = (ImageList.from_folder(path, extensions=extensions)
            .split_by_folder()
            .label_from_folder()
            .transform(tfms, size=img_size)
            .databunch(bs=bs, num_workers=0).normalize(imagenet_stats))

    return data


def print_data_classes_size(data: ImageDataBunch) -> None:
    """Print number and name of data classes. Also, size of training and validation sets.

    Args:
        data: a fastai Databunch

    """
    print('Number of classes {0}'.format(data.c))
    print(data.classes)
    print('Train dataset size: {0}'.format(len(data.train_ds.x)))
    print('Test dataset size: {0}'.format(len(data.valid_ds.x)))


def plot_similar_tats_idx(idx: int, feature_dict: dict, lsh_variable: LSHash, n_items: int = 6,
                          distance_func: str = 'hamming') -> plt.Figure:
    """Takes an input index for the training set and plots the closest matching tattoos to that input
    tattoo.

    Args:
        idx : index to tattoo in the training set
        feature_dict : wraps both image locations and feature vectors at the output of the cnn
        before the final layer.
        lsh_variable : trained lsh model to query the input image
        n_items : number of items to return
        distance_func : The distance function. Currently it needs to be one of ("hamming",
        "euclidean", "true_euclidean", "centred_euclidean", "cosine", "l1norm"). By default
        "hamming" will used.

    Returns:
        Matplotlib grid plot of the index image first and n other similar images.

    """
    response = lsh_variable.query(feature_dict[list(feature_dict.keys())[idx]].flatten(),
                                  num_results=n_items + 1, distance_func=distance_func)

    return plot_similar_tats_query(response, n_items=n_items + 1, distance_func=distance_func)


def plot_similar_tats_query(lsh_response: dict, n_items: int = 6, distance_func: str =
                            'hamming') -> plt.Figure:
    """Takes a lsh query and plots the closest matching tattoos to that input tattoo.

    Args:
        lsh_response : lsh response variable containing a dictionary with values and image locations
        n_items : number of items to return
        distance_func : The distance function. Currently it needs to be one of ("hamming",
        "euclidean", "true_euclidean", "centred_euclidean", "cosine", "l1norm"). By default
        "hamming" will used.

    Returns:
        Matplotlib grid plot of the index image first and n other similar images.

    """
    columns = 3
    rows = int(np.ceil(n_items+1 / columns))
    fig = plt.figure(figsize=(2 * rows, 5 * rows))
    for i in range(1, columns*rows + 1):
        if i < n_items + 1:
            img = Image.open(lsh_response[i-1][0][1])
            fig.add_subplot(rows, columns, i)
            plt.imshow(img)
    return plt.show()
