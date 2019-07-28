Python argparse wrapper to allow hierarchically nested class based parameters suitable for automatic code analysis especially in [Pycharm](https://www.jetbrains.com/pycharm/).
It also provides a unified parameter specification protocol that can be used to provide parameters through both text files and command line.

Please refer to the included parameter skeleton of a large multi object tracking project for which the functionality included in this package was originally developed.

It provides an excellent example of a highly modular project with deeply nested and shared modules.

For example, this is one of the deeper instances of module nesting in this example: Params->Trainer->Target->Templates->Siamese->SiamFC->DesignParams.

Parameter for this configuration can be provided as:

trainer.target.templates.siamese.siamfc.design.exemplar_sz=150






>



