<!-- No Heading Fix -->

<!-- MarkdownTOC -->

- [Introduction](#introductio_n_)
- [Imports](#imports_)
- [Sections](#section_s_)
    - [Hierarchical nesting](#hierarchical_nestin_g_)
    - [Replication](#replication_)
    - [Commands](#command_s_)
    - [Applications](#application_s_)
- [Placeholders](#placeholder_s_)

<!-- /MarkdownTOC -->

<a id="introductio_n_"></a>
# Introduction

Paramparse is a lightweight argparse wrapper to allow hierarchically nested class-based parameters suitable for automatic code analysis / intellisense  in advanced IDEs like [Pycharm](https://www.jetbrains.com/pycharm/).    
It also provides a unified parameter specification protocol that can be used to provide parameter values through both text files and command line.

Please refer to the included parameter skeleton of a large multi object tracking project for which the functionality included in this package was originally developed.
It provides an excellent example of a highly modular project with deeply nested and shared modules.

For example, this is one of the deeper instances of module nesting in this example: 

`Params->Trainer->Target->Templates->Siamese->SiamFC->DesignParams`

Parameter for this configuration can be provided as:

`trainer.target.templates.siamese.siamfc.design.exemplar_sz=150`

Specifying multiple parameters for a deeply nested module can quickly become cumbersome especially from command line.
The package thus provides a way to group parameters from the same module using the __@__ identifier.
An example is provided in [example/cfg/params.cfg](https://github.com/abhineet123/paramparse/blob/master/example/cfg/params.cfg).
Note that the indentation used in this file is only for ease of human parsing and is not needed as this system of grouping also works from command line.
Example commands are in [example/commands.md](https://github.com/abhineet123/paramparse/blob/master/example/commands.md).

The __@__ identifier specifies a prefix `pf` to be added to all subsequent arguments so that `arg_name` is then treated as `pf.arg_name`.    
Assuming `pf=arg1.arg2`, following flavors of __@__ identifier usage are supported:

| __usage__      | __effect__ | __pf__ |
| ----------- | ----------- | ----------- |
|`@arg3`      | reset `pf` to `arg3`       | `arg3`       |
|`@`   |     reset `pf` to empty    |         |
|`@@arg3`    | add `arg3` to `pf`     | `arg1.arg2.arg3`       |
|`@@@arg3`     | remove rightmost component of `pf` and add `arg3`     | `arg1.arg3`       |
|`@@@`      | remove rightmost component of `pf`       | `arg1`       |

Usage of the package is very simple and involves calling `paramparse.process` as demonstrated in [example/main.py](https://github.com/abhineet123/paramparse/blob/master/example/main.py).

__More detailed usage examples are available in [Deep MDP](https://github.com/abhineet123/deep_mdp) for which this parser was originally designed.https://github.com/abhineet123/deep_mdp __

It also provides three converter functions `from_parser`, `from_dict` and `from_function` that can create a parameter class compatible with this package from existing parameters in  `argparse.ArgumentParser` and `dict` formats or using a function's keyword arguments respectively.
The generated class code is either writen to a python source file whose name can be specified as the second argument (defaults to `Params.py`) or copied to clipboard if `to_clipboard=1` is provided (requires [pyperclip](https://pypi.org/project/pyperclip/)).

The `process` function does type inference from the default value of each param but also supports extracting the type from [restructuredText/pycharm type docstring](https://www.jetbrains.com/help/pycharm/using-docstrings-to-specify-types.html) (as generated by the converter functions) if it is provided.

__Note__ : `paramparse` uses the reserved parameter `cfg` to specify paths to text files containing parameter values.
If an existing argparse or dict object to be converted into `paramparse` class already has a `cfg` field used for some other purpose, it will conflict with the parser so please rename this field before or after converting but before running `paramparse.process`.

Usage of converter functions is demonstrated in [example/utils_demo.py](https://github.com/abhineet123/paramparse/blob/master/example/utils_demo.py)

Run `python3 main.py --h` from the example folder to see the hierarchical help documentation generated by argparse.

Apart from the hierarchical nesting and parameter grouping, an important utility of `paramparse` is in the class based representation that allows automated code analysis, navigation and refactoring in IDEs like Pycharm that is not possible when using vanilla `argparse.ArgumentParser` or `dict`.

<a id="imports_"></a>
# Imports
A cfg can be imported from within another using the `%import%` keyword followed by the relative path of that cfg with respect to the importing cfg. 

For example, the line
```
%import% dir3/imported.cfg
```
in `dir1/dir2/importing.cfg` will import `dir1/dir2/dir3/imported.cfg`.

Importing a CFG is equivalent to copying and pasting all the lines from the imported CFG into the importing CFG at the place where the `%import%` line is.

Recursive imports are supported and circular imports will raise an assertion error.

<a id="section_s_"></a>
# Sections
Sections provide a means to read a cfg file selectively rather than in its entirety.    
Each section is a named group of consecutive lines within a cfg file that is preceded and succeeded by a line starting with two or more `#`:
- preceding line specifies the name of the section
- succeeding line can either specify the name of the next section or simply mark the end of the current section if it is nameless
- lines without an explicit section are considered to be in an implicit `common` section that is always read while parsing a cfg (in addition to the specified sections)

<a id="hierarchical_nestin_g_"></a>
## Hierarchical nesting
Sections can be nested to any number of hierarchical levels
- level at which a section lies is determined by the number of `#` preceding its name 
    - `##` denotes level 1, `###` denotes level 2 and so on
    - lines starting with a single `#` are regarded as comments and ignored
- each section at level 2 or greater (i.e. with 3 or more `#` preceding its name) is considered to be nested within the nearest section before it that is one level above it
- a section can have multiple children
- a section can only have a single parent 
- a section can be included in a command only if all its ancestors have also been included 
- sections nested within different hierarchies in the same cfg file can have identical names

<a id="replication_"></a>
## Replication
Multiple sections can be started in a single line by specifying their names separated by commas
- all lines in such a multi-name section (inluding any section hierarchies therein) are replicated for each one of the names
- this can reduce redundancy when specifying sections that differ only in ways that can be derived from their names using [placeholders](#placeholders)
- long lists of numeric names can be specified succinctly using `range()` and `irange()` placeholders that can be used with 1, 2 or 3 arguments similar to the python `range` function, with `irange` being inclusive with respect to its upper bound
    - multiple disjointed ranges can be joined  with each other as well as with manually specified lists using `+` operator, e,g. range(3, 6)+irange(10, 13)+21,22 = 3,4,5,10,11,12,13,21,22

<a id="command_s_"></a>
## Commands
Sections are specified in a command by following the name of the cfg file with a colon (`:`) and a list of section names also separated with colons
- name of a parent section should precede that of its children
- if the cfg file has multiple identically-named sections in different hierarchies and only one of them is to be read (while reading all ancestors of more than one of them), its name should be separated from its parent by a hyphen (`-`) instead of a `:` 
- if a cfg file needs to be read again with a different section hierarchy, name of the root section of this hierarchy can be prefixed by `++` or `+++` 
    - `++` causes the common sections to be read again in addition to the new section hierarchy
    - `+++` causes the common sections to be be skipped so that only the new section hierarchy is read

<a id="application_s_"></a>
## Applications
Sections can have many uses:

- each section (or hierarchy thereof) can be used to specify the parameter values needed to run the script in a given configuration (or variants thereof)
- sections can be given short and intuitive names to quickly figure out exactly which configuration any given command corresponds to
- sections can make it very easy to switch between configurations with minimal changes to the commands
- hierarchical nesting of sections makes the relations between the different configurations explicit and easier to keep track of
- placeholders allow the names and values of parameters within a given section to be derived from the names of the section and its parents.

<a id="placeholder_s_"></a>
# Placeholders

Placeholders are reserved keywords that or variables will be replaced by their respective texts while parsing a cfg file.
Paramparse supports the following placeholders:

| __placeholder__      | __replacement__ |
| ----------- | ----------- | 
|`%N%`/`__name__`      | name of the section      |
|`%N<i>%`/`__name<i>__`      | `i`<sup>th</sup> component of the section name if that name is treated as being composed of underscore-separated components (`i` is 0-based and the enclosing `<>` is not part of the placeholder, e.g. with section name = `ab_cd_12_34` `%N0%`, `%N1%`, `%N2%` and `%N3%` respectively denote `ab`, `cd`, `12` and `34`) |
|`%N<i>*%`/`__name<i>*__`      | all components of the section name starting with the `i`<sup>th</sup> component joined with underscores (`i` >= 1, e.g. with section name = `ab_cd_12_34`, `%N1*%` and`%N2*%` respectively  denote `cd_12_34` and `12_34`) |
|`%P%`/`__parent__`      | name of the parent of the section      |
|`%GP%`/`__g_parent__`      | name of the grandparent of the section      |
|`%GGP%`/`__gg_parent__`      | name of the great grandparent of the section      |
|`%R%`/`__root__`      | name of the root section of the section's hierarchy    |
|`%F%`/`__full__`      | names of the section and its parent separated by an underscore    |
|`%PF%`/`__parent_full__`      | names of the section's parent and its grand parent separated by an underscore    |
|`%GF%`/`__g_full__`      | names of the section, its parent and its grandparent separated by underscores |
|`%GGF%`/`__gg_full__`      | names of the section, its parent, its grandparent and its great grandparent separated by underscores |
|`%RI%`/`__ratio__`      | name of the section interpreted as a number and divided by 100     |
|`%PRI%`/`__parent_ratio__`      | same as `__ratio__`  but with parent's name    |
|`%GPRI%`/`__g_parent_ratio__`      | same as `__ratio__`  but with grandparent's name    |
|`%GGPRI%`/`__gg_parent_ratio__`      | same as `__ratio__`  but with great grandparent's name    |
|`%L%`/`__list__`      |  name of the section converted into a list by splitting it with underscores (i.e. each component of its name separated by an underscore becomes an element of the list)     |
|`%PL%`/`__parent_list__`      | same as `__list__`  but with parent's name |
|`%GPL%`/`__g_parent_list__`      | same as `__list__`  but with grandparent's name |
|`%GGPL%`/`__gg_parent_list__`      | same as `__list__`  but with great grandparent's name |
|`%LRI%`/`__list_ratio__`      | same as `__list__` with each list member interpreted as a number and divided by 100     |
|`%PLRI%`/`__parent_list_ratio__`      | same as `__list_ratio__` but with parent's name     |
|`%GPLRI%`/`__g_parent_list_ratio__`      | same as `__list_ratio__` but with grandparent's name     |
|`%GGPLRI%`/`__gg_parent_list_ratio__`      | same as `__list_ratio__` but with great grandparent's name     |
|`%RA%`/`__range__`      | name of the section converted into a list by extracting 1, 2 or 3 underscore separated numbers and using them as arguments to the python `range` function |
|`%PRA%`/`__parent_range__`      | same as `__range__`  but with parent's name    |
|`%GPRA%`/`__g_parent_range__`      | same as `__range__`  but with grandparent's name    |
|`%GGPRA%`/`__gg_parent_range__`      | same as `__range__`  but with great grandparent's name    |
|`range()`      | generate a list with 1, 2 or 3 comma separated arguments within the parenthesis using similar syntax as the python `range`  function   |
|`irange()`      |  same as `range()`  but with inclusive upper bound  |

