Python argparse wrapper to allow hierarchically nested class based parameters suitable for automatic code analysis especially in [Pycharm](https://www.jetbrains.com/pycharm/).

It also provides a unified parameter specification protocol that can be used to provide parameters through both text files and command line.

Please refer to the included parameter skeleton of a large multi object tracking project for which the functionality included in this package was originally developed.

It provides an excellent example of a highly modular project with deeply nested and shared modules.

For example, this is one of the deeper instances of module nesting in this example: 

`Params->Trainer->Target->Templates->Siamese->SiamFC->DesignParams`

Parameter for this configuration can be provided as:

`trainer.target.templates.siamese.siamfc.design.exemplar_sz=150`

Specifying multiple parameters for a deeply nested module can quickly become cumbersome especially from command line.
The package thus provides a way to group parameters from the same module using the __@__ identifier.
An example is provided in [example/cfg/params.cfg](example/cfg/params.cfg).
Note that the indentation used in this file is only for ease of human parsing and is not needed as this system of grouping also works from command line.
Example commands are in [example/commands.md](example/commands.md)

Usage of the package is very simple and demonstrated in [main.py](example/main.py).

Apart from the `process` function, it also provides two utility functions `argparse.fromParser` and `argparse.fromDict` that can create a parameter class compatible with this package from existing parameters in  `argparse.ArgumentParser` and `dict` formats respectively.
The generated class code is writen to a python source file whose name can be specified as the second argument (defaults to `Params.py`).
Usage of both functions is demonstrated in [utils_demo.py](example/utils_demo.py)

Run `python3 main.py --h` from the example folder to see the hierarchical help documentation generated by argparse.

Apart from the hierarchical nesting and parameter grouping, an important utility is in the class based representation that allows automatic code analysis in IDEs like Pycharm that is not possible when using vanilla `argparse.ArgumentParser` or `dict`.





>



