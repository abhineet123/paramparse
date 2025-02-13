import copy
import sys
import os
import re
import json
import inspect
import argparse
from ast import literal_eval
from pprint import pformat
from datetime import datetime
from collections import defaultdict
from pydoc import locate
import numpy as np

# import time

try:
    import cPickle as pickle
except ImportError:
    import pickle

import docstring_parser_custom


# try:
#     import docstring_parser_custom
# except:
#     docstring_parser_custom = None

class RegexDict(dict):

    def __init__(self, _dict):
        super(RegexDict, self).__init__(_dict)

    def __getitem__(self, item):
        for k, v in self.items():
            if re.match(k, item):
                return v
        raise KeyError


class CFG:
    """
    convenience base class that any parameter class can inherit to
    avoid having to declare cfg specific parameters

    :ivar cfg: One or more plain text CFG files from which  to read parameter values;
    these will be overridden by commandline arguments
    :type cfg: tuple[str]

    :ivar cfg_ext: extension of the CFG files;
    this is automatically appended to the specified CFG files without any extension
    defaults to 'cfg' so that a file named cvat.cfg can be specified simply as cvat
    :type cfg_ext: str

    :ivar cfg_root: path to the folder containing CFG files;
    defaults to 'cfg' where all CFG files would be expected to be in a sub folder named cfg in the
    current working directory
    :type cfg_root: str

    :ivar cfg_prefix: prefix to be added to the names of all the CFG file;
    :type cfg_prefix: str

    :ivar cfg_suffix: suffix to be added to the names of all the CFG file;
    :type cfg_suffix: str
    """

    def __init__(self, **kwargs):
        self.cfg = ()
        self.cfg_root = 'cfg'
        self.cfg_ext = 'cfg'
        self.cfg_prefix = ''
        self.cfg_suffix = ''

        self.__dict__.update(kwargs)


class MultiString(str):
    def __init__(self, val, sep):
        str.__init__(val)
        self._sep = sep

    @staticmethod
    def _process(_str, _sep):
        """

        :param str _str:
        :param str _sep:
        :rtype:  str
        """
        tokens = _str.split(_sep)
        tokens = [strip_quotes(k) for k in tokens]
        token_str = _sep.join(tokens)
        token_str = token_str.replace(_sep + '!', '')
        return token_str


class MultiPath(MultiString):
    def __init__(self, val=''):
        MultiString.__init__(self, val, '_')

    @staticmethod
    def process(_str):
        """

        :param str _str:
        :rtype:  MultiPath
        """
        return MultiPath(MultiString._process(_str, _sep='_'))


class MultiCFG(MultiString):
    def __init__(self, val=''):
        MultiString.__init__(self, val, '::')

    @staticmethod
    def process(_str):
        """

        :param str _str:
        :rtype:  MultiCFG
        """
        return MultiCFG(MultiString._process(_str, _sep='::'))

    @staticmethod
    def to_dict(cfgs, valid_ids):
        """
        fill in missing cfg
        :param str cfgs:
        :param int n_iters:
        :rtype: dict
        """
        _cfgs_out = {}
        if not cfgs:
            return _cfgs_out

        # if ',,' not in cfgs:
        #     cfgs = '{},,'.format(cfgs)
        # cfg_tokens = [k for k in cfgs.split(',,') if k]

        # cfgs2 = cfgs.replace('",', '::').replace('"', '')

        cfg_tokens = cfgs.split('::')

        for i, cfg_token in enumerate(cfg_tokens):
            # if '::' not in _cfg:
            #     cfg_id = i
            # else:
            #     cfg_id, _cfg = _cfg.split('::')
            #     cfg_id = int(cfg_id)

            _cfg_list = cfg_token.split(':')
            cfg_id = _cfg_list[0]

            assert cfg_id in valid_ids, "Invalid cfg_id: {} in cfg token: {}".format(cfg_id, cfg_token)

            cfg_str = ':'.join(_cfg_list[1:])
            try:
                _cfgs_out[cfg_id] = '{},{}'.format(_cfgs_out[cfg_id], cfg_str)
            except KeyError:
                _cfgs_out[cfg_id] = cfg_str
        return _cfgs_out


class Node:
    """
    :type parent: Node
    :type full_name: str
    :type name: str
    :type orig_text: str
    :type parent_text: str
    """

    def __init__(self, heading_text='', parent=None, orig_text=None, parent_text=None,
                 # marker=None,
                 line_id=None, end_id=None, seq_id=None, curr_level=None, template_id=None):
        """

        :param str heading_text:
        :param Node | None parent:
        :param str orig_text:
        :param str parent_text:
        :param str marker:
        :param int line_id:
        :param int seq_id:
        """
        self.name = heading_text
        if not self.name:
            self.name = '__root__'

        if self.name.startswith('__') and self.name.endswith('__'):
            self.is_common = True
        else:
            self.is_common = False

        self.parent = parent
        self.orig_text = orig_text
        self.parent_text = parent_text
        # self.marker = marker
        self.line_id = line_id
        self.end_id = end_id
        self.seq_id = seq_id
        self.curr_level = curr_level
        self.template_id = template_id
        # self.is_included = False
        self.children = []

        self.added = 0

        if parent is None:
            self.is_root = True
            self.full_name = self.name
        else:
            self.is_root = False
            self.full_name = parent.name + self.name
            parent.children.append(self)

    def copy(self, **kwargs):
        new_node = Node(
            heading_text=self.name,
            parent=self.parent,
            orig_text=self.orig_text,
            parent_text=self.parent_text,
            line_id=self.line_id,
            end_id=self.end_id,
            seq_id=self.seq_id,
            curr_level=self.curr_level,
            template_id=self.template_id,
        )

        for _arg, _val in kwargs.items():
            setattr(new_node, _arg, _val)

        return new_node

    def get_descendants(self):
        descendants = []
        for child in self.children:
            descendants.append(child)
            descendants += child.get_descendants()
        return descendants

    def get_ancestors(self):
        ancestors = []
        parent = self.parent
        while parent is not None and not parent.is_root:
            ancestors.append(parent)
            parent = parent.parent
        return ancestors

    def p(self):
        return self.parent.name

    def gp(self):
        return self.parent.parent.name

    def ggp(self):
        return self.parent.parent.parent.name

    def gf(self):
        return f'{self.name}_{self.p()}_{self.gp()}'

    def ggf(self):
        return f'{self.name}_{self.p()}_{self.gp()}_{self.ggp()}'

    @staticmethod
    def name_to_ratio(name):
        return str(float(name) / 100.0)

    def ri(self):
        return self.name_to_ratio(self.name)

    def pri(self):
        return self.name_to_ratio(self.p())

    def gpri(self):
        return self.name_to_ratio(self.gp())

    def ggpri(self):
        return self.name_to_ratio(self.ggp())

    @staticmethod
    def name_to_list(name):
        return ','.join(name.split('_'))

    def l_(self):
        return self.name_to_list(self.name)

    def pl(self):
        return self.name_to_list(self.p())

    def gpl(self):
        return self.name_to_list(self.gp())

    def ggpl(self):
        return self.name_to_list(self.ggp())

    @staticmethod
    def name_to_list_ratio(_name):
        temp = _name.split('_')
        for k_id, k in enumerate(temp):
            if k.startswith('n'):
                k = k.replace('n', '-')
            k = str(float(k) / 100.0)
            temp[k_id] = k
        return ','.join(temp)

    def lri(self):
        return self.name_to_list_ratio(self.name)

    def plri(self):
        return self.name_to_list_ratio(self.p())

    def gplri(self):
        return self.name_to_list_ratio(self.gp())

    def ggplri(self):
        return self.name_to_list_ratio(self.ggp())

    @staticmethod
    def name_to_range(name):
        return ':'.join(name.split('_'))

    def ra(self):
        return self.name_to_range(self.name)

    def pra(self):
        return self.name_to_range(self.p())

    def gpra(self):
        return self.name_to_range(self.gp())

    def ggpra(self):
        return self.name_to_range(self.ggp())


def obj_from_docs(obj, member, verbose=False):
    doc_dict = getattr(type(obj), '__doc_dict__', None)
    if doc_dict is None:
        doc_dict = {}
        dict_from_docs(type(obj), doc_dict, verbose)
        setattr(type(obj), '__doc_dict__', doc_dict)

    return literal_eval(doc_dict[member]['help'])


def match_opt(params, opt_name, verbose, print_name=''):
    """

    :param params:
    :param str opt_name:
    :param str print_name:
    :return:
    """

    if not print_name:
        print_name = opt_name

    opt_val = str(getattr(params, opt_name))
    opt_vals = obj_from_docs(params, opt_name, verbose)  # type: dict

    matching_val = [k for k in opt_vals.keys() if opt_val in [str(_val) for _val in opt_vals[k]]]
    assert matching_val, "No matches found for {} {} in\n{}".format(print_name, opt_val, pformat(opt_vals))
    assert len(matching_val) == 1, "Multiple matches for {} {} found: {}".format(print_name, opt_val, matching_val)

    return matching_val[0]


def _find_children(nodes, nodes_by_fullname, _headings, root_level, _start_id, _root_node, n_headings):
    """

    :param dict nodes:
    :param defaultdict(list) | None nodes_by_fullname:
    :param _headings:
    :param root_level:
    :param _start_id:
    :param _root_node:
    :param n_headings:
    :return:
    """
    _id = _start_id

    while _id < n_headings:
        _heading, line_id, end_id, curr_level, template_id = _headings[_id]
        assert _heading, "Invalid empty heading found"

        # curr_level = _heading[0].count('#') + 1

        if curr_level <= root_level:
            break

        parent_text = ''
        if _root_node is not None and _root_node.parent is not None:
            parent_text = _root_node.name
            if curr_level > 2:
                # parent_text = str(_root_node)
                parent_text = '{}/{}'.format(parent_text, _root_node.parent_text)
        new_node = Node(_heading, parent=_root_node, orig_text=_heading, parent_text=parent_text,
                        # marker=_heading[0],
                        line_id=line_id, end_id=end_id, seq_id=_id, curr_level=curr_level, template_id=template_id)
        nodes[_id] = new_node

        if nodes_by_fullname is not None:
            # assert new_node.full_name not in nodes_by_fullname, \
            #     "Duplicate nodes found with full_name {}:\n{}\n{}".format(new_node.full_name, new_node.name,
            #                                                               nodes_by_fullname[new_node.full_name].name)
            nodes_by_fullname[new_node.full_name].append(new_node)

        ___id = _find_children(nodes, nodes_by_fullname, _headings, curr_level, _id + 1, new_node, n_headings)
        # nodes += child_nodes
        _id = ___id

    return _id


def scalar_to_string(val, add_quotes=False):
    if isinstance(val, (int, bool)):
        return '{:d}'.format(int(val))
    elif isinstance(val, float):
        return '{:f}'.format(val)
    elif isinstance(val, str):
        if add_quotes:
            return "'{:s}'".format(val)
        else:
            return val
    print('Invalid scalar: ', val)
    return None


def tuple_to_string(vals):
    _str = ''
    for val in vals:
        if isinstance(val, (int, bool, float, str)):
            _str = '{:s}{:s},'.format(_str, scalar_to_string(val, True))
        elif isinstance(val, (tuple, list)):
            _str = '{:s}{:s},'.format(_str, tuple_to_string(val))
        elif isinstance(val, dict):
            _str = '{:s}{:s},'.format(_str, dict_to_string(val))
    return '({:s})'.format(_str)


def dict_to_string(vals):
    _str = '{{'
    for key in vals.keys():
        val = vals[key]
        key_str = scalar_to_string(key)
        if isinstance(val, (int, bool, float, str)):
            val_str = scalar_to_string(val)
        elif isinstance(val, (tuple, list)):
            val_str = tuple_to_string(val)
        elif isinstance(val, dict):
            val_str = dict_to_string(val)
        else:
            raise TypeError('invalid scalar type for {}: {}'.format(val, type(val).__name__))

        _str = '{:s}{:s}:{:s},'.format(_str, key_str, val_str)
    _str += '}}'
    return _str


def strip_quotes(val):
    return val.strip("\'").strip('\"')


def str_to_tuple_multi(val):
    vals = val.split('+')
    out_list = []
    for _val in vals:
        out_list += list(str_to_tuple(_val))
    return tuple(out_list)


def safer_arange(start, stop, step):
    return step * np.arange(start / step, stop / step)


def str_to_tuple(val):
    if val.startswith('range('):
        """standard (exclusive) range"""
        val_list = val[6:].replace(')', '').split(',')
        val_list = [int(x) for x in val_list]
        val_list = tuple(range(*val_list))
        return val_list
    elif val.startswith('irange('):
        """inclusive range"""
        val_list = val.replace('irange(', '').replace(')', '').split(',')
        val_list = [int(x) for x in val_list]

        if len(val_list) == 1:
            val_list[0] += 1
        elif len(val_list) >= 2:
            val_list[1] += 1
        val_list = tuple(range(*val_list))
        return val_list
    elif ':' in val:
        """Try to parse the string as a floating point range specification - both inclusive and exclusive
        """
        try:
            _val = val
            inclusive_start = inclusive_end = 1
            if _val.endswith(')'):
                _val = _val[:-1]
                inclusive_end = 0
            if val.startswith('('):
                _val = _val[1:]
                inclusive_start = 0
            _temp = [float(k) for k in _val.split(':')]
            if len(_temp) == 3:
                _step = _temp[2]
            else:
                _step = 1.0
            if inclusive_end:
                _temp[1] += _step
            if not inclusive_start:
                _temp[0] += _step
            return tuple(safer_arange(*_temp))
        except BaseException as e:
            pass
    if any(k in val for k in ('(', '{', '[')):
        # nested tuple
        return literal_eval(val)
    else:
        if ',' not in val:
            val = '{},'.format(val)
        arg_vals = [x for x in val.split(',')]
        if not arg_vals[-1]:
            del arg_vals[-1]
        arg_vals_parsed = []
        for _val in arg_vals:
            _val_parsed = str_to_basic_type(_val)
            arg_vals_parsed.append(_val_parsed)
        return arg_vals_parsed


def linux_path(*args, **kwargs):
    return os.path.join(*args, **kwargs).replace(os.sep, '/')


def str_to_basic_type(_val):
    # if _type == str:
    #     _val_parsed = _val
    #     if _val_parsed == '__n__':
    #         _val_parsed = ''
    #     return _val_parsed

    if not _val:
        return _val

    """try parsing in decreasing order of specificity --> int, float, str"""

    """allow k,m,g,t,p terminated specification for large integers: kilo, mega, giga, tera, peta"""
    if all(c.isdigit() for c in _val[:-1]):
        if _val[-1] == 'k':
            _val = _val.replace('k', '000')
        if _val[-1] == 'm':
            _val = _val.replace('m', '000000')
        if _val[-1] == 'g':
            _val = _val.replace('g', '000000000')
        if _val[-1] == 't':
            _val = _val.replace('t', '000000000000')
        if _val[-1] == 'p':
            _val = _val.replace('t', '000000000000000')
    try:
        _val_parsed = int(_val)
    except ValueError:
        try:
            _val_parsed = float(_val)
        except ValueError:
            """remove trailing and leading quotes"""
            _val_parsed = strip_quotes(_val)

    if _val_parsed == '__n__':
        _val_parsed = ''

    return _val_parsed


def copy_recursive(src, dst=None, include_protected=1):
    valid_members = get_valid_members(src, include_protected=include_protected)

    if dst is None:
        dst = type(src)()

    try:
        copy_excluded = getattr(src, '_copy_excluded')
    except AttributeError:
        copy_excluded = []

    for member in valid_members:
        if member == 'help':
            continue

        member_val = getattr(src, member)
        if member in copy_excluded or member_val is None or isinstance(member_val, (
                int, bool, float, str, MultiPath, MultiCFG, tuple)):
            setattr(dst, member, member_val)
        elif isinstance(member_val, (dict, list)):
            setattr(dst, member, member_val.copy())
        else:
            # dst_member = getattr(dst, member)
            member_val_copy = copy_recursive(member_val, include_protected=include_protected)
            setattr(dst, member, member_val_copy)
    return dst


def save(obj, dir_name, out_name='params.bin'):
    save_path = linux_path(dir_name, out_name)
    pickle.dump(obj, open(save_path, "wb"))


def load(obj, dir_name, prefix='', out_name='params.bin'):
    load_path = linux_path(dir_name, out_name)
    params = pickle.load(open(load_path, "rb"))
    missing_params = []
    _recursive_load(obj, params, prefix, missing_params)
    if missing_params:
        print('Missing loaded parameters found:\n{}'.format(pformat(missing_params)))


def write(obj, dir_name, prefix='', out_name='params.cfg'):
    save_path = linux_path(dir_name, out_name)
    save_fid = open(save_path, "w")
    _recursive_write(obj, prefix, save_fid)


def read(obj, dir_name, prefix='', out_name='params.cfg', allow_unknown=0):
    load_path = linux_path(dir_name, out_name)
    lines = open(load_path, "r").readlines()
    if prefix:
        lines = [k.replace(prefix + '.', '') for k in lines if k.startswith(prefix + '.')]
    args_in = ['--{}'.format(k.strip()) for k in lines]
    process(obj, args_in=args_in, prog=prefix,
            usage=None, allow_unknown=allow_unknown)


def _recursive_load(obj, loaded_obj, prefix, missing_params):
    load_members = get_valid_members(loaded_obj)
    obj_members = get_valid_members(obj)

    for member in obj_members:
        member_name = '{:s}.{:s}'.format(prefix, member) if prefix else member
        if member not in load_members:
            missing_params.append(member_name)
            continue
        default_val = getattr(obj, member)
        load_val = getattr(loaded_obj, member)
        if isinstance(default_val, (int, bool, float, str, tuple, list, dict, MultiPath, MultiCFG)):
            setattr(obj, member, load_val)
        else:
            _recursive_load(default_val, load_val, member_name, missing_params)


def _recursive_write(obj, prefix, save_fid):
    obj_members = get_valid_members(obj)

    for member in obj_members:
        if member == 'help':
            continue
        member_val = getattr(obj, member)
        member_name = '{:s}.{:s}'.format(prefix, member) if prefix else member
        if isinstance(member_val, (int, bool, float, str, MultiPath, MultiCFG)):
            save_fid.write('{:s}={:s}\n'.format(member_name, scalar_to_string(member_val)))
        elif isinstance(member_val, (tuple, list)):
            save_fid.write('{:s}={:s}\n'.format(member_name, tuple_to_string(member_val)))
        elif isinstance(member_val, dict):
            save_fid.write('{:s}={:s}\n'.format(member_name, dict_to_string(member_val)))
        else:
            _recursive_write(member_val, member_name, save_fid)


def to_dict(obj):
    """

    :param obj:
    :rtype: dict
    """
    obj_dict = {}
    obj_members = get_valid_members(obj)

    for member in obj_members:
        if member == 'help':
            continue

        member_val = getattr(obj, member)
        if isinstance(member_val, (int, bool, float, str, MultiPath, MultiCFG, tuple, list, dict)):
            obj_dict[member] = member_val
        else:
            obj_dict[member] = to_dict(member_val)

    return obj_dict


def _match_template(start_templ, member_templ, _str, exclude_starts):
    _match = ''

    doc_para = _str.split(start_templ)
    relevant_para = [k for k in doc_para if k.startswith(member_templ)]

    if not relevant_para:
        return _match

    assert len(relevant_para) == 1, "multiple matches found for {} {} in:\n{}".find(start_templ, member_templ, _str)

    relevant_para = relevant_para[0]
    _help_lines = relevant_para.splitlines()
    if exclude_starts:
        _help_lines = [k for k in _help_lines if not any(k.startswith(_start) for _start in exclude_starts)]

    _match = ' '.join(_help_lines)[len(member_templ):]

    return _match


def dict_from_str(string, verbose):
    # if docstring_parser_custom is None:
    #     if verbose:
    #         print('docstring parser is not available')
    #     return {}

    docstring = docstring_parser_custom.parse(string)

    type_dict = defaultdict(lambda: None)
    param_type_dict = {_meta.args[2]: locate(_meta.args[1]) for _meta in docstring.meta if
                       len(_meta.args) == 3 and _meta.args[0] == 'param'}
    main_type_dict = {_meta.args[1]: locate(_meta.description) for _meta in docstring.meta if _meta.args[0] == 'type'}
    type_dict.update(param_type_dict)
    type_dict.update(main_type_dict)

    help_dict = defaultdict(lambda: None)
    param_help_dict = {_meta.args[-1]: _meta.description for _meta in docstring.meta if _meta.args[0] == 'param'}
    ivar_help_dict = {_meta.args[1]: _meta.description for _meta in docstring.meta if _meta.args[0] == 'ivar'}
    help_dict.update(param_help_dict)
    help_dict.update(ivar_help_dict)

    members = set(list(type_dict.keys()) + list(help_dict.keys()))

    combined_dict = {
        _member: {
            'help': help_dict[_member],
            'type': type_dict[_member],
        }
        for _member in members
    }

    combined_dict['__description__'] = (docstring.short_description, docstring.long_description)

    return combined_dict


def dict_from_docs(obj_type, doc_dict, verbose):
    if obj_type in doc_dict:
        return

    class_hierarchy = inspect.getmro(obj_type)[:-1][::-1]
    obj_help_dict = {}
    for _class in class_hierarchy:
        if _class in doc_dict:
            curr_dict = doc_dict[_class]
        else:
            doc = inspect.getdoc(_class)
            if doc is None:
                continue
            curr_dict = dict_from_str(doc, verbose)
            doc_dict[_class] = curr_dict

        obj_help_dict.update(curr_dict)

    doc_dict[obj_type] = obj_help_dict


def help_from_docs(obj, member):
    _help = ''

    class_hierarchy = inspect.getmro(type(obj))[:-1][::-1]
    all_doc = ''
    for _class in class_hierarchy:

        doc = inspect.getdoc(_class)
        if doc is not None:
            all_doc += doc + '\n'

    if not all_doc:
        return _help

    doc_lines = all_doc.splitlines()
    if not doc_lines:
        return _help

    filtered_lines = [k.strip() for k in doc_lines]
    filtered_lines = list(filter(lambda k: k and not k.startswith(':type ') and not k.startswith('#'), filtered_lines))

    filtered_str = '\n'.join(filtered_lines)

    start_templ = ':param '
    member_templ = '{} {}: '.format(type(getattr(obj, member)).__name__, member)

    start_templ2 = ':ivar '
    member_templ2 = '{}: '.format(member)

    _help = _match_template(start_templ, member_templ, filtered_str, (start_templ2,))
    if _help:
        return _help

    _help = _match_template(start_templ2, member_templ2, filtered_str, (start_templ,))
    return _help


_supported_types = (int, bool, float, str, tuple, list, dict, tuple, list, dict, MultiPath, MultiCFG)


def type_from_docs(obj, member):
    doc = inspect.getdoc(obj)
    if doc is None:
        return None

    doc_lines = doc.splitlines()
    if not doc_lines:
        return None

    templs = [(':param {} {}: '.format(k.__name__, member), k) for k in _supported_types]
    relevant_lines = [k for k in doc_lines if any(k.startswith(templ[0]) for templ in templs)]

    if not relevant_lines:
        templs2 = [(':type {}: {}'.format(member, k.__name__), k) for k in _supported_types]
        relevant_lines = [k for k in doc_lines if any(k.startswith(templ[0]) for templ in templs)]

        if not relevant_lines:
            return None

    if len(relevant_lines) > 1:
        print('Multiple matching docstring lines for {}:\n{}'.format(member, pformat(relevant_lines)))
        return None

    relevant_line = relevant_lines[0]
    if relevant_line:
        relevant_templs = [templ for templ in templs if relevant_line.startswith(templ[0])]
        if len(relevant_lines) > 1:
            print('Multiple matching templates for {} with docstring line {}:\n{}'.format(
                member, relevant_line, pformat(relevant_templs)))
            return None
        return relevant_templs[0][1]

    return None


def get_valid_members(obj, include_protected=0):
    obj_t = type(obj)
    prop_attr = [attr for attr in dir(obj_t) if isinstance(getattr(obj_t, attr), property)]
    valid_members = tuple([attr for attr in dir(obj) if
                           attr not in prop_attr and
                           not callable(getattr(obj, attr))
                           and not attr.startswith("__")
                           and (include_protected or not attr.startswith("_"))
                           ])

    return valid_members


def _add_params_to_parser(parser, obj, member_to_type, doc_dict, root_name='', obj_name='', verbose=0):
    """

    :param argparse.ArgumentParser parser:
    :param obj:
    :param dict member_to_type:
    :param dict doc_dict:
    :param str root_name:
    :param str obj_name:
    :return:
    """
    members = get_valid_members(obj)

    obj_type = type(obj)

    assert members, "Invalid composite object with no component members found: {} (type: {})".format(
        obj, obj_type)

    dict_from_docs(obj_type, doc_dict, verbose)

    obj_doc_dict = doc_dict[obj_type]
    setattr(type(obj), '__doc_dict__', obj_doc_dict)

    if obj_name:
        if root_name:
            root_name = '{:s}.{:s}'.format(root_name, obj_name)
        else:
            root_name = '{:s}'.format(obj_name)
    for member in members:
        if member == 'help':
            continue

        default_val = getattr(obj, member)
        # member_type = type_from_docs(obj, member)

        try:
            member_type = obj_doc_dict[member]['type']
        except KeyError:
            member_type = None

        if member_type is None:
            if default_val is None:
                if verbose:
                    print('No type found in docstring for param {} with default as None'.format(member))
                continue
            # print('Deduced type {} from docstring for param {} with default as None'.format(member_type, member))
            else:
                member_type = type(default_val)

        if member_type in (int, bool, float, str, tuple, list, dict, MultiCFG, MultiPath):

            if root_name:
                member_param_name = '{:s}.{:s}'.format(root_name, member)
            else:
                member_param_name = '{:s}'.format(member)

            member_to_type[member_param_name] = member_type

            # if member_type in (MultiCFG, MultiPath):
            #     print()

            if hasattr(obj, 'help') and member in obj.help:
                _help = obj.help[member]
                if not isinstance(_help, str):
                    _help = pformat(_help)
            else:
                try:
                    _help = obj_doc_dict[member]['help']
                except KeyError:
                    _help = ''

                # _help = help_from_docs(obj, member)

            if member_type in (tuple, list):
                parser.add_argument('--{:s}'.format(member_param_name), type=str_to_tuple,
                                    default=default_val, help=_help, metavar='')
            elif member_type is dict:
                parser.add_argument('--{:s}'.format(member_param_name), type=json.loads, default=default_val,
                                    help=_help, metavar='')
            elif member_type in (MultiCFG, MultiPath):
                parser.add_argument('--{:s}'.format(member_param_name), type=member_type.process, default=default_val,
                                    help=_help, metavar='')
            elif member_type is str:
                parser.add_argument('--{:s}'.format(member_param_name), type=strip_quotes, default=default_val,
                                    help=_help, metavar='')
            elif member_type in (int, bool, float, str):
                parser.add_argument('--{:s}'.format(member_param_name), type=str_to_basic_type, default=default_val,
                                    help=_help, metavar='')
            else:
                raise AssertionError('Something weird going on with member_type: {}'.format(member_type))
        else:
            # parameter is itself an instance of some other parameter class so its members must
            # be processed recursively
            _add_params_to_parser(parser, getattr(obj, member), member_to_type, doc_dict, root_name, member,
                                  verbose=verbose)


def _assign_arg(obj, arg, _id, val, member_to_type, parent_name):
    """

    :param obj:
    :param list arg:
    :param int _id:
    :param val:
    :param dict member_to_type:
    :param str parent_name:
    :return:
    """
    if _id >= len(arg):
        print('Invalid arg: {} with _id: {}'.format(arg, _id))
        return

    _arg = arg[_id]
    obj_attr = getattr(obj, _arg)
    obj_attr_name = '{}.{}'.format(parent_name, _arg) if parent_name else _arg
    if obj_attr is None:
        # _key = '--{}'.format(obj_attr_name)
        obj_attr_type = member_to_type[obj_attr_name]
    else:
        obj_attr_type = type(obj_attr)

    if obj_attr_type in _supported_types:
        if val == '#' or val == '__n__':
            if isinstance(obj_attr, str):
                # empty string
                val = ''
            elif isinstance(obj_attr, tuple):
                # empty tuple
                val = ()
            elif isinstance(obj_attr, list):
                # empty list
                val = []
            elif isinstance(obj_attr, dict):
                # empty dict
                val = {}
        setattr(obj, _arg, val)
    else:
        # parameter is itself an instance of some other parameter class so its members must
        # be processed recursively
        _assign_arg(obj_attr, arg, _id + 1, val, member_to_type, obj_attr_name)


def _process_args_from_parser(obj, args, member_to_type):
    """

    :param obj:
    :param Namespace args:
    :param dict member_to_type:
    :return:
    """
    # arg_prefix = ''
    # if hasattr(obj, 'arg_prefix'):
    #     arg_prefix = obj.arg_prefix

    # optionals = parser._optionals._option_string_actions
    # positionals = parser._positionals._option_string_actions

    # all_params = optionals.copy()
    # all_params.update(positionals)

    members = vars(args)
    for key in members.keys():
        val = members[key]
        key_parts = key.split('.')
        _assign_arg(obj, key_parts, 0, val, member_to_type, '')


def recursive_read(cfg, imported_cfgs=(), level=0):
    indent = '\t' * level
    print(f'{indent}Reading parameters from {cfg:s}')
    file_args = [k.strip() for k in open(cfg, 'r').readlines()]

    cfg_dir = os.path.dirname(cfg)

    out_file_args = []
    out_imported_cfgs = [cfg, ]

    for file_arg_id, file_arg in enumerate(file_args):
        if file_arg.startswith('%import% '):
            _, imported_cfg_name = file_arg.split(' ')
            imported_cfg = linux_path(cfg_dir, imported_cfg_name)
            prev_imported_cfgs = tuple(set(imported_cfgs + tuple(out_imported_cfgs)))

            assert imported_cfg not in prev_imported_cfgs, f"circular CFG import found in {cfg}: {imported_cfg}"

            out_imported_cfgs.append(imported_cfg)
            imported_file_args, imported_cfgs = recursive_read(
                imported_cfg, imported_cfgs=tuple(out_imported_cfgs), level=level + 1)
            out_file_args += imported_file_args
            out_imported_cfgs += imported_cfgs
        else:
            out_file_args.append(file_arg)

    out_imported_cfgs = tuple(set(out_imported_cfgs))

    return out_file_args, out_imported_cfgs


def get_cfg_cache_path(_cfg):
    _cfg_dir = os.path.dirname(_cfg)
    _cfg_name = os.path.basename(_cfg)

    _cfg_cache_dir = linux_path(_cfg_dir, '.cache')
    os.makedirs(_cfg_cache_dir, exist_ok=True)

    cfg_cache_path = linux_path(_cfg_cache_dir, _cfg_name + '.cache')

    return cfg_cache_path


def load_cfg_cache(_cfg):
    cfg_cache_path = get_cfg_cache_path(_cfg)

    if not os.path.exists(cfg_cache_path):
        return None

    cfg_cache_mtime = os.path.getmtime(cfg_cache_path)
    cfg_mtime = os.path.getmtime(_cfg)

    if cfg_mtime > cfg_cache_mtime:
        return None

    try:
        print('Loading cfg data from {:s}'.format(cfg_cache_path))
        with open(cfg_cache_path, 'rb') as f:
            cache_data = pickle.load(f)
        nodes, nodes_by_fullname, _sections, file_args, file_args_offset, root_sec_name, imported_cfgs = cache_data
    except BaseException as e:
        print(f'failed to load cfg data from cache: {e}')
        return None
    else:
        for imported_cfg in imported_cfgs:
            imported_cfg_mtime = os.path.getmtime(imported_cfg)
            if imported_cfg_mtime > cfg_cache_mtime:
                return None

        return nodes, nodes_by_fullname, _sections, file_args, file_args_offset, root_sec_name

    # cfg_cache_mtime_local = time.ctime(cfg_cache_mtime)
    # cfg_mtime_local = time.ctime(cfg_mtime)
    # print('cfg_cache_mtime_local: {}'.format(cfg_cache_mtime_local))
    # print('cfg_mtime_local: {}'.format(cfg_mtime_local))


def read_cfg(_cfg, enable_cache=1):
    if not _cfg:
        return

    if enable_cache:
        cfg_cache = load_cfg_cache(_cfg)
        if cfg_cache is not None:
            return cfg_cache

    file_args_offset = 0

    file_args, imported_cfgs = recursive_read(_cfg)

    if not file_args[0].startswith('##'):
        file_args.insert(0, '##')
        file_args_offset = 1
    _sections = [[k.lstrip('#').strip(), i, k.count('#') - 1, 0]
                 for i, k in enumerate(file_args) if k.startswith('##')]

    n_file_args = len(file_args)
    n_sections = len(_sections)

    """parent specific sections"""
    # _parent_specific_section_ids = [k[1] for k in _sections if k[0].endswith(' __')]
    # _sections = [(k[0].rstrip(' __'), k[1], k[2], k[3]) if k[1] in _parent_specific_section_ids else k
    #              for k in _sections]

    _sections = [k if k[0] else ['__common__', k[1], k[2], k[3]] for k in _sections]

    """common sections"""
    _sections = [k if k[0] else ['__common__', k[1], k[2], k[3]] for k in _sections]

    """add section end IDs as the start IDs of the next section"""
    _sections = [[k[0], k[1], _sections[i + 1][1] if i < n_sections - 1 else n_file_args, k[2], k[3]]
                 for i, k in enumerate(_sections)]

    # """default sections
    # """
    # _default_sections, _default_section_ids = zip(*[
    #     (k[0].rstrip('__').strip(), i) for i, k in enumerate(_sections) if k[0].endswith('__')])
    # for i, j in enumerate(_default_section_ids):
    #     k = _sections[i]
    #     _sections[j] = (_default_sections[i], k[1], k[2])

    """template sections"""
    _curr_template_id = 1
    # _sec_id_orig = _sec_id_temp = 0
    # for i, _sec in enumerate(_sections):
    _all_temp_sections = {}
    pass_id = 0
    while True:

        n_sections = len(_sections)
        curr_root = Node()
        temp_nodes = {}  # :type dict(tuple, Node)
        _find_children(temp_nodes, None, _sections, 0, 0, curr_root, n_sections)

        _temp_sections = []
        # _added_sections = {}
        found_new_sections = 0
        for i, _sec in enumerate(_sections):
            # if _sec_id_temp >= len(_temp_sections):
            #     if _sec_id_orig >= len(_sections):
            #         break
            #     else:
            #         _sec = _sections[_sec_id_orig]
            #         _sec_id_orig += 1
            # else:
            #     _sec = _temp_sections[_sec_id_temp]
            #     _sec_id_temp += 1

            # if (_sec[1], _sec[2]) in _added_sections:
            #     """this section has already been added as a descendant of a previous template section
            #     """
            #     continue
            # _added_sections[(_sec[1], _sec[2])] = 1

            _sec_name = _sec[0]

            prelim_node = temp_nodes[i]

            if prelim_node.added:
                """this section has already been added in this pass as a descendant of a 
                previous template section
                """
                continue

            prelim_node.added = 1

            """range based section names
            """
            _templ_sec_names = []
            # any(map(_sec_name.startswith, ['(', '[', 'range(', 'irange(']))
            list_tokens = ['(', '[', ':', 'range(', 'irange(']
            """allow a list section name specifier to be prefixed by ordinary str separated by underscore"""
            if any(__sec_name.startswith(list_token)  for __sec_name in _sec_name.split('_')
                   for list_token in list_tokens):
            # if any(list_token in _sec_name for list_token in list_tokens):
                # assert ',' not in _sec_name, \
                #     "Combining template and range sections is not supported currently"
                """in case there are multiple ranges or lists"""
                # in_range_sec_names = _sec_name.split('+')
                # for in_range_sec_name in in_range_sec_names:
                in_range_sec_name = _sec_name
                range_tokens = in_range_sec_name.split('_')
                """in case there are multiple ranges or lists"""
                range_tuples = tuple(map(str_to_tuple_multi, range_tokens))

                def _get_sec_names(_sec_names, _tuples, _id, _nums):
                    for _num in _tuples[_id]:
                        __nums = _nums[:]
                        if isinstance(_num, str):
                            __nums.append(_num)
                        else:
                            if _num < 0:
                                __nums.append('n' + str(abs(_num)))
                            else:
                                __nums.append(str(_num))
                        if _id < len(_tuples) - 1:
                            _get_sec_names(_sec_names, _tuples, _id + 1, __nums)
                        else:
                            __sec_name = '_'.join(__nums)
                            _sec_names.append(__sec_name)

                _out_range_sec_names = []
                _get_sec_names(_out_range_sec_names, range_tuples, 0, [])
                _templ_sec_names += _out_range_sec_names
            elif ',' in _sec_name:
                _templ_sec_names = _sec_name.split(',')

            if not _templ_sec_names:
                _temp_sections.append(_sec)
                continue

            found_new_sections = 1
            descendants = prelim_node.get_descendants()
            if descendants:
                # def is_template(__sec_name):
                #     return __sec_name.startswith('(') or __sec_name.startswith(
                #         '[') or ':' in __sec_name or \
                #            __sec_name.startswith('range(') or __sec_name.startswith(
                #         'irange(') or ',' in __sec_name

                for k_id, k in enumerate(_templ_sec_names):
                    _temp_sections.append([k, _sec[1], _sec[2], _sec[3], _curr_template_id])
                    for descendant in descendants:  # type: Node
                        _temp_sections.append(
                            [descendant.name, descendant.line_id, descendant.end_id, descendant.curr_level, 0])
                        descendant.added = 1
                        # if k_id == 0:
                        #     # assert not is_template(descendant.name), \
                        #     #     f"template section: {descendant.name} used as a descendant of " \
                        #     #         f"another: {_sec_name}"
                        #     _added_sections[(descendant.line_id, descendant.curr_level)] = 1
            else:
                _temp_sections += [[k, _sec[1], _sec[2], _sec[3], _curr_template_id] for k in _templ_sec_names]
            _curr_template_id += 1

        if not found_new_sections:
            break

        _sections = _temp_sections
        _all_temp_sections[pass_id] = _temp_sections
        pass_id += 1

    time_stamp = datetime.now().strftime("%y%m%d_%H%M%S")
    root_sec_name = "__root_{}__".format(time_stamp)
    curr_root = Node(root_sec_name)
    n_sections = len(_sections)
    nodes = {}  # :type dict(tuple, Node)
    nodes_by_fullname = defaultdict(list)
    _find_children(nodes, nodes_by_fullname, _sections, 0, 0, curr_root, n_sections)

    nodes_by_fullname = dict(nodes_by_fullname)

    if enable_cache:
        cfg_cache_path = get_cfg_cache_path(_cfg)
        with open(cfg_cache_path, 'wb') as f:  # Python 3: open(..., 'wb')
            pickle.dump([nodes, nodes_by_fullname, _sections,
                         file_args, file_args_offset, root_sec_name, imported_cfgs], f)

    return nodes, nodes_by_fullname, _sections, file_args, file_args_offset, root_sec_name


def process_dict(params, *args, **kwargs):
    """

    :param dict params:
    :param args:
    :param kwargs:
    :return:
    """

    class TempObject:
        def __init__(self, entries):
            self.help = {}
            self.__dict__.update(entries)

    obj = TempObject(params)
    process(obj, *args, **kwargs)
    params.update(obj.__dict__)


def process(obj, args_in=None, cmd=True, cfg='', cfg_root='', cfg_ext='',
            cfg_prefix='', cfg_suffix='',
            prog='', usage='%(prog)s [options]', allow_unknown=0, cfg_cache=1,
            cmd_args=None, verbose=0):
    """

    :param obj:
    :param list | None args_in:
    :param bool cmd: enable command line argument processing
    :param str cfg:
    :param str cfg_root:
    :param str cfg_ext:
    :param str cfg_prefix:
    :param str cfg_suffix:
    :param str prog:
    :param str | None usage:
    :param int allow_unknown:
    :param int cfg_cache:
    :return:
    """

    class_input = False
    if inspect.isclass(obj):
        class_input = True
        obj = obj()

    arg_dict = {}
    if prog:
        arg_dict['prog'] = prog
    if usage is None:
        arg_dict['usage'] = argparse.SUPPRESS
    elif usage:
        arg_dict['usage'] = usage
    if hasattr(obj, 'help') and '__desc__' in obj.help:
        arg_dict['description'] = obj.help['__desc__']

    arg_dict['formatter_class'] = argparse.RawTextHelpFormatter

    parser = argparse.ArgumentParser(**arg_dict)
    member_to_type = {}
    doc_dict = {}
    _add_params_to_parser(parser, obj, member_to_type, doc_dict, verbose=verbose)

    obj_type = type(obj)
    obj_doc_dict = doc_dict[obj_type]

    try:
        short_description, long_description = obj_doc_dict['__description__']
    except KeyError:
        pass
    else:
        if short_description is not None:
            parser.description = short_description
            if long_description is not None:
                parser.description += '\n' + long_description
        elif long_description is not None:
            parser.description = long_description

    if args_in is None:
        if cmd_args is None:
            cmd_args = sys.argv[1:]

            if cmd_args and cmd_args[0].startswith('python') and '=' not in cmd_args[0]:
                cmd_args = cmd_args[1:]
                if cmd_args and '=' not in cmd_args[0]:
                    cmd_args = cmd_args[1:]

        argv_id = 0
        cfg_from_cmd = None

        if not cfg:
            # check for cfg files specified at command line
            if cmd and len(cmd_args) > 0 and ('--cfg' in cmd_args[0] or cmd_args[0].startswith('cfg=')):
                _, arg_val = cmd_args[0].split('=')
                cfg = cfg_from_cmd = arg_val
                argv_id += 1
                if hasattr(obj, 'cfg'):
                    obj.cfg = cfg
            cfg = getattr(obj, 'cfg', cfg)

        if not cfg_root:
            cfg_root = getattr(obj, 'cfg_root', cfg_root)

        if not cfg_prefix:
            cfg_prefix = getattr(obj, 'cfg_prefix', cfg_prefix)

        if not cfg_suffix:
            cfg_suffix = getattr(obj, 'cfg_suffix', cfg_suffix)

        if not cfg_ext:
            cfg_ext = getattr(obj, 'cfg_ext', cfg_ext)

        if not cfg and hasattr(obj, 'cfg'):
            obj.cfg = cfg

        if isinstance(cfg, str):
            if ',' not in cfg:
                cfg = '{},'.format(cfg)

            cfg = [k for k in cfg.split(',') if k]

        """pre-process raw cfg strings to extract and refine cfg files and sections"""
        cfg_file_list = []
        for _cfg in cfg:
            _cfg_sec = []
            if ':' not in _cfg:
                """no explicit section specified for the CFG so read its common sections"""
                _cfg = '{}:__common__'.format(_cfg)

            """alternate specification for parent specific sections for ease of selecting child section"""
            # _cfg = _cfg.replace('-', '')

            _cfg = _cfg.split(':')
            _cfg_sec = [k for k in list(_cfg[1:]) if k]
            _cfg = _cfg[0]

            """optional leading and trailing underscores for better visible discrimination between
             cfg files and sections in commands stored in syntax-highlighted markdown files"""
            if _cfg.startswith('_') and _cfg.endswith('_'):
                _cfg = _cfg.strip('_')

            if cfg_prefix:
                _cfg = f'{cfg_prefix}-{_cfg}'

            if cfg_suffix:
                _cfg = f'{_cfg}-{cfg_suffix}'

            if cfg_ext:
                _cfg = f'{_cfg}.{cfg_ext}'

            if cfg_root:
                _cfg = linux_path(cfg_root, _cfg)

            if not os.path.isfile(_cfg):
                if _cfg:
                    raise IOError('cfg file does not exist: {:s}'.format(linux_path(os.path.abspath(_cfg))))
            repeated_cfgs = []

            repeated_sec_ids = [__sec_id for __sec_id, __sec in enumerate(_cfg_sec) if '+' in __sec]

            excluded_ids = []

            for i, __sec_id in enumerate(repeated_sec_ids):

                _exclude_common_secs = 0

                if _cfg_sec[__sec_id].startswith('++'):
                    if _cfg_sec[__sec_id].startswith('+++'):
                        _exclude_common_secs = 1
                        _cfg_name_start_pos = 3
                    else:
                        _cfg_name_start_pos = 2
                        _exclude_common_secs = 0

                    """these sections are exclusive to the repeated cfg files so excluded from the default one"""
                    _exclusive_secs = 1
                    __sec_names = _cfg_sec[__sec_id][_cfg_name_start_pos:].split('+')
                    repeat_sec_names = __sec_names
                    _cfg_sec[__sec_id] = ''
                else:
                    _exclusive_secs = 0
                    __sec_names = _cfg_sec[__sec_id].split('+')
                    repeat_sec_names = __sec_names[1:]
                    _cfg_sec[__sec_id] = __sec_names[0]

                start_include_id = __sec_id + 1
                end_include_id = repeated_sec_ids[i + 1] if i < len(repeated_sec_ids) - 1 else len(_cfg_sec)
                for __name in repeat_sec_names:
                    included_secs = [__name, ] + _cfg_sec[start_include_id:end_include_id]
                    repeated_cfgs.append((_cfg, included_secs, 1, _exclude_common_secs))

                if _exclusive_secs:
                    excluded_ids += list(range(start_include_id, end_include_id))

            _cfg_sec = [k for i, k in enumerate(_cfg_sec) if i not in excluded_ids and k]
            cfg_file_list.append((_cfg, _cfg_sec, 0, 0))
            cfg_file_list += repeated_cfgs

        """process each cfg file and its sections"""
        args_in = []
        prev_cfg_data = []
        for _cfg, _cfg_sec, _cfg_repeat, _exclude_common_secs in cfg_file_list:
            if not _cfg:
                continue

            if _cfg_repeat:
                assert prev_cfg_data, "repeat cfg found without previous cfg data: {}".format(_cfg)
                txt = 'Processing repeat parameters from {:s}'.format(_cfg)
                if _exclude_common_secs:
                    txt = '{} without common sections'.format(txt)
                print(txt)
            else:
                prev_cfg_data = read_cfg(_cfg, enable_cache=cfg_cache)

                # _sections = [(k, i) for k, i in _sections]

            nodes, nodes_by_fullname, _sections, _file_args, file_args_offset, root_sec_name = prev_cfg_data

            # _re_sections = RegexDict({
            #     __sec[0]: (nodes[__sec_id], __sec) for __sec_id, __sec in enumerate(_sections) if '*' in __sec[0]
            # })

            n_file_args = len(_file_args)

            """remove excluded sections"""
            excluded_cfg_sec = [_sec.lstrip('!') for _sec in _cfg_sec if _sec.startswith('!')]
            section_names, section_line_ids, section_end_ids, section_seq_ids, section_template_ids = map(
                list, zip(
                    *[(_sec[0], _sec[1], _sec[2], i, _sec[4]) for i, _sec in enumerate(_sections)
                      if _sec not in excluded_cfg_sec]))

            if excluded_cfg_sec:
                print('Excluding section(s):\n{}'.format(pformat(excluded_cfg_sec)))
                _cfg_sec = [_sec for _sec in _cfg_sec if _sec not in excluded_cfg_sec]
                assert _cfg_sec, 'No included sections found for {}'.format(_cfg)

            if not _exclude_common_secs:
                """add common sections"""
                common_section_names = [s for __i, s in enumerate(section_names) if
                                        nodes[section_seq_ids[__i]].is_common]
                _cfg_sec += common_section_names

            """unique section names"""
            _cfg_sec = list(set(_cfg_sec))

            """specific sections from full names"""
            invalid_sec = [(_id, _sec) for _id, _sec in enumerate(_cfg_sec) if _sec not in section_names]
            specific_sec = []
            specific_sec_ids = {}

            # _node_matches = {( _id, _sec) : nodes[k] for _id, _sec in invalid_sec for k in nodes
            #                  if nodes[k].full_name == _sec}
            for _id, _sec in invalid_sec:
                _sec_full = _sec.replace('-', '')
                try:
                    _node_matches = nodes_by_fullname[_sec_full]  # type: list
                except KeyError:
                    # raise AssertionError('Section {} not found in {}'.format(
                    #     _sec, _cfg))
                    try:
                        _orig_sec, _subs_sec = _sec.split('-', maxsplit=1)

                        """optional leading and trailing double underscores for better visible 
                        discrimination between substitution and ordinary sections in commands 
                        stored in syntax-highlighted markdown files"""
                        if _subs_sec.startswith('__') and _subs_sec.endswith('__'):
                            _subs_sec = _subs_sec.strip('__')
                        _orig_sec_full = f'__sub__{_orig_sec}'
                        _node_matches = nodes_by_fullname[_orig_sec_full]  # type: list

                        assert len(_node_matches) == 1, f"multiple substitution sections found for {_sec}"

                        matched_node_ = _node_matches[0]
                        seq_id = matched_node_.seq_id

                        matched_sec_ = _sections[seq_id]

                        assert matched_sec_[0] == matched_node_.name, "substitution section name mismatch"
                        assert section_names[seq_id] == matched_node_.name, "substitution section name mismatch"

                        matched_node_.name = matched_sec_[0] = section_names[seq_id] = _subs_sec

                        # _sections[_node_matches[0].seq_id] = tuple(matched_sec_)

                        # matched_node_, matched_sec_ = _re_sections[_sec_full]  # type: Node, list
                        # new_node_ = matched_node_.copy(name=_child_sec, seq_id=len(_sections))
                        # new_sec_ = list(matched_sec_).copy()
                        # new_sec_[0] = _child_sec
                        # _sections.append(tuple(new_sec_))
                        # _node_matches = [new_node_, ]
                        print()
                    except KeyError:
                        raise AssertionError(f'Section {_sec} not found in {_cfg}')

                # curr_specific_sec = []
                for _node in _node_matches:  # type:Node

                    parent = _node.parent
                    specific_sec.append((_node.seq_id, _node.name))
                    specific_sec_ids[_node.seq_id] = 0

                    if parent.seq_id is not None:
                        specific_sec.append((parent.seq_id, parent.name))
                        specific_sec_ids[parent.seq_id] = 1

                    # if _node.parent.template_id:
                    #     shared_parents = template_nodes[_node.parent.template_id]
                    # else:
                    #     shared_parents = [_node.parent, ]
                    #
                    # for parent in shared_parents:
                    #     specific_sec.append((parent.seq_id, parent.name))
                    #     specific_sec_ids.append(parent.seq_id)

                    # _sec_matches = []
                    # _curr_sec_node = _node
                    # while _curr_sec_node.parent is not None:
                    #     _sec_matches.append((_curr_sec_node.seq_id, _curr_sec_node.name))
                    #     _curr_sec_node = _curr_sec_node.parent
                    # specific_sec += _sec_matches[::-1]
                # specific_sec[_sec] = curr_specific_sec

                _cfg_sec[_id] = ''

            # valid_check = [_sec in sections for _sec in _cfg_sec]
            # assert all(valid_check), \
            #     'One or more sections: {} from:\n{}\nnot found in cfg file {} with sections:\n{}'.format(
            #         [_sec for _sec in _cfg_sec if _sec not in sections],
            #         pformat(_cfg_sec), _cfg, pformat(sections))

            """all occurrences of each section
            """
            _cfg_sec_ids = [[i for i, x in enumerate(section_names) if _sec and x == _sec] for _sec in _cfg_sec]

            # _cfg_sec_ids = [item for sublist in _cfg_sec_ids for item in sublist]

            """flatten
            """
            __cfg_sec_ids = []
            __cfg_sec = []
            is_included = defaultdict(bool)
            for _sec, _sec_ids in zip(_cfg_sec, _cfg_sec_ids):
                for _sec_id in _sec_ids:
                    __cfg_sec.append(_sec)
                    __cfg_sec_ids.append(_sec_id)
                    is_included[section_seq_ids[_sec_id]] = True

            _cfg_sec_disp = []
            valid_cfg_sec = []
            skipped_cfg_sec = []
            skipped_parent_seq_ids = []
            _sec_args = []
            valid_parent_names = [root_sec_name, ]
            valid_parent_seq_ids = [None, ]
            _common_str = ''

            for _sec_id, x in specific_sec:
                __cfg_sec_ids.append(_sec_id)
                is_included[section_seq_ids[_sec_id]] = True
                __cfg_sec.append(x)

            # n_sections = len(sections)

            """sort by line and process each cfg section
            """
            __cfg_sec_sorted = sorted(zip(__cfg_sec_ids, __cfg_sec))

            # __cfg_seq_ids = [section_seq_ids[k[0]] for k in __cfg_sec_sorted]

            for _sec_id, x in __cfg_sec_sorted:

                _curr_sec_seq_id = section_seq_ids[_sec_id]
                _curr_sec_node = nodes[_curr_sec_seq_id]  # type: Node

                _curr_sec_parent_name = _curr_sec_node.parent.name
                _curr_sec_parent_seq_id = _curr_sec_node.parent.seq_id

                _curr_sec_seq_id = _curr_sec_node.seq_id
                _curr_sec_name = section_names[_sec_id]

                assert _curr_sec_name == _curr_sec_node.name, "curr_sec_node name mismatch"

                if _curr_sec_parent_seq_id not in valid_parent_seq_ids:
                    # if _sec_id in specific_sec_ids and specific_sec_ids[_sec_id] == 0:
                    #     raise AssertionError('Specific section {} not found'.format(_curr_sec_ancestral_path))
                    # print('skipping section {}'.format(_curr_sec_ancestral_path))
                    if _curr_sec_parent_seq_id in skipped_parent_seq_ids:
                        skipped_cfg_sec.append(x)
                        skipped_parent_seq_ids.append(_curr_sec_seq_id)
                    continue

                if _curr_sec_name == '__exc__':
                    """exclusive sibling section"""
                    included_siblings = [(_node.seq_id, _node.name) for _node in _curr_sec_node.parent.children
                                         if is_included[_node.seq_id] and _node.seq_id != _curr_sec_seq_id]
                    if included_siblings:
                        assert len(included_siblings) == 1, \
                            "multiple included siblings for " \
                            "exclusive section with parent {},{} :: {}".format(
                                _curr_sec_parent_seq_id, _curr_sec_parent_name, included_siblings)
                        print('skipping exclusive section {} with parent {},{} due to included sibling: {}'.format(
                            _curr_sec_seq_id, _curr_sec_parent_seq_id, _curr_sec_parent_name, included_siblings[0]
                        ))
                        skipped_cfg_sec.append(x)
                        skipped_parent_seq_ids.append(_curr_sec_seq_id)
                        continue

                _curr_sec_full_name = _curr_sec_node.full_name
                _curr_sec_parent_full_name = _curr_sec_node.parent.full_name

                ancestors = _curr_sec_node.get_ancestors()
                _curr_sec_ancestral_path = ':'.join([ancestor.name for ancestor in ancestors[::-1]
                                                     if ancestor.name not in common_section_names] +
                                                    [_curr_sec_name, ])
                _curr_sec_root_name = ancestors[-1].name if ancestors else _curr_sec_name

                assert x == _curr_sec_name, "mismatch between x: {} and _curr_sec_name: {}".format(x, _curr_sec_name)

                valid_parent_seq_ids.append(_curr_sec_seq_id)
                valid_parent_names.append(x)
                valid_cfg_sec.append(x)

                _start_id = section_line_ids[_sec_id] + 1
                _template_id = section_template_ids[_sec_id]

                # if _template_id:
                #     """template sections with the same ID all have same line IDs so look for the
                #     first subsequent section with different ID that is not an ancestor;
                #     """
                #     _end_id = n_file_args
                #     _next_sec_id = None
                #     # ancestors = _curr_sec_node.get_ancestors()
                #     # ancestor_template_ids = [ancestor.template_id for ancestor in ancestors]
                #     for i in range(_sec_id + 1, n_sections):
                #         if section_template_ids[i] != _template_id and section_line_ids[i] > _start_id:
                #             _next_node = nodes[section_seq_ids[i]]
                #             _next_template_id = section_template_ids[i]
                #             _end_id = section_line_ids[i]
                #             _next_sec_id = i
                #             break
                # else:
                #     _end_id = section_line_ids[_sec_id + 1] if _sec_id < n_sections - 1 else n_file_args

                _end_id = section_end_ids[_sec_id]

                # discard empty and comment lines from start of section
                orig_start_id = _start_id
                while _start_id < n_file_args:
                    if _file_args[_start_id] and not _file_args[_start_id].startswith('#'):
                        # if _file_args[_start_id - 1]:
                        break
                    _start_id += 1

                # discard empty and comment lines from end of section
                orig_end_id = _end_id
                while _end_id >= 0:
                    if _file_args[_end_id - 1] and not _file_args[_end_id - 1].startswith('#'):
                        # if _file_args[_end_id - 1]:
                        break
                    _end_id -= 1

                if _start_id >= _end_id:
                    if x not in common_section_names:
                        # print('skipping empty section {} ({}, {})'.format(x, orig_start_id, orig_end_id))
                        assert orig_start_id == orig_end_id, "invalid empty section {} ({}, {})".format(
                            x, orig_start_id, orig_end_id)
                    continue

                _curr_sec_args = _file_args[_start_id:_end_id]

                phs_sub = {
                    ('%N%', '__name__',): _curr_sec_name,
                    ('%P%', '__parent__',): _curr_sec_parent_name,
                    ('%R%', '__root__',): _curr_sec_root_name,
                    ('%F%', '__full__',): _curr_sec_full_name,
                    ('%PF%', '__parent_full__',): _curr_sec_parent_full_name,
                }

                _curr_sec_sub_names = _curr_sec_name.split('_')
                if len(_curr_sec_sub_names) > 1:
                    for sub_name_id, sub_name in enumerate(_curr_sec_sub_names):
                        phs_sub[(f'%N{sub_name_id}%', f'__name{sub_name_id}__',)] = sub_name
                        if sub_name_id > 0:
                            phs_sub[(f'%N{sub_name_id}*%', f'__name{sub_name_id}*__',)] = '_'.join(
                                _curr_sec_sub_names[sub_name_id:])

                """
                only replace these if the placeholder actually exists since the 
                substitution might be invalid depending on the name and hierarchical position of the section
                """
                phs_sub_fn = {
                    ('%GP%', '__g_parent__'): _curr_sec_node.gp,
                    ('%GGP%', '__gg_parent__'): _curr_sec_node.ggp,

                    ('%GF%', '__g_full__'): _curr_sec_node.gf,
                    ('%GGF%', '__gg_full__'): _curr_sec_node.ggf,

                    ('%RI%', '__ratio__'): _curr_sec_node.ri,
                    ('%PRI%', '__parent_ratio__'): _curr_sec_node.pri,
                    ('%GPRI%', '__g_parent_ratio__'): _curr_sec_node.gpri,
                    ('%GGPRI%', '__gg_parent_ratio__'): _curr_sec_node.ggpri,

                    ('%L%', '__list__'): _curr_sec_node.l_,
                    ('%PL%', '__parent_list__'): _curr_sec_node.pl,
                    ('%GPL%', '__g_parent_list__'): _curr_sec_node.gpl,
                    ('%GGPL%', '__gg_parent_list__'): _curr_sec_node.ggpl,

                    ('%LRI%', '__list_ratio__'): _curr_sec_node.lri,
                    ('%PLRI%', '__parent_list_ratio__'): _curr_sec_node.plri,
                    ('%GPLRI%', '__g_parent_list_ratio__'): _curr_sec_node.gplri,
                    ('%GGPLRI%', '__gg_parent_list_ratio__'): _curr_sec_node.ggplri,

                    ('%RA%', '__range__'): _curr_sec_node.ra,
                    ('%PRA%', '__parent_range__'): _curr_sec_node.pra,
                    ('%GPRA%', '__g_parent_range__'): _curr_sec_node.gpra,
                    ('%GGPRA%', '__gg_parent_range__'): _curr_sec_node.ggpra,
                }

                for i, _curr_sec_arg in enumerate(_curr_sec_args):

                    for phs, sub in phs_sub.items():
                        for ph in phs:
                            _curr_sec_args[i] = _curr_sec_args[i].replace(ph, sub)

                    for phs, sub_fn in phs_sub_fn.items():
                        for ph in phs:
                            if ph not in _curr_sec_args[i]:
                                continue
                            _curr_sec_args[i] = _curr_sec_args[i].replace(ph, sub_fn())

                _sec_args += _curr_sec_args

                start_line_num = _start_id + 1 - file_args_offset
                end_line_num = _end_id - file_args_offset

                if x not in common_section_names:

                    # if _sec_id in specific_sec_ids and not _curr_sec_node.parent.is_root:
                    #     _sec_disp_name = _curr_sec_full_name
                    # # elif not _curr_sec_node.parent.is_root:
                    # #     _sec_disp_name = '{}:{}'.format(_curr_sec_parent_name, _curr_sec_name)
                    # else:
                    #     _sec_disp_name = _curr_sec_ancestral_path

                    _sec_disp_name = _curr_sec_ancestral_path

                    _str = '{}: {}'.format(_sec_disp_name, start_line_num)
                    if end_line_num > start_line_num:
                        _str = '{} -> {}'.format(_str, end_line_num)
                    _cfg_sec_disp.append(_str)
                else:
                    _str = '{}'.format(start_line_num)
                    if end_line_num > start_line_num:
                        _str = '{} -> {}'.format(_str, end_line_num)
                    _common_str = '{}, {}'.format(_common_str, _str) if _common_str else _str

                # print(_str)
                # pass

            invalid_cfg_sec = [k for k in __cfg_sec if k and k not in valid_cfg_sec + skipped_cfg_sec]
            if invalid_cfg_sec:
                raise AssertionError('Invalid cfg sections provided for {}:\n {}'.format(_cfg, invalid_cfg_sec))

            if _common_str:
                _common_str = 'common: {}'.format(_common_str)
                _cfg_sec_disp.append(_common_str)

            print('\t{}'.format(
                '\n\t'.join(_cfg_sec_disp)
                # pformat(_cfg_sec_disp)
            ))

            file_args = [arg.strip() for arg in _sec_args if arg.strip()]
            # lines starting with # in the cfg file are comments or section headings and thus ignored
            file_args = ['--{:s}'.format(arg) for arg in file_args if not arg.startswith('#')]
            args_in += file_args

            # reset prefix before next cfg file
            args_in.append('@')

        help_mode = ''
        # command line arguments override those in the cfg file
        if cmd:
            # reset prefix before command line args
            args_in.append('@')
            noncfg_cmd_args = list(cmd_args[argv_id:])
            # if noncfg_cmd_args and noncfg_cmd_args[0] in ('--h', '-h', '--help'):
            #     # args_in.insert(0, noncfg_cmd_args[0])
            #     help_mode = noncfg_cmd_args[0]
            #     noncfg_cmd_args = noncfg_cmd_args[1:]
            args_in += noncfg_cmd_args

        args_in = [k if k.startswith('--') or k == '-h' else '--{}'.format(k) for k in args_in]

        # pf: Prefix to be added to all subsequent arguments to avoid very long argument names
        # for deeply nested module parameters:
        # with pf=name1.name2
        # @name: pf=name
        # @@name: pf=name1.name2.name
        # @@@name: pf=name1.name

        _args_in = []
        _args_dict = {}
        pf = ''
        for _id, _arg in enumerate(args_in):
            if _arg in ('--h', '-h', '--help'):
                help_mode = _arg
                continue

            _arg = _arg[2:]
            suspend_pf = 0
            if _arg.startswith('@'):
                _name = _arg[1:].strip()

                if '=' in _name:
                    if _name.startswith('@@'):
                        pf_id = '@@'
                    elif _name.startswith('@'):
                        pf_id = '@'
                    else:
                        pf_id = ''
                    _pf = _get_pf(pf_id, pf)
                    _name = _name.lstrip('@')
                    if _pf:
                        _arg = '{}.{}'.format(_pf, _name)
                    else:
                        _arg = _name
                    suspend_pf = 1
                else:
                    pf = _get_pf(_name, pf)
                    continue

            if '+=' in _arg:
                try:
                    _name, _val = _arg.split('+=')
                except ValueError as e:
                    raise ValueError('Invalid argument provided: {} :: {}'.format(_arg, e))
                if pf and not suspend_pf:
                    _name = '{}.{}'.format(pf, _name)

                if ',' in _name:
                    _names_recursive = []
                    _recursive_append(_name, _names_recursive)

                    # print('{} --> {}'.format(_name, _names_recursive))
                    # print('')
                else:
                    _names_recursive = [_name, ]

                for __name in _names_recursive:
                    __val = _val
                    try:
                        arg_type = member_to_type[__name]
                    except KeyError:
                        msg = 'Invalid param name {} in argument {}'.format(__name, _arg)
                        if allow_unknown:
                            print(msg)
                        else:
                            raise ValueError(msg)
                    else:
                        assert arg_type in (tuple, list, MultiPath, MultiCFG), \
                            "incremental value specification found for argument {} of invalid type: {}".format(
                                __name, arg_type)
                        try:
                            old_val = _args_dict[__name]
                        except KeyError:
                            pass
                            # print('Accumulative value provided for uninitialized arg: {} :: {}'.format(
                            #     __name, _arg))
                        else:
                            if arg_type is MultiPath:
                                sep = '_'
                            elif arg_type is MultiCFG:
                                sep = '::'
                            else:
                                sep = ','
                            __val = '{}{}{}'.format(old_val, sep, _val)
                    _args_in.append('--{}={}'.format(__name, __val))
                    _args_dict[__name] = __val
            else:
                try:
                    _name, _val = _arg.split('=')
                except ValueError as e:
                    raise ValueError('Invalid argument provided: {} :: {}'.format(_arg, e))
                if pf:
                    _name = '{}.{}'.format(pf, _name)

                if ',' in _name:
                    _names_recursive = []
                    _recursive_append(_name, _names_recursive)

                    # print('{} --> {}'.format(_name, _names_recursive))
                    # print('')
                else:
                    _names_recursive = [_name, ]

                _args_in += ['--{}={}'.format(__name, _val) for __name in _names_recursive]
                _args_dict.update({__name: _val for __name in _names_recursive})

        args_in = _args_in

        _args_in = []
        for _arg_str in args_in:
            _name, _val = _arg_str.split('=')
            if not _val or _val.startswith('#'):
                continue
            _args_in.append(_arg_str)

        args_in = _args_in
        if help_mode:
            args_in.insert(0, help_mode)
    if allow_unknown:
        args, unknown = parser.parse_known_args(args_in)
        if unknown:
            print('Unknown arguments found:\n{}'.format(pformat(unknown)))
    else:
        args = parser.parse_args(args_in)

    _process_args_from_parser(obj, args, member_to_type)

    if cfg_from_cmd is not None and hasattr(obj, 'cfg'):
        obj.cfg = cfg_from_cmd

    # print('train_seq_ids: ', self.train_seq_ids)
    # print('test_seq_ids: ', self.test_seq_ids)

    if class_input:
        return obj

    return args_in


def _recursive_append(name, out_names, names_lists=None, _id=0, out_name=None, ):
    if names_lists is None:
        names_lists = [name.split(',') for name in name.split('.')]
        out_name = ''
        _id = 0

    if _id == len(names_lists):
        out_names.append(out_name)
        return

    name_list = names_lists[_id]
    for name in name_list:
        if _id == 0:
            out_name = name
        else:
            out_name += '.' + name
        _recursive_append(None, out_names, names_lists, _id + 1, out_name)


def _get_pf(_name, pf):
    if _name.startswith('@@'):
        """go up one level"""
        if '.' in pf:
            _idx = pf.rfind('.')
            pf = pf[:_idx]
        else:
            pf = ''
        _name = _name[2:].strip()
        if pf and _name:
            pf = '{}.{}'.format(pf, _name)
        elif pf:
            pass
        elif _name:
            pf = _name
    elif _name.startswith('@'):
        """go down one level"""
        _name = _name[1:].strip()
        if pf and _name:
            pf = '{}.{}'.format(pf, _name)
    else:
        pf = _name

    return pf


def to_flags(flags, params, allow_missing=0, verbose=0):
    flags_dict = flags.flag_values_dict()
    param_names = list(flags_dict.keys())

    param_names.sort()

    valid_param_names = [_param_name for _param_name in param_names if hasattr(params, _param_name)]
    missing_param_names = [_param_name for _param_name in param_names if not hasattr(params, _param_name)]

    if missing_param_names:
        msg = 'found missing params:\n{}\n'.format('\n\t'.join(missing_param_names))
        if allow_missing:
            print(msg)
        else:
            raise AssertionError(msg)

    if verbose:
        print('setting flags for {} params:\n{}\n'.format(len(valid_param_names), '\n\t'.join(valid_param_names)))

    for _param_name in valid_param_names:
        if not _param_name:
            continue

        # flags_dict[_param_name] = getattr(params, _param_name)

        setattr(flags, _param_name, getattr(params, _param_name))

    print()


def from_flags(flags, class_name='Params', allow_none_default=True,
               add_help=True, to_clipboard=False, sort_by_name=True):
    flags_dict = flags.flag_values_dict()
    flags_help = flags.get_help()

    all_params_names = list(flags_dict.keys())

    flags_help_lines = flags_help.split('\n')

    excluded_line_ids = [i for i, line in enumerate(flags_help_lines) if not line]
    excluded_line_ids += [i + 1 for i in excluded_line_ids]

    flags_help_lines = [line.strip() for i, line in enumerate(flags_help_lines) if i not in excluded_line_ids]

    start_ids = [i for i, line in enumerate(flags_help_lines) if line.startswith('--')]

    start_ids.append(len(flags_help_lines))

    param_name_to_help = {
        flags_help_lines[i][2:]: ' '.join(flags_help_lines[start_ids[__id]:start_ids[__id + 1]])[2:]
        for __id, i in enumerate(start_ids[:-1])
    }

    param_name_to_help2 = {
        k.split(': ')[0]: v for k, v in param_name_to_help.items()

    }

    param_name_to_help3 = {
        k.lstrip('[no]'): v[len(k) + 1:] for k, v in param_name_to_help2.items()

    }

    header_text = 'class {}:\n'.format(class_name)
    out_text = '\tdef __init__(self):\n'
    if '--cfg' not in all_params_names:
        out_text += "\t\tself.cfg = ()\n"
    # help_text = '\t\tself.help = {\n'
    help_text = '\t"""\n'

    _param_names = list(flags_dict.keys())
    if sort_by_name:
        _param_names.sort()

    for _param_name in _param_names:
        if not _param_name:
            continue

        _param_val = flags_dict[_param_name]

        try:
            _help = param_name_to_help3[_param_name]
        except KeyError:
            _help = ''

        _param_type = type(_param_val)

        if _param_type in (list, tuple):
            if _param_type is str:
                default_str = "['{}, ]'".format(_param_val)
            else:
                default_str = '[{} ,]'.format(_param_val)
        else:
            if _param_type is str:
                default_str = "'{}'".format(_param_val)
            else:
                default_str = '{}'.format(_param_val)

        var_name = _param_name.replace('-', '_').replace(' ', '_')

        out_text += '\t\tself.{} = {}\n'.format(var_name, default_str)
        # help_text += "\t\t\t'{}': '{}',\n".format(var_name, _help)

        help_text += "\t:ivar {}: {}\n".format(var_name, _help)
        help_text += "\t:type {}: {}\n\n".format(var_name, _param_type.__name__)

    help_text += '\t"""\n'
    if add_help:
        out_text = help_text + out_text

    out_text = header_text + out_text

    if to_clipboard:
        try:
            import pyperclip

            pyperclip.copy(out_text)
            spam = pyperclip.paste()
        except BaseException as e:
            print('Copying to clipboard failed: {}'.format(e))
        else:
            print('Class definition copied to clipboard')

    else:
        class_name_snake_case = re.sub(r'(?<!^)(?=[A-Z])', '_', class_name).lower()
        out_fname = '{}.py'.format(class_name_snake_case)
        out_path = linux_path(os.path.abspath(out_fname))
        if os.path.exists(out_path):
            print('output path already exists so not writing to it: {}'.format(out_path))
        else:
            print('Writing output to {}'.format(out_path))
            with open(out_path, 'w') as fid:
                fid.write(out_text)


def from_parser(parser, class_name='Params', allow_none_default=True,
                add_help=True, to_clipboard=False, sort_by_name=True):
    """
    convert argparse.ArgumentParser object into a parameter class compatible with this module
    writes the class code to a python source file named  <class_name>.py

    :param argparse.ArgumentParser parser:
    :param str class_name:
    :param bool add_help:
    :param bool to_clipboard:
    :return:
    """

    optionals = parser._optionals._option_string_actions
    positionals = parser._positionals._option_string_actions

    all_params = optionals.copy()
    all_params.update(positionals)

    all_params_names = list(all_params.keys())

    if sort_by_name:
        all_params_names.sort()

    header_text = 'class {}:\n'.format(class_name)
    out_text = '\tdef __init__(self):\n'
    if '--cfg' not in all_params_names:
        out_text += "\t\tself.cfg = ()\n"
    # help_text = '\t\tself.help = {\n'
    help_text = '\t"""\n'

    if parser.description is not None:
        # help_text += "\t\t\t'__desc__': '{}',\n".format(parser.description)
        help_text += "\t{}\n".format(parser.description)

    # doc_text = '\t"""\n'

    for _name in all_params_names:
        __name = _name[2:]

        if not __name or _name in ('--h', '-h', '--help'):
            continue

        _param = all_params[_name]
        _help = _param.help

        if _help is None:
            _help = ''

        default = _param.default
        nargs = _param.nargs

        if isinstance(nargs, str):
            _param_type = list
        else:
            _param_type = _param.type

        if default is None:

            assert _param_type is not None, 'Both type and default are None for params {}'.format(__name)

            msg = 'None default found for param: {}'.format(__name)
            if allow_none_default:
                print(msg)

                if _param_type in (list, tuple):
                    default_str = '[None, ]'
                else:
                    default_str = 'None'
                # if _param_type is str:
                #     default_str = ""
                # else:
                #     default_str = "{}".format(_param_type())
            else:
                raise IOError(msg)
        else:
            if _param_type is None:
                _param_type = type(_param.default)

            if _param_type in (list, tuple):
                default_str = '[{} ,]'.format(_param.default)
            else:
                if _param_type is str:
                    default_str = "'{}'".format(_param.default)
                else:
                    default_str = '{}'.format(_param.default)

        var_name = __name.replace('-', '_').replace(' ', '_')

        out_text += '\t\tself.{} = {}\n'.format(var_name, default_str)
        # help_text += "\t\t\t'{}': '{}',\n".format(var_name, _help)

        help_text += "\t:ivar {}: {}\n".format(var_name, _help)
        help_text += "\t:type {}: {}\n\n".format(var_name, _param_type.__name__)

        # doc_text += '\t:param {} {}: {}\n'.format(_param_type.__name__, var_name, _help)

    # help_text += "\t\t}"
    help_text += '\t"""\n'

    # doc_text += '\t"""\n'

    if add_help:
        # out_text += help_text
        out_text = help_text + out_text

    # if add_doc:
    #     out_text = doc_text + out_text

    out_text = header_text + out_text

    # time_stamp = datetime.now().strftime("%y%m%d_%H%M%S")

    if to_clipboard:
        try:
            import pyperclip

            pyperclip.copy(out_text)
            spam = pyperclip.paste()
        except BaseException as e:
            print('Copying to clipboard failed: {}'.format(e))
        else:
            print('Class definition copied to clipboard')

    else:
        class_name_snake_case = re.sub(r'(?<!^)(?=[A-Z])', '_', class_name).lower()
        out_fname = '{}.py'.format(class_name_snake_case)
        out_path = linux_path(os.path.abspath(out_fname))
        if os.path.exists(out_path):
            print('output path already exists so not writing to it: {}'.format(out_path))
        else:
            print('Writing output to {}'.format(out_path))
            with open(out_path, 'w') as fid:
                fid.write(out_text)


def val_to_str(name, val, class_name, class_prefix, nested, **kwargs):
    sub_class_txt = ''
    if isinstance(val, list):
        val_str = ''
        for _idx, _val in enumerate(val):
            _name = f'{name}{_idx}'
            val_str_, sub_class_txt_ = val_to_str(_name, _val, class_name, class_prefix, nested, **kwargs)
            if sub_class_txt_:
                sub_class_txt += f'\n{sub_class_txt_}\n'

            val_str += f'{val_str_},'

        val_str = f'[{val_str}]'

    elif isinstance(val, dict):
        sub_class_name = name.title().replace('_', '')
        class_prefix_ = f'{class_name}'
        if class_prefix:
            class_prefix_ = f'{class_prefix}.{class_prefix_}'

        sub_class_txt = from_dict(val, class_name=sub_class_name, class_prefix=class_prefix_,
                                  return_only=True,
                                  nested=nested + 1,
                                  add_cfg=False, **kwargs)
        val_str = f'{class_prefix_}.{sub_class_name}()'
    elif isinstance(val, str):
        val_str = f"'{val}'"
    else:
        val_str = f'{val}'

    return val_str, sub_class_txt


def from_dict(param_dict, class_name='Params',
              add_cfg=True, add_help=True,
              return_only=False, to_clipboard=False,
              sort_by_name=True, nested=0, class_prefix='', add_init=True):
    """
    convert a dictionary into a parameter class compatible with this module
    supports nested dictionaries by creating a nested class for each
    optionally writes the class code to a python source file named  <class_name>.py or copies it to the clipboard

    :param dict param_dict:
    :param str class_name:
    :param bool add_cfg:
    :param bool add_help:
    :param bool return_only:
    :param bool to_clipboard:
    :param bool sort_by_name:
    :param int nested:
    :param bool add_init:
    :param str class_prefix:
    :return:
    """

    all_params_names = list(param_dict.keys())

    if sort_by_name:
        all_params_names.sort()

    if nested:
        nesting_str = '\t' * nested
    else:
        nesting_str = ''

    header_text = f'{nesting_str}class {class_name}:\n'
    sub_class_txt = ''
    out_text = ''
    if add_init:
        out_text += f'{nesting_str}\tdef __init__(self):\n'
    if add_cfg and 'cfg' not in all_params_names:
        if add_init:
            out_text += f"{nesting_str}\t\tself.cfg = ()\n"
        else:
            out_text += f"{nesting_str}\t\tcfg = ()\n"

    # help_text = '\t\tself.help = {\n'
    help_text = f'{nesting_str}\t"""\n'

    # doc_text = '\t"""\n'

    for _name in all_params_names:
        default_val = param_dict[_name]
        _help = ''

        default_str, sub_class_txt_ = val_to_str(
            name=_name,
            val=default_val,
            class_name=class_name,
            class_prefix=class_prefix,
            nested=nested,
            add_help=add_help,
            add_init=add_init,
        )

        if sub_class_txt_:
            assert add_init, "nested classes do not work without __init__"
            sub_class_txt += f'\n{sub_class_txt_}\n'

        var_name = _name.replace('-', '_').replace(' ', '_')

        if add_init:
            out_text += f'{nesting_str}\t\tself.{var_name} = {default_str}\n'
        else:
            out_text += f'{nesting_str}\t\t{var_name} = {default_str}\n'

        # help_text += "\t\t\t'{}': '{}',\n".format(var_name, _help)
        help_text += f"{nesting_str}\t:ivar {var_name}: {_help}\n"
        help_text += f"{nesting_str}\t:type {var_name}: {type(default_val).__name__}\n\n"

        # doc_text += '\t:param {} {}: {}\n'.format(type(default_val).__name__, var_name, _help)

    # help_text += "\t\t}"
    help_text += f'{nesting_str}\t"""\n'

    # doc_text += '\t"""\n'

    if add_help:
        # out_text += help_text
        out_text = help_text + out_text

    # if add_doc:
    #     out_text = doc_text + out_text

    out_text = header_text + out_text + sub_class_txt
    # time_stamp = datetime.now().strftime("%y%m%d_%H%M%S")

    if return_only:
        return out_text

    if to_clipboard:
        try:
            import pyperclip

            pyperclip.copy(out_text)
            spam = pyperclip.paste()
        except BaseException as e:
            print('Copying to clipboard failed: {}'.format(e))
        else:
            print('Class definition for class {} copied to clipboard'.format(class_name))

    else:
        class_name_snake_case = re.sub(r'(?<!^)(?=[A-Z])', '_', class_name).lower()
        out_fname = '{}.py'.format(class_name_snake_case)
        out_path = linux_path(os.path.abspath(out_fname))

        if os.path.exists(out_path):
            print('output path already exists so not writing to it: {}'.format(out_path))
        else:
            print('Writing output to {}'.format(out_path))
            with open(out_path, 'w') as fid:
                fid.write(out_text)


def from_function(fn, class_name='', start=0, only_kw=True,
                  add_cfg=True, add_doc=True, add_help=True,
                  to_clipboard=False, sort_by_name=True):
    args, varargs, varkw, defaults = inspect.getargspec(fn)

    if not class_name:
        class_name = fn.__name__

    args = args[start:]

    n_defaults = len(defaults)
    n_non_defaults = len(args) - n_defaults

    args_dict = dict(zip(args[-n_defaults:], defaults))
    if not only_kw and n_non_defaults:
        args_dict_non_defaults = dict(zip(args[:n_defaults], [None, ] * n_non_defaults))
        args_dict.update(args_dict_non_defaults)

    from_dict(args_dict, class_name, add_cfg=add_cfg,
              add_doc=add_doc, add_help=add_help,
              to_clipboard=to_clipboard, sort_by_name=sort_by_name)


if __name__ == '__main__':
    try:
        from Tkinter import Tk
    except ImportError:
        from tkinter import Tk

    in_txt = Tk().clipboard_get()
    _dict = literal_eval(in_txt)

    if not isinstance(_dict, dict):
        raise IOError('Clipboard contents do not form a valid dict:\n{}'.format(in_txt))
    from_dict(_dict)
