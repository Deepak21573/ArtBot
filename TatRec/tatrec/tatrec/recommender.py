import pickle
from pathlib import Path
import os
import numpy as np
from fastai.metrics import error_rate
from fastai.vision import cnn_learner
from fastai.vision import models
from fastai.basic_data import load_data
# import sys
# Ensure tatrec package is in the path
# sys.path.append(os.path.join(Path.cwd(), "..", "tatrec"))
from .notebook_funcs import get_data_from_folder
from .config import (path_web_cleaned_chicago, path_web_upload,
                     path_web_models_chicago, path_web_data)


class TatRecommender:
    """
    A class used to represent a tattoo recommendation engine.

    Attributes:
        data: data to be used in the learner for predictions
        name: CNN model architecture
        sound: CNN learner class
        lsh: lsh model to search similarities of stored database of images
        n_items: number of items to return from lsh query
        path_img_upload: path to image upload on flask server
        distance_func: distance function used for lsh query
        lsh: lsh model to search similarities of stored database of images

    Methods:
        get_tattoo_recs(path_img_upload=path_web_upload)

    """
    def __init__(self):
        self.data = load_data(path_web_cleaned_chicago, "databunch-lsh.pkl")
        self.arch = models.resnet50
        self.learn = cnn_learner(self.data, self.arch, metrics=error_rate)
        self.learn.load("tatrec-stage-2-1")
        self.sf = SaveFeatures(self.learn.model[1][5])
        self.lsh = pickle.load(open(path_web_models_chicago + 'lsh.pkl', 'rb'))
        self.n_items = 5
        self.path_img_upload = path_web_upload
        self.distance_func = 'hamming'

    def get_tattoo_recs(self, path_img_upload=path_web_upload):
        """Gets the similar tattoo recommendations for the image in the upload folder

        Args
        ----------
        path_img_upload: path to the upload folder to use to train the input tattoo

        Returns
        -------
        Tuple of images paths that are the first self.n_items recommended images.

        """
        data = get_data_from_folder(path_img_upload, 1, 64)
        self.learn.data = data
        self.learn.get_preds(data.train_ds)[0]
        query = self.sf.features[-1].flatten()
        currentDirectory = Path(path_img_upload + 'train/user/')
        currentPattern = "*.jpg"
        in_dataset = False
        for currentFile in currentDirectory.glob(currentPattern):
            if os.path.basename(currentFile)[:14] == "tatrec--demo--":
                in_dataset = True
        if in_dataset:
            response = self.lsh.query(query, num_results=self.n_items + 1,
                                      distance_func=self.distance_func)
            img_rec1 = path_web_data + response[1][0][1][27:-4]
            img_rec2 = path_web_data + response[2][0][1][27:-4]
            img_rec3 = path_web_data + response[3][0][1][27:-4]
            img_rec4 = path_web_data + response[4][0][1][27:-4]
            img_rec5 = path_web_data + response[5][0][1][27:-4]
        else:
            response = self.lsh.query(query, num_results=self.n_items,
                                      distance_func=self.distance_func)
            img_rec1 = path_web_data + response[0][0][1][27:-4]
            img_rec2 = path_web_data + response[1][0][1][27:-4]
            img_rec3 = path_web_data + response[2][0][1][27:-4]
            img_rec4 = path_web_data + response[3][0][1][27:-4]
            img_rec5 = path_web_data + response[4][0][1][27:-4]
        #  FIXME Update this to work with n-items not first 5
        img_paths = (img_rec1, img_rec2, img_rec3, img_rec4, img_rec5)
        return img_paths


class SaveFeatures():
    """This is a hook (used for saving intermediate computations) used to extract before the last FC
    layer for use in similarity matching.

    Attributes:
        hook: the hook you want to grab data from
        features: extracted features

    Methods:
        hook_fn(module, input, output)
        remove()

    """
    features = None

    def __init__(self, m):
        self.hook = m.register_forward_hook(self.hook_fn)
        self.features = None

    def hook_fn(self, module, input, output):
        out = output.detach().cpu().numpy()
        if isinstance(self.features, type(None)):
            self.features = out
        else:
            self.features = np.row_stack((self.features, out))

    def remove(self):
        self.hook.remove()
