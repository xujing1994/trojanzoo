#!/usr/bin/env python3

from trojanzoo.environ import env
from trojanzoo.utils.output import ansi, prints
from trojanzoo.utils.tensor import repeat_to_batch

import torch
import torch.nn as nn
import torchvision.transforms as transforms

from collections import Callable
from typing import Iterator

__all__ = ['get_all_layer', 'get_layer', 'get_layer_name',
           'summary', 'activate_params', 'accuracy', 'generate_target']

filter_tuple: tuple[nn.Module] = (transforms.Normalize,
                                  nn.Dropout, nn.BatchNorm2d,
                                  nn.ReLU, nn.Sigmoid)


def get_layer_name(module: nn.Module, depth: int = -1, prefix: str = '',
                   use_filter: bool = True, non_leaf: bool = False,
                   seq_only: bool = False, init: bool = True) -> list[str]:
    r"""Get layer names of a :any:`torch.nn.Module`.

    Args:
        module (torch.nn.Module): the module to process.
        depth (int): The traverse depth.
            Defaults to ``-1`` (means :math:`\infty`).
        prefix (str): The prefix string to all elements.
            Defaults to empty string ``''``.
        use_filter (bool): Whether to filter out certain layer types.

            * :any:`torchvision.transforms.Normalize`
            * :any:`torch.nn.Dropout`
            * :any:`torch.nn.BatchNorm2d`
            * :any:`torch.nn.ReLU`
            * :any:`torch.nn.Sigmoid`
        non_leaf (bool): Whether to include non-leaf nodes.
            Defaults to ``False``.
        seq_only (bool): Whether to only traverse children
            of :any:`torch.nn.Sequential`.
            If ``False``, will traverse children of all :any:`torch.nn.Module`.
            Defaults to ``False``.

    Returns:
        list[str]: The list of all layer names.

    :Example:
        >>> import torchvision
        >>> from trojanzoo.utils.model import get_layer_name
        >>>
        >>> model = torchvision.models.resnet18()
        >>> get_layer_name(model, depth=0)
        []
        >>> get_layer_name(model, depth=1)
        ['conv1', 'maxpool', 'layer1', 'layer2',
        'layer3', 'layer4', 'avgpool', 'fc']
        >>> get_layer_name(model, depth=2, prefix='model')
        ['model.conv1', 'model.maxpool', 'model.layer1.0', 'model.layer1.1',
        'model.layer2.0', 'model.layer2.1', 'model.layer3.0', 'model.layer3.1',
        'model.layer4.0', 'model.layer4.1', 'model.avgpool', 'model.fc']
        >>> get_layer_name(model, seq_only=True)
        ['conv1', 'maxpool', 'layer1.0', 'layer1.1', 'layer2.0', 'layer2.1',
        'layer3.0', 'layer3.1', 'layer4.0', 'layer4.1', 'avgpool', 'fc']
        >>> get_layer_name(model, depth=2, seq_only=True, non_leaf=True)
        ['conv1', 'maxpool',
        'layer1.0', 'layer1.1', 'layer1',
        'layer2.0', 'layer2.1', 'layer2',
        'layer3.0', 'layer3.1', 'layer3',
        'layer4.0', 'layer4.1', 'layer4',
        'avgpool', 'fc']
        >>> get_layer_name(model)
        ['conv1', 'maxpool',
        'layer1.0.conv1', 'layer1.0.conv2', 'layer1.1.conv1', 'layer1.1.conv2',
        'layer2.0.conv1', 'layer2.0.conv2', 'layer2.0.downsample.0', 'layer2.1.conv1', 'layer2.1.conv2',
        'layer3.0.conv1', 'layer3.0.conv2', 'layer3.0.downsample.0', 'layer3.1.conv1', 'layer3.1.conv2',
        'layer4.0.conv1', 'layer4.0.conv2', 'layer4.0.downsample.0', 'layer4.1.conv1', 'layer4.1.conv2',
        'avgpool', 'fc']
    """
    layer_name_list: list[str] = []
    is_leaf = True
    if (init or (not seq_only or isinstance(module, nn.Sequential)))\
            and depth != 0:
        for name, child in module.named_children():
            full_name = prefix + ('.' if prefix else '') + name  # prefix=full_name
            layer_name_list.extend(get_layer_name(child, depth - 1, full_name,
                                                  use_filter, non_leaf, seq_only,
                                                  init=False))
            is_leaf = False
    if prefix and (not use_filter or filter_layer(module)) \
            and (non_leaf or depth == 0 or is_leaf):
        layer_name_list.append(prefix)
    return layer_name_list


def get_all_layer(module: nn.Module, x: torch.Tensor,
                  layer_input: str = 'input', depth: int = 0,
                  prefix='', use_filter: bool = True, non_leaf: bool = False,
                  seq_only: bool = True, verbose: int = 0
                  ) -> dict[str, torch.Tensor]:
    r"""Get all intermediate layer outputs of
    :attr:`_input` from any intermediate layer
    in a :any:`torch.nn.Module`.

    Args:
        module (torch.nn.Module): the module to process.
        x (torch.Tensor): The batched input tensor
            from :attr:`layer_input`.
        layer_input (str): The intermediate layer name of :attr:`x`.
            Defaults to ``'input'``.
        depth (int): The traverse depth.
            Defaults to ``0``.
        prefix (str): The prefix string to all elements.
            Defaults to empty string ``''``.
        use_filter (bool): Whether to filter out certain layer types.

            * :any:`torchvision.transforms.Normalize`
            * :any:`torch.nn.Dropout`
            * :any:`torch.nn.BatchNorm2d`
            * :any:`torch.nn.ReLU`
            * :any:`torch.nn.Sigmoid`
        non_leaf (bool): Whether to include non-leaf nodes.
            Defaults to ``False``.
        seq_only (bool): Whether to only traverse children
            of :any:`torch.nn.Sequential`.
            If ``False``, will traverse children of all :any:`torch.nn.Module`.
            Defaults to ``False``.
        verbose (bool): Whether to show verbose information
            including layer names and output shape.
            Defaults to ``True``.

    Returns:
        dict[str, torch.Tensor]: The dict of all layer outputs.

    :Example:
        >>> import torch
        >>> import torchvision
        >>> from trojanzoo.utils.model import get_all_layer
        >>>
        >>> model = torchvision.models.densenet121()
        >>> x = torch.randn(5, 3, 224, 224)
        >>> y = get_all_layer(model.features, x, verbose=True)
        layer name                                        output shape        module information
        conv0                                             [5, 64, 112, 112]   Conv2d
        pool0                                             [5, 64, 56, 56]     MaxPool2d
        denseblock1                                       [5, 256, 56, 56]    _DenseBlock
        transition1.conv                                  [5, 128, 56, 56]    Conv2d
        transition1.pool                                  [5, 128, 28, 28]    AvgPool2d
        denseblock2                                       [5, 512, 28, 28]    _DenseBlock
        transition2.conv                                  [5, 256, 28, 28]    Conv2d
        transition2.pool                                  [5, 256, 14, 14]    AvgPool2d
        denseblock3                                       [5, 1024, 14, 14]   _DenseBlock
        transition3.conv                                  [5, 512, 14, 14]    Conv2d
        transition3.pool                                  [5, 512, 7, 7]      AvgPool2d
        denseblock4                                       [5, 1024, 7, 7]     _DenseBlock
        >>> y.keys()
        dict_keys(['conv0', 'pool0',
        'denseblock1', 'transition1.conv', 'transition1.pool',
        'denseblock2', 'transition2.conv', 'transition2.pool',
        'denseblock3', 'transition3.conv', 'transition3.pool',
        'denseblock4'])
    """
    layer_name_list = get_layer_name(
        module, depth=depth, prefix=prefix, use_filter=False)
    if layer_input == 'input':
        layer_input = 'record'
    elif layer_input not in layer_name_list:
        print('Model Layer Name List: ', layer_name_list)
        print('Input layer: ', layer_input)
        raise ValueError('Layer name not in model')
    if verbose:
        print(f'{ansi["green"]}{"layer name":<50s}'
              f'{"output shape":<20}{"module information"}{ansi["reset"]}')
    return _get_all_layer(module, x, layer_input, depth,
                          prefix, use_filter, non_leaf,
                          seq_only, verbose=verbose, init=True)[0]


def _get_all_layer(module: nn.Module, x: torch.Tensor,
                   layer_input: str = 'record', depth: int = 0,
                   prefix: str = '', use_filter: bool = True,
                   non_leaf: bool = False, seq_only: bool = True,
                   verbose: int = 0, init: bool = False
                   ) -> tuple[dict[str, torch.Tensor], torch.Tensor]:
    _dict: dict[str, torch.Tensor] = {}
    if init or (not seq_only or isinstance(module, nn.Sequential)) \
            and depth != 0:
        for name, child in module.named_children():
            full_name = prefix + ('.' if prefix else '') + \
                name  # prefix=full_name
            if layer_input == 'record' or \
                    layer_input.startswith(f'{full_name}.'):
                sub_dict, x = _get_all_layer(child, x, layer_input, depth - 1,
                                             full_name, use_filter, non_leaf,
                                             seq_only, verbose)
                _dict.update(sub_dict)
                layer_input = 'record'
            elif layer_input == full_name:
                layer_input = 'record'
    else:
        x = module(x)
    if prefix and (not use_filter or filter_layer(module)) \
            and (non_leaf or depth == 0 or
                 not isinstance(module, nn.Sequential)):
        _dict[prefix] = x.clone()
        if verbose:
            shape_str = str(list(x.shape))
            module_str = ''
            if verbose == 1:
                module_str = module.__class__.__name__
            elif verbose == 2:
                module_str = type(module)
            elif verbose == 3:
                module_str = str(module).split('\n')[0].removesuffix('(')
            else:
                module_str = str(module)
            print(f'{ansi["blue_light"]}{prefix:<50s}{ansi["reset"]}'
                  f'{ansi["yellow"]}{shape_str:<20}{ansi["reset"]}'
                  f'{module_str}')
    return _dict, x


def get_layer(module: nn.Module, x: torch.Tensor, layer_output: str = 'output',
              layer_input: str = 'input',
              layer_name_list: list[str] = None,
              seq_only: bool = True) -> torch.Tensor:
    r"""Get one certain intermediate layer output
    of :attr:`_input` from any intermediate layer
    in a :any:`torch.nn.Module`.

    Args:
        module (torch.nn.Module): the module to process.
        x (torch.Tensor): The batched input tensor
            from :attr:`layer_input`.
        layer_output (str): The intermediate output layer name.
            Defaults to ``'classifier'``.
        layer_input (str): The intermediate layer name of :attr:`x`.
            Defaults to ``'input'``.
        seq_only (bool): Whether to only traverse children
            of :any:`torch.nn.Sequential`.
            If ``False``, will traverse children of all :any:`torch.nn.Module`.
            Defaults to ``True``.

    Returns:
        torch.Tensor: The output of layer :attr:`layer_output`.
    """
    if layer_input == 'input' and layer_output == 'output':
        return module(x)
    if layer_name_list is None:
        layer_name_list = get_layer_name(module, use_filter=False, non_leaf=True)
        layer_name_list.insert(0, 'input')
        layer_name_list.append('output')
    if layer_input not in layer_name_list \
        or layer_output not in layer_name_list \
            or layer_name_list.index(
                layer_input) > layer_name_list.index(layer_output):
        print('Model Layer Name List: \n', layer_name_list)
        print('Input  layer: ', layer_input)
        print('Output layer: ', layer_output)
        raise ValueError('Layer name not correct')
    if layer_input == 'input':
        layer_input = 'record'
    return _get_layer(module, x, layer_output, layer_input,
                      seq_only, init=True)


def _get_layer(module: nn.Module, x: torch.Tensor,
               layer_output: str = 'output', layer_input: str = 'record',
               prefix: str = '', seq_only: bool = True,
               init: bool = False) -> torch.Tensor:
    if init or (not seq_only or isinstance(module, nn.Sequential)):
        for name, child in module.named_children():
            full_name = prefix + ('.' if prefix else '') + \
                name  # prefix=full_name
            if layer_input == 'record' or \
                    layer_input.startswith(f'{full_name}.'):
                x = _get_layer(child, x, layer_output,
                               layer_input, full_name, seq_only)
                layer_input = 'record'
            elif layer_input == full_name:
                layer_input = 'record'
            if layer_output.startswith(full_name):
                return x
    else:
        x = module(x)
    return x


def filter_layer(module: nn.Module,
                 filter_tuple: tuple[nn.Module] = filter_tuple
                 ) -> bool:
    return not isinstance(module, filter_tuple)


def summary(module: nn.Module, depth: int = 0, verbose: bool = True,
            indent: int = 0, tree_length: int = None, indent_atom: int = 12
            ) -> None:
    tree_length = tree_length if tree_length is not None else indent_atom * \
        (depth + 1)
    if depth > 0:
        for name, child in module.named_children():
            _str = f'{ansi["blue_light"]}{name}{ansi["reset"]}'
            if verbose:
                _str = _str.ljust(tree_length - indent +
                                  len(ansi['blue_light']) + len(ansi['reset']))
                _str += str(child).split('\n')[0].removesuffix('(')
            prints(_str, indent=indent)
            summary(child, depth=depth - 1, indent=indent + indent_atom,
                    verbose=verbose, tree_length=tree_length)


def activate_params(module: nn.Module, params: Iterator[nn.Parameter]) -> None:
    module.requires_grad_(False)
    for param in params:
        param.requires_grad_()


def accuracy(_output: torch.Tensor, _label: torch.Tensor, num_classes: int,
             topk: tuple[int] = (1, 5)) -> list[float]:
    r"""Computes the accuracy over the k top predictions
    for the specified values of k
    """
    with torch.no_grad():
        maxk = min(max(topk), num_classes)
        batch_size = _label.size(0)
        _, pred = _output.topk(maxk, 1, True, True)
        pred = pred.t()
        correct = pred.eq(_label[None])
        res: list[float] = []
        for k in topk:
            if k > num_classes:
                res.append(100.0)
            else:
                correct_k = float(correct[:k].sum(dtype=torch.float32))
                res.append(correct_k * (100.0 / batch_size))
        return res


def generate_target(module: nn.Module, _input: torch.Tensor,
                    idx: int = 1, same: bool = False
                    ) -> torch.Tensor:
    with torch.no_grad():
        _output: torch.Tensor = module(_input)
    target = _output.argsort(dim=-1, descending=True)[:, idx]
    if same:
        target = repeat_to_batch(target.mode(dim=0)[0], len(_input))
    return target


# https://github.com/pytorch/vision/blob/main/references/classification/utils.py
class ExponentialMovingAverage(torch.optim.swa_utils.AveragedModel):
    r"""Maintains moving averages of model parameters using an exponential decay.
    ``ema_avg = decay * avg_model_param + (1 - decay) * model_param``

    See Also:
        `torch.optim.swa_utils.AveragedModel <https://pytorch.org/docs/stable/optim.html#stochastic-weight-averaging>`_
        is used to compute the EMA.
    """  # noqa: E501

    def __init__(self, model: nn.Module, decay: float):
        def ema_avg(avg_model_param: torch.Tensor, model_param: torch.Tensor,
                    num_averaged: torch.Tensor) -> torch.Tensor:
            return decay * avg_model_param + (1 - decay) * model_param

        super().__init__(model, device=env['device'], avg_fn=ema_avg)
        self.n_averaged: torch.Tensor
        self.module: nn.Module
        self.avg_fn: Callable[[torch.Tensor, torch.Tensor, torch.Tensor],
                              torch.Tensor]

    def update_parameters(self, model: nn.Module):
        for p_swa, p_model in zip(self.module.state_dict().values(),
                                  model.state_dict().values()):
            device = p_swa.device
            p_model_ = p_model.detach().to(device)
            if self.n_averaged.eq(0):
                p_swa.detach().copy_(p_model_)
            else:
                p_swa.detach().copy_(self.avg_fn(p_swa.detach(), p_model_,
                                                 self.n_averaged.to(device)))
        self.n_averaged += 1
