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

import numpy as np

try:
    import cPickle as pickle
except ImportError:
    import pickle


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

        self.parent = parent
        self.orig_text = orig_text
        self.parent_text = parent_text
        # self.marker = marker
        self.line_id = line_id
        self.end_id = end_id
        self.seq_id = seq_id
        self.curr_level = curr_level
        self.template_id = template_id
        self.children = []

        self.added = 0

        if parent is None:
            self.is_root = True
            self.full_name = self.name
        else:
            self.is_root = False
            self.full_name = parent.name + self.name
            parent.children.append(self)

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


def match_opt(params, opt_name, print_name=''):
    """

    :param params:
    :param str opt_name:
    :param str print_name:
    :return:
    """

    if not print_name:
        print_name = opt_name

    opt_val = str(getattr(params, opt_name))
    opt_vals = params.help[opt_name]  # type: dict

    matching_val = [k for k in opt_vals.keys() if opt_val in opt_vals[k]]
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
            _str = '{:s}{:s}:{:s},'.format(_str, key_str, scalar_to_string(val))
        elif isinstance(val, (tuple, list)):
            _str = '{:s}{:s}:{:s},'.format(_str, key_str, tuple_to_string(val))
        elif isinstance(val, dict):
            _str = '{:s}{:s}:{:s},'.format(_str, key_str, dict_to_string(val))
    _str += '}}'
    return _str


def strip_quotes(val):
    return val.strip("\'").strip('\"')


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
            return tuple(np.arange(*_temp))
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


def str_to_basic_type(_val):
    # if _type == str:
    #     _val_parsed = _val
    #     if _val_parsed == '__n__':
    #         _val_parsed = ''
    #     return _val_parsed

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


def save(obj, dir_name, out_name='params.bin'):
    save_path = os.path.join(dir_name, out_name)
    pickle.dump(obj, open(save_path, "wb"))


def load(obj, dir_name, prefix='', out_name='params.bin'):
    load_path = os.path.join(dir_name, out_name)
    params = pickle.load(open(load_path, "rb"))
    missing_params = []
    _recursive_load(obj, params, prefix, missing_params)
    if missing_params:
        print('Missing loaded parameters found:\n{}'.format(pformat(missing_params)))


def write(obj, dir_name, prefix='', out_name='params.cfg'):
    save_path = os.path.join(dir_name, out_name)
    save_fid = open(save_path, "w")
    _recursive_write(obj, prefix, save_fid)


def read(obj, dir_name, prefix='', out_name='params.cfg', allow_unknown=0):
    load_path = os.path.join(dir_name, out_name)
    lines = open(load_path, "r").readlines()
    args_in = ['--{}'.format(k.strip()) for k in lines]
    if prefix:
        args_in = [k.replace(prefix + '.', '') for k in args_in]
    process(obj, args_in=args_in, prog=prefix,
            usage=None, allow_unknown=allow_unknown)


def _recursive_load(obj, loaded_obj, prefix, missing_params):
    load_members = [attr for attr in dir(loaded_obj) if
                    not callable(getattr(loaded_obj, attr)) and not attr.startswith("_")]
    obj_members = [attr for attr in dir(obj) if not callable(getattr(obj, attr)) and not attr.startswith("_")]
    for member in obj_members:
        member_name = '{:s}.{:s}'.format(prefix, member) if prefix else member
        if member not in load_members:
            missing_params.append(member_name)
            continue
        default_val = getattr(obj, member)
        load_val = getattr(loaded_obj, member)
        if isinstance(default_val, (int, bool, float, str, tuple, list, dict)):
            setattr(obj, member, load_val)
        else:
            _recursive_load(default_val, load_val, member_name, missing_params)


def _recursive_write(obj, prefix, save_fid):
    obj_members = [attr for attr in dir(obj) if not callable(getattr(obj, attr)) and not attr.startswith("_")]
    for member in obj_members:
        if member == 'help':
            continue
        member_val = getattr(obj, member)
        member_name = '{:s}.{:s}'.format(prefix, member) if prefix else member
        if isinstance(member_val, (int, bool, float, str)):
            save_fid.write('{:s}={:s}\n'.format(member_name, scalar_to_string(member_val)))
        elif isinstance(member_val, tuple):
            save_fid.write('{:s}={:s}\n'.format(member_name, tuple_to_string(member_val)))
        elif isinstance(member_val, dict):
            save_fid.write('{:s}={:s}\n'.format(member_name, dict_to_string(member_val)))
        else:
            _recursive_write(member_val, member_name, save_fid)


def help_from_docs(obj, member):
    _help = ''
    doc = inspect.getdoc(obj)
    if doc is None:
        return _help

    doc_lines = doc.splitlines()
    if not doc_lines:
        return _help

    templ = ':param {} {}: '.format(type(getattr(obj, member)).__name__, member)
    relevant_line = [k for k in doc_lines if k.startswith(templ)]

    if relevant_line:
        _help = relevant_line[0].replace(templ, '')

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


def _add_params_to_parser(parser, obj, member_to_type, root_name='', obj_name=''):
    """

    :param argparse.ArgumentParser parser:
    :param obj:
    :param dict member_to_type:
    :param str root_name:
    :param str obj_name:
    :return:
    """
    members = tuple([attr for attr in dir(obj) if not callable(getattr(obj, attr))
                     and not attr.startswith("_")])
    if obj_name:
        if root_name:
            root_name = '{:s}.{:s}'.format(root_name, obj_name)
        else:
            root_name = '{:s}'.format(obj_name)
    for member in members:
        if member == 'help':
            continue
        default_val = getattr(obj, member)
        member_type = type_from_docs(obj, member)
        if member_type is None:
            if default_val is None:
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

            if hasattr(obj, 'help') and member in obj.help:
                _help = obj.help[member]
                if not isinstance(_help, str):
                    _help = pformat(_help)
            else:
                _help = help_from_docs(obj, member)

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
            _add_params_to_parser(parser, getattr(obj, member), member_to_type, root_name, member)


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


def read_cfg(_cfg):
    print('Reading parameters from {:s}'.format(_cfg))
    file_args = [k.strip() for k in open(_cfg, 'r').readlines()]
    file_args_offset = 0

    if not file_args[0].startswith('##'):
        file_args.insert(0, '##')
        file_args_offset = 1
    _sections = [(k.lstrip('#').strip(), i, k.count('#') - 1, 0)
                 for i, k in enumerate(file_args) if k.startswith('##')]

    n_file_args = len(file_args)
    n_sections = len(_sections)

    """common sections"""
    _sections = [k if k[0] else ('__common__', k[1], k[2], k[3]) for k in _sections]

    """add section end IDs as the start IDs of the next section"""
    _sections = [(k[0], k[1], _sections[i + 1][1] if i < n_sections - 1 else n_file_args, k[2], k[3])
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
            if _sec_name.startswith('(') or _sec_name.startswith('[') or ':' in _sec_name or \
                    _sec_name.startswith('range(') or _sec_name.startswith('irange('):
                # assert ',' not in _sec_name, \
                #     "Combining template and range sections is not supported currently"
                """in case there are multiple ranges or lists"""
                in_range_sec_names = _sec_name.split('+')
                for in_range_sec_name in in_range_sec_names:
                    range_tokens = in_range_sec_name.split('_')
                    range_tuples = tuple(map(str_to_tuple, range_tokens))

                    def _get_sec_names(_sec_names, _tuples, _id, _nums):
                        for _num in _tuples[_id]:
                            __nums = _nums[:]
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
                    _temp_sections.append((k, _sec[1], _sec[2], _sec[3], _curr_template_id))
                    for descendant in descendants:  # type: Node
                        _temp_sections.append(
                            (descendant.name, descendant.line_id, descendant.end_id, descendant.curr_level, 0))
                        descendant.added = 1
                        # if k_id == 0:
                        #     # assert not is_template(descendant.name), \
                        #     #     f"template section: {descendant.name} used as a descendant of " \
                        #     #         f"another: {_sec_name}"
                        #     _added_sections[(descendant.line_id, descendant.curr_level)] = 1
            else:
                _temp_sections += [(k, _sec[1], _sec[2], _sec[3], _curr_template_id) for k in _templ_sec_names]
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

    return nodes, dict(nodes_by_fullname), _sections, file_args, file_args_offset, root_sec_name


def process(obj, args_in=None, cmd=True, cfg='', cfg_root='', cfg_ext='',
            prog='', usage='%(prog)s [options]', allow_unknown=0):
    """

    :param obj:
    :param list | None args_in:
    :param bool cmd: enable command line argument processing
    :param str cfg:
    :param str cfg_root:
    :param str cfg_ext:
    :param str prog:
    :param str | None usage:
    :param int allow_unknown:
    :return:
    """
    arg_dict = {}
    if prog:
        arg_dict['prog'] = prog
    if usage is None:
        arg_dict['usage'] = argparse.SUPPRESS
    elif usage:
        arg_dict['usage'] = usage
    if hasattr(obj, 'help') and '__desc__' in obj.help:
        arg_dict['description'] = obj.help['__desc__']

    parser = argparse.ArgumentParser(**arg_dict)
    member_to_type = {}
    _add_params_to_parser(parser, obj, member_to_type)

    if args_in is None:
        argv_id = 1

        if not cfg:
            # check for cfg files specified at command line
            if cmd and len(sys.argv) > 1 and ('--cfg' in sys.argv[1] or sys.argv[1].startswith('cfg=')):
                _, arg_val = sys.argv[1].split('=')
                cfg = arg_val
                argv_id += 1
                if hasattr(obj, 'cfg'):
                    obj.cfg = cfg
            cfg = getattr(obj, 'cfg', cfg)

        if not cfg_root:
            cfg_root = getattr(obj, 'cfg_root', cfg_root)

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
                _cfg = '{}:__common__'.format(_cfg)

            _cfg = _cfg.replace('-', '')
            _cfg = _cfg.split(':')
            _cfg_sec = [k for k in list(_cfg[1:]) if k]
            _cfg = _cfg[0]

            """optional leading and trailing for better visible discrimination between cfg files and sections 
            in commands stored in syntax highlighted markdown files"""
            if _cfg.startswith('_') and _cfg.endswith('_'):
                _cfg = _cfg.strip('_')

            if cfg_ext:
                _cfg = '{}.{}'.format(_cfg, cfg_ext)
            if cfg_root:
                _cfg = os.path.join(cfg_root, _cfg)
            if not os.path.isfile(_cfg):
                if _cfg:
                    raise IOError('cfg file does not exist: {:s}'.format(_cfg))
            repeated_cfgs = []

            repeated_sec_ids = [__sec_id for __sec_id, __sec in enumerate(_cfg_sec) if '+' in __sec]

            excluded_ids = []

            for i, __sec_id in enumerate(repeated_sec_ids):

                if _cfg_sec[__sec_id].startswith('++'):
                    """these sections are exclusive to the repeated cfg files so excluded from the default one"""
                    _exclusive_secs = 1
                    __sec_names = _cfg_sec[__sec_id][2:].split('+')
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
                    repeated_cfgs.append((_cfg, included_secs, 1))
                if _exclusive_secs:
                    excluded_ids += list(range(start_include_id, end_include_id))

            _cfg_sec = [k for i, k in enumerate(_cfg_sec) if i not in excluded_ids and k]
            cfg_file_list.append((_cfg, _cfg_sec, 0))
            cfg_file_list += repeated_cfgs

        """process each cfg file and its sections"""
        args_in = []
        prev_cfg_data = []
        for _cfg, _cfg_sec, _cfg_repeat in cfg_file_list:
            if _cfg_repeat:
                assert prev_cfg_data, "repeat cfg found without previous cfg data: {}".format(_cfg)
                print('Processing repeat parameters from {:s}'.format(_cfg))
            else:
                prev_cfg_data = read_cfg(_cfg)

                # _sections = [(k, i) for k, i in _sections]

            nodes, nodes_by_fullname, _sections, _file_args, file_args_offset, root_sec_name = prev_cfg_data

            n_file_args = len(_file_args)

            """remove excluded sections"""
            excluded_cfg_sec = [_sec.lstrip('!') for _sec in _cfg_sec if _sec.startswith('!')]
            sections, section_line_ids, section_end_ids, section_seq_ids, section_template_ids = zip(
                *[(_sec[0], _sec[1], _sec[2], i, _sec[4]) for i, _sec in enumerate(_sections)
                  if _sec not in excluded_cfg_sec])

            if excluded_cfg_sec:
                print('Excluding section(s):\n{}'.format(pformat(excluded_cfg_sec)))
                _cfg_sec = [_sec for _sec in _cfg_sec if _sec not in excluded_cfg_sec]
                assert _cfg_sec, 'No included sections found for {}'.format(_cfg)

            """add common sections"""
            common_sections = [s for s in sections if s.startswith('__') and s.endswith('__')]
            _cfg_sec += common_sections

            """unique section names"""
            _cfg_sec = list(set(_cfg_sec))

            """specific sections from full names"""
            invalid_sec = [(_id, _sec) for _id, _sec in enumerate(_cfg_sec) if _sec not in sections]
            specific_sec = []
            specific_sec_ids = {}

            # _node_matches = {( _id, _sec) : nodes[k] for _id, _sec in invalid_sec for k in nodes
            #                  if nodes[k].full_name == _sec}
            for _id, _sec in invalid_sec:
                try:
                    _node_matches = nodes_by_fullname[_sec]  # type: list
                except KeyError:
                    raise AssertionError('Section {} not found in {}'.format(
                        _sec, _cfg))

                # curr_specific_sec = []
                for _node in _node_matches:  # type:Node

                    parent = _node.parent
                    specific_sec.append((_node.seq_id, _node.name))
                    specific_sec_ids[_node.seq_id] = 0

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
            _cfg_sec_ids = [[i for i, x in enumerate(sections) if _sec and x == _sec] for _sec in _cfg_sec]

            # _cfg_sec_ids = [item for sublist in _cfg_sec_ids for item in sublist]

            """flatten
            """
            __cfg_sec_ids = []
            __cfg_sec = []
            for _sec, _sec_ids in zip(_cfg_sec, _cfg_sec_ids):
                for _sec_id in _sec_ids:
                    __cfg_sec.append(_sec)
                    __cfg_sec_ids.append(_sec_id)

            _cfg_sec_disp = []
            valid_cfg_sec = []
            _sec_args = []
            valid_parent_names = [root_sec_name, ]
            valid_parent_seq_ids = [None, ]
            _common_str = ''

            for _sec_id, x in specific_sec:
                __cfg_sec_ids.append(_sec_id)
                __cfg_sec.append(x)

            # n_sections = len(sections)

            """sort by line and process each cfg section
            """
            __cfg_sec_sorted = sorted(zip(__cfg_sec_ids, __cfg_sec))

            for _sec_id, x in __cfg_sec_sorted:

                _curr_sec_seq_id = section_seq_ids[_sec_id]
                _curr_sec_node = nodes[_curr_sec_seq_id]  # type: Node

                _curr_sec_parent_name = _curr_sec_node.parent.name
                _curr_sec_parent_seq_id = _curr_sec_node.parent.seq_id
                _curr_sec_seq_id = _curr_sec_node.seq_id
                _curr_sec_name = sections[_sec_id]
                _curr_sec_full_name = _curr_sec_node.full_name
                _curr_sec_parent_full_name = _curr_sec_node.parent.full_name

                ancestors = _curr_sec_node.get_ancestors()
                _curr_sec_ancestral_path = ':'.join([ancestor.name for ancestor in ancestors[::-1]] +
                                                    [_curr_sec_name, ])

                assert x == _curr_sec_name, "mismatch between x: {} and _curr_sec_name: {}".format(x, _curr_sec_name)

                if _curr_sec_parent_seq_id not in valid_parent_seq_ids:
                    # if _sec_id in specific_sec_ids and specific_sec_ids[_sec_id] == 0:
                    #     raise AssertionError('Specific section {} not found'.format(_curr_sec_ancestral_path))
                    # print('skipping section {}'.format(_curr_sec_ancestral_path))
                    continue

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
                    if x not in common_sections:
                        # print('skipping empty section {} ({}, {})'.format(x, orig_start_id, orig_end_id))
                        assert orig_start_id == orig_end_id, "invalid empty section {} ({}, {})".format(
                            x, orig_start_id, orig_end_id)
                    continue

                _curr_sec_args = _file_args[_start_id:_end_id]

                for i, _curr_sec_arg in enumerate(_curr_sec_args):
                    _curr_sec_args[i] = _curr_sec_args[i].replace('__name__', _curr_sec_name)
                    _curr_sec_args[i] = _curr_sec_args[i].replace('__parent_name__', _curr_sec_parent_name)

                    if '__name_ratio__' in _curr_sec_args[i]:
                        ratio_str = str(float(_curr_sec_name) / 100.0)
                        _curr_sec_args[i] = _curr_sec_args[i].replace('__name_ratio__', ratio_str)

                    _curr_sec_args[i] = _curr_sec_args[i].replace('__name_list__',
                                                                  ','.join(_curr_sec_name.split('_')))
                    if '__name_list_ratio__' in _curr_sec_args[i]:
                        temp = _curr_sec_name.split('_')
                        for k_id, k in enumerate(temp):
                            if k.startswith('n'):
                                k = k.replace('n', '-')
                            k = str(float(k) / 100.0)
                            temp[k_id] = k
                        _curr_sec_args[i] = _curr_sec_args[i].replace('__name_list_ratio__', ','.join(temp))

                    _curr_sec_args[i] = _curr_sec_args[i].replace('__name_range__',
                                                                  ':'.join(_curr_sec_name.split('_')))

                    _curr_sec_args[i] = _curr_sec_args[i].replace('__full_name__', _curr_sec_full_name)
                    _curr_sec_args[i] = _curr_sec_args[i].replace('__parent_full_name__',
                                                                  _curr_sec_parent_full_name)

                _sec_args += _curr_sec_args

                start_line_num = _start_id + 1 - file_args_offset
                end_line_num = _end_id - file_args_offset

                if x not in common_sections:

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

            invalid_cfg_sec = [k for k in __cfg_sec if k and k not in valid_cfg_sec]
            if invalid_cfg_sec:
                raise AssertionError('Invalid cfg sections provided for {}:\n {}'.format(_cfg, invalid_cfg_sec))

            if _common_str:
                _common_str = 'common: {}'.format(_common_str)
                _cfg_sec_disp.append(_common_str)

            print('\t{}'.format(
                '\n\t'.join(_cfg_sec_disp)
                # pformat(_cfg_sec_disp)
            ))

            file_args = _sec_args

            file_args = [arg.strip() for arg in file_args if arg.strip()]
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
            cmd_args = list(sys.argv[argv_id:])
            if cmd_args and cmd_args[0] in ('--h', '-h', '--help'):
                # args_in.insert(0, cmd_args[0])
                help_mode = cmd_args[0]
                cmd_args = cmd_args[1:]
            args_in += cmd_args

        args_in = [k if k.startswith('--') else '--{}'.format(k) for k in args_in]

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
                try:
                    arg_type = member_to_type[_name]
                except KeyError:
                    raise ValueError('Invalid param name {} in argument {}'.format(_name, _arg))
                assert arg_type in (tuple, list, MultiPath, MultiCFG), \
                    "incremental value specification found for argument {} of invalid type: {}".format(_name, arg_type)
                try:
                    old_val = _args_dict[_name]
                except KeyError:
                    pass
                    # print('Accumulative value provided for uninitialized arg: {} :: {}'.format(
                    #     _name, _arg))
                else:
                    if arg_type is MultiPath:
                        sep = '_'
                    elif arg_type is MultiCFG:
                        sep = '::'
                    else:
                        sep = ','
                    _val = '{}{}{}'.format(old_val, sep, _val)
                    pass
            else:
                try:
                    _name, _val = _arg.split('=')
                except ValueError as e:
                    raise ValueError('Invalid argument provided: {} :: {}'.format(_arg, e))
                if pf:
                    _name = '{}.{}'.format(pf, _name)

            _args_in.append('--{}={}'.format(_name, _val))
            _args_dict[_name] = _val

        args_in = _args_in

        _args_in = []
        for _arg_str in args_in:
            _name, _val = _arg_str.split('=')
            if _val and not _val.startswith('#'):
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

    # print('train_seq_ids: ', self.train_seq_ids)
    # print('test_seq_ids: ', self.test_seq_ids)

    return args_in


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


def from_parser(parser, class_name='Params', allow_none_default=1,
                add_doc=True, add_help=True, to_clipboard=False):
    """
    convert argparse.ArgumentParser object into a parameter class compatible with this module
    writes the class code to a python source file named  <class_name>.py

    :param argparse.ArgumentParser parser:
    :param str class_name:
    :return:
    """

    optionals = parser._optionals._option_string_actions
    positionals = parser._positionals._option_string_actions

    all_params = optionals.copy()
    all_params.update(positionals)

    all_params_names = sorted(list(all_params.keys()))

    header_text = 'class {}:\n'.format(class_name)
    out_text = '\tdef __init__(self):\n'
    if '--cfg' not in all_params_names:
        out_text += "\t\tself.cfg = ('', )\n"
    help_text = '\t\tself.help = {\n'

    if parser.description is not None:
        help_text += "\t\t\t'__desc__': '{}',\n".format(parser.description)

    doc_text = '\t"""\n'

    for _name in all_params_names:
        __name = _name[2:]
        if not __name or _name in ('--h', '-h', '--help'):
            continue
        _param = all_params[_name]
        _help = _param.help

        default = _param.default
        nargs = _param.nargs

        if isinstance(nargs, str):
            _param_type = list
        else:
            _param_type = _param.type

        if default is None:
            if _param_type is None:
                raise IOError('Both type and default are None for params {}'.format(__name))

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
                if _param_type is str:
                    default_str = "['{}, ]'".format(_param.default)
                else:
                    default_str = '[{} ,]'.format(_param.default)
            else:
                if _param_type is str:
                    default_str = "'{}'".format(_param.default)
                else:
                    default_str = '{}'.format(_param.default)

        var_name = __name.replace('-', '_').replace(' ', '_')

        out_text += '\t\tself.{} = {}\n'.format(var_name, default_str)
        help_text += "\t\t\t'{}': '{}',\n".format(var_name, _help)

        doc_text += '\t:param {} {}: {}\n'.format(_param_type.__name__, var_name, _help)

    help_text += "\t\t}"
    doc_text += '\t"""\n'

    if add_help:
        out_text += help_text

    if add_doc:
        out_text = doc_text + out_text

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
        out_path = os.path.abspath(out_fname)
        print('Writing output to {}'.format(out_path))
        with open(out_path, 'w') as fid:
            fid.write(out_text)


def from_dict(param_dict, class_name='Params',
              add_cfg=True, add_doc=True, add_help=True,
              to_clipboard=False):
    """
    convert a dictionary into a parameter class compatible with this module
    writes the class code to a python source file named  <class_name>.py

    :param dict param_dict:
    :param str class_name:
    :return:
    """

    all_params_names = sorted(list(param_dict.keys()))

    header_text = 'class {}:\n'.format(class_name)
    out_text = '\tdef __init__(self):\n'
    if add_cfg and 'cfg' not in all_params_names:
        out_text += "\t\tself.cfg = ('', )\n"
    help_text = '\t\tself.help = {\n'
    doc_text = '\t"""\n'

    for _name in all_params_names:
        default = param_dict[_name]
        _help = ''

        if isinstance(default, str):
            default_str = "'{}'".format(default)
        else:
            default_str = '{}'.format(default)

        var_name = _name.replace('-', '_').replace(' ', '_')

        out_text += '\t\tself.{} = {}\n'.format(var_name, default_str)
        help_text += "\t\t\t'{}': '{}',\n".format(var_name, _help)

        doc_text += '\t:param {} {}: {}\n'.format(type(default).__name__, var_name, _help)

    help_text += "\t\t}"
    doc_text += '\t"""\n'

    if add_help:
        out_text += help_text

    if add_doc:
        out_text = doc_text + out_text

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
            print('Class definition for class {} copied to clipboard'.format(class_name))

    else:
        class_name_snake_case = re.sub(r'(?<!^)(?=[A-Z])', '_', class_name).lower()
        out_fname = '{}.py'.format(class_name_snake_case)
        out_path = os.path.abspath(out_fname)
        print('Writing output to {}'.format(out_path))
        with open(out_path, 'w') as fid:
            fid.write(out_text)


def from_function(fn, class_name='', start=0, only_kw=True,
                  add_cfg=True, add_doc=True, add_help=True,
                  to_clipboard=False):
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
              to_clipboard=to_clipboard)


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
