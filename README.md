# TrojanZoo

> **NOTE:** TrojanZoo requires `python>=3.9.2`, `pytorch>=1.8.1` and `torchvision>=0.9.1`, which must be installed manually. Recommend to use `conda` to install.

This is the code implementation (pytorch) for our paper.

TrojanZoo provides a universal pytorch platform to conduct security researches (especially backdoor attacks/defenses) of image classification in deep learning. It is composed of two packages: `trojanzoo` and `trojanvision`. `trojanzoo` contains abstract classes and utilities, while `trojanvision` contains abstract and concrete ones for image classification task. 

## Features
1. **Colorful and verbose output!**
   > Note: enable with `--color` for color and `--verbose` for verbose.  
   To open an interactive window with color, use `python - --color`
2. Modular design (plug and play)
3. Good code linting support (this package requires `python>=3.9`)
4. Register **your own module** to the library.
5. Native Pytorch Output  
   `trojanzoo` and `trojanvision` provides API to generate raw pytorch instances, which makes it flexible to work with native `pytorch` and other 3rd party libraries.
   > `trojanzoo.datasets.DataSet` can generate `torch.utils.data.Dataset` and `torch.utils.data.DataLoader`  
   > `trojanzoo.models.Model` attribute `_model` is `torch.nn.Module`, attribute `model` is `torch.nn.DataParallel`  
   > Specifically, `trojanvision.datasets.ImageSet` can generate `torchvision.datasets.VisionDataset`, `trojanvision.datasets.ImageFolder` can generate `torchvision.datasets.ImageFolder`
6. Enable pytorch native AMP(Automatic Mixed Precision) with `--amp` for training
7. Flexible Configuration Files
8. Good help information to check arguments. (`-h` or `--help`)
9. Detailed and well-organized `summary()` for each module.

## Installation
1. `pip install trojanzoo`  
2. **(todo)** `conda install trojanzoo`  
3. **(RECOMMEND)**`python setup.py develop`  
    > This could install the github repo package but avoid copying files to `site_packages`, so that during developing `TrojanZoo`, you don't need move `example` files to the root directory of repo.  

## Quick Start

You can use the provided example scripts to reproduce the evaluation results in our paper.  
> Note: The program won't save results without `--save`  
1. Train a model:  
    e.g. `ResNet18` on `CIFAR10` with 95% Acc
    ```python3
    python ./examples/train.py --color --verbose 1 --dataset cifar10 --model resnet18_comp --lr_scheduler --cutout --grad_clip 5.0 --save
    ```

2. Test backdoor attack (e.g., BadNet):  
    e.g. `BadNet` with `ResNet18` on `CIFAR10`
    ```python3
    python ./examples/backdoor_attack.py --color --verbose 1 --pretrain --validate_interval 1 --dataset cifar10 --model resnet18_comp --attack badnet --random_init --epoch 50 --lr 0.01 --save
    ```

3. Test backdoor defense (e.g., Neural Cleanse):  
    e.g. `Neural Cleanse` against `BadNet`
    ```python3
    python ./examples/backdoor_defense.py --color --verbose 1 --pretrain --validate_interval 1 --dataset cifar10 --model resnet18_comp --attack badnet --defense neural_cleanse --random_init --epoch 50 --lr 0.01
    ```
## Detailed Usage
### Configuration file structure
All arguments in the parser are able to set default values in configuration files.  
If argument values are not set in the config files, we will use the default values of `__init__()`

Parameters Config: (priority ascend order)
> The higher priority config will override lower priority ones.  
> Within each priority channel, `trojanvision` configs will overwrite `trojanzoo`
1. Package Default: `/trojanzoo/configs/`, `/trojanvision/configs/`
   > These are package default settings. Please don't modify them.  
   > You can use this as a template to set other configs.
2. User Default: Not decided yet. 
   > (Enable it in the code `trojanzoo/configs/__init__.py`, `trojanvision/configs/__init__.py`)
3. Workspace Default: `/configs/trojanzoo/`, `/configs/trojanvision/`
4. Custom Config: `--config [config location]`
5. CMD parameters: `--[parameter] [value]`

### Store path of Dataset, Model, Attack & Defense Results  
Modify them in corresponding config files and command-line arguments. 
> Dataset: `--data_dir` (`./data/data`)  
> Model: `--model_dir` (`./data/model`)  
> Attack: `--attack_dir` (`./data/attack`)  
> Defense: `--defense_dir` (`./data/defense`)  


### Output Verbose Information:
1. CMD modules: `--verbose 1`
2. **Colorful output**: `--color`
3. **tqdm progress bar**: `--tqdm`
4. Check command-line argument usage: `--help`
5. AdvMind verbose information: `--output [number]`

### Use your DIY Dataset/Model/Attack/Defense
1. Follow our example to write your DIY class. (`CIFAR10`, `ResNet`, `IMC`, `Neural Cleanse`)
   > It's necessary to subclass our base class. (`Dataset`, `Model`, `Attack`, `Defense`)  
   > Optional base classes depending on your use case: (`ImageSet`, `ImageFolder`, `ImageModel`)
2. Register your DIY class in `trojanvision`
   > Example: `trojanvision.attacks.class_dict[attack_name]=AttackClass`
3. Create your config files if necessary.  
   No need to modify any codes. Just directly add `{attack_name}.yml` (`.json`) in the config directory.
4. Good to go!

## Todo List
1. Sphinx Docs  
2. **Unit test**

## License
TrojanZoo has a GPL-style license, as found in the [LICENSE](https://github.com/ain-soph/trojanzoo/blob/master/LICENSE) file.
