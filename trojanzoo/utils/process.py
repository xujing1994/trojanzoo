# -*- coding: utf-8 -*-

from .output import ansi, prints, output_iter
from trojanzoo.datasets import ImageSet
from trojanzoo.models import ImageModel
from .environ import env

import os
from typing import Union


class Process:

    name: str = 'process'

    def __init__(self, output: Union[int, list[str]] = 0, indent: int = 0, **kwargs):

        self.param_list = {}
        self.param_list['verbose'] = ['output', 'indent']

        self.output: list[str] = None
        self.output = self.get_output(output)
        self.indent = indent

    # -----------------------------------Output-------------------------------------#
    def summary(self, indent: int = None):
        if indent is None:
            indent = self.indent
        prints('{blue_light}{0:<20s}{reset} Parameters: '.format(self.name, **ansi), indent=indent)
        for key, value in self.param_list.items():
            prints('{green}{0:<20s}{reset}'.format(key, **ansi), indent=indent + 10)
            prints({v: getattr(self, v) for v in value}, indent=indent + 10)
            prints('-' * 20, indent=indent + 10)

    def get_output(self, org_output: Union[int, list[str]] = None) -> list[str]:
        output = None
        if org_output is None:
            output = self.output
        elif isinstance(org_output, list):
            output = set(org_output)
        elif isinstance(org_output, int):
            output = self.get_output_int(org_output)
        else:
            output = org_output
        return output

    def get_output_int(self, org_output: int = 0) -> list[str]:
        result: list[str] = []
        if org_output >= 5:
            result.append('end')
        if org_output >= 10:
            result.append('start')
        if org_output >= 20:
            result.append('middle')
        if org_output >= 30:
            result.append('memory')
        return result

    @staticmethod
    def output_iter(name: str, _iter, iteration=None, indent=0):
        string = name + ' Iter: ' + output_iter(_iter + 1, iteration)
        prints(string, indent=indent)


class Model_Process(Process):

    name: str = 'model_process'

    def __init__(self, dataset: ImageSet = None, model: ImageModel = None, folder_path: str = None, **kwargs):
        super().__init__(**kwargs)
        self.param_list['process'] = ['clean_acc', 'folder_path']
        self.dataset: ImageSet = dataset
        self.model: ImageModel = model

        _, self.clean_acc, _ = self.model._validate(print_prefix='Baseline Clean', get_data=None, verbose=False)
        # ----------------------------------------------------------------------------- #
        if folder_path is None:
            folder_path = env['result_dir']
            if dataset and isinstance(dataset, ImageSet):
                folder_path += dataset.name + '/'
            if model and isinstance(model, ImageModel):
                folder_path += model.name + '/'
            folder_path += self.name + '/'
        self.folder_path = folder_path
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)