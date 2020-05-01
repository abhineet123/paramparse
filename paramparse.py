import sys
import os
import re
import json
import inspect
import argparse
from ast import literal_eval
from pprint import pformat
from datetime import datetime

import numpy as np

try:
    import cPickle as pickle
except ImportError:
    import pickle


class Node:
    """
    :type parent: Node
    :type full_name: str
    :type name: str
    :type orig_text: str
    :type parent_text: str
    """

    def __init__(self, heading_text, parent=None, orig_text=None, parent_text=None,
                 marker=None, line_id=None, seq_id=None):
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
        self.parent = parent
        self.orig_text = orig_text
        self.parent_text = parent_text
        self.marker = marker
        self.line_id = line_id
        self.seq_id = seq_id

        if parent is None:
            self.is_root = True
            self.full_name = self.name
        else:
            self.is_root = False
            self.full_name = parent.name + self.name


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


def _find_children(nodes, _headings, root_level, _start_id, _root_node, n_headings):
    """

    :param dict nodes:
    :param _headings:
    :param root_level:
    :param _start_id:
    :param _root_node:
    :param n_headings:
    :return:
    """
    _id = _start_id
    while _id < n_headings:
        _heading, line_id, curr_level, _ = _headings[_id]
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
                        marker=_heading[0], line_id=line_id, seq_id=_id)
        nodes[(_heading, line_id)] = new_node

        ___id = _find_children(nodes, _headings, curr_level, _id + 1, new_node, n_headings)
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
        val_list = val[6:].replace(')', '').split(',')
        val_list = [int(x) for x in val_list]
        val_list = tuple(range(*val_list))
        return val_list
    elif ':' in val:
        # Try to parse the string as a range specification
        try:
            _val = val
            inclusive_start = inclusive_end = 1
            if _val.endswith(')'):
                _val = _val[:-1]
                inclusive_end = 0
            if val.startswith(')'):
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
                    not callable(getattr(loaded_obj, attr)) and not attr.startswith("__")]
    obj_members = [attr for attr in dir(obj) if not callable(getattr(obj, attr)) and not attr.startswith("__")]
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
    obj_members = [attr for attr in dir(obj) if not callable(getattr(obj, attr)) and not attr.startswith("__")]
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


_supported_types = (int, bool, float, str, tuple, list, dict, tuple, list, dict)


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
                     and not attr.startswith("__")])
    if obj_name:
        if root_name:
            root_name = '{:s}.{:s}'.format(root_name, obj_name)
        else:
            root_name = '{:s}'.format(obj_name)
    for member in members:
        if member == 'help':
            continue
        default_val = getattr(obj, member)
        if default_val is None:
            member_type = type_from_docs(obj, member)
            if member_type is None:
                print('No type found in docstring for param {} with default as None'.format(member))
                continue
            # print('Deduced type {} from docstring for param {} with default as None'.format(member_type, member))
        else:
            member_type = type(default_val)

        if member_type in (int, bool, float, str, tuple, list, dict):
            member_to_type[member] = member_type

            if root_name:
                member_param_name = '{:s}.{:s}'.format(root_name, member)
            else:
                member_param_name = '{:s}'.format(member)
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
            elif member_type is str:
                parser.add_argument('--{:s}'.format(member_param_name), type=strip_quotes, default=default_val,
                                    help=_help, metavar='')
            else:
                parser.add_argument('--{:s}'.format(member_param_name), type=str_to_basic_type, default=default_val,
                                    help=_help, metavar='')
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

        args_in = []
        for _cfg in cfg:
            _cfg_sec = []
            if ':' in _cfg:
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
            else:
                print('Reading parameters from {:s}'.format(_cfg))
                file_args = [k.strip() for k in open(_cfg, 'r').readlines()]
                n_file_args = len(file_args)
                file_args_offset = 0
                if _cfg_sec:
                    if not file_args[0].startswith('##'):
                        file_args.insert(0, '##')
                        n_file_args += 1
                        file_args_offset = 1
                    _sections = [(k.lstrip('#').strip(), i, k.count('#') - 1, 0)
                                 for i, k in enumerate(file_args) if k.startswith('##')]

                    """common sections"""
                    _sections = [k if k[0] else ('__common__', k[1], k[2], k[3]) for k in _sections]

                    # """default sections
                    # """
                    # _default_sections, _default_section_ids = zip(*[
                    #     (k[0].rstrip('__').strip(), i) for i, k in enumerate(_sections) if k[0].endswith('__')])
                    # for i, j in enumerate(_default_section_ids):
                    #     k = _sections[i]
                    #     _sections[j] = (_default_sections[i], k[1], k[2])

                    _temp_sections = []
                    _curr_template_id = 1
                    for i, _sec in enumerate(_sections):
                        if ',' in _sec[0]:
                            _templ_sec_names = _sec[0].split(',')
                            _temp_sections += [(k, _sec[1], _sec[2], _curr_template_id) for k in _templ_sec_names]
                            _curr_template_id += 1
                        else:
                            _temp_sections.append(_sec)

                    _sections = _temp_sections

                    time_stamp = datetime.now().strftime("%y%m%d_%H%M%S")
                    root_sec_name = "__root_{}__".format(time_stamp)
                    curr_root = Node(root_sec_name)
                    n_sections = len(_sections)
                    nodes = {}  # :type dict(tuple, Node)
                    _find_children(nodes, _sections, 0, 0, curr_root, n_sections)

                    # _sections = [(k, i) for k, i in _sections]

                    excluded_cfg_sec = [_sec.lstrip('!') for _sec in _cfg_sec if _sec.startswith('!')]
                    sections, section_ids, template_ids = zip(
                        *[(_sec, i, _template_id) for _sec, i, _, _template_id in _sections
                          if _sec not in excluded_cfg_sec])

                    # sections, section_ids = [k[0] for k in _sections], [k[1] for k in _sections]

                    if excluded_cfg_sec:
                        print('Excluding section(s):\n{}'.format(pformat(excluded_cfg_sec)))
                        _cfg_sec = [_sec for _sec in _cfg_sec if _sec not in excluded_cfg_sec]
                        if not _cfg_sec:
                            print('No included sections found for cfg file {} so including all sections'.format(_cfg))
                            _cfg_sec = sections

                    """add common sections
                    """
                    common_sections = [s for s in sections if s.startswith('__') and s.endswith('__')]
                    _cfg_sec += common_sections

                    """unique section names
                    """
                    _cfg_sec = list(set(_cfg_sec))

                    invalid_sec = [(_id, _sec) for _id, _sec in enumerate(_cfg_sec) if _sec not in sections]
                    specific_sec = []
                    specific_sec_ids = []
                    for _id, _sec in invalid_sec:
                        _node_matches = [nodes[k] for k in nodes if nodes[k].full_name == _sec]  # type: list[Node]
                        if not _node_matches:
                            raise AssertionError('Section {} not found in cfg file {} with sections:\n{}'.format(
                                _sec, _cfg, pformat(sections)))
                        # curr_specific_sec = []
                        for _node in _node_matches:
                            specific_sec.append((_node.seq_id, _node.name))
                            specific_sec.append((_node.parent.seq_id, _node.parent.name))

                            specific_sec_ids.append(_node.seq_id)
                            specific_sec_ids.append(_node.parent.seq_id)

                            # _sec_matches = []
                            # curr_node = _node
                            # while curr_node.parent is not None:
                            #     _sec_matches.append((curr_node.seq_id, curr_node.name))
                            #     curr_node = curr_node.parent
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

                    """sort by line
                    """
                    _cfg_sec_disp = []
                    valid_cfg_sec = []
                    _sec_args = []
                    valid_parent_names = [root_sec_name, ]
                    _common_str = ''

                    for _sec_id, x in specific_sec:
                        __cfg_sec_ids.append(_sec_id)
                        __cfg_sec.append(x)

                        # _start_id = section_ids[_sec_id] + 1
                        # _end_id = section_ids[_sec_id + 1] if _sec_id < len(sections) - 1 else n_file_args
                        #
                        # # discard empty lines from end of section
                        # while not file_args[_end_id - 1]:
                        #     _end_id -= 1

                        # _sec_args += file_args[_start_id:_end_id]

                    n_sections = len(sections)
                    for _sec_id, x in sorted(zip(__cfg_sec_ids, __cfg_sec)):

                        curr_node = nodes[(x, section_ids[_sec_id])]  # type: Node

                        if curr_node.parent.name not in valid_parent_names:
                            print('skipping node {} whose parent {} in not among valid parents: {}'.format(
                                curr_node.name, curr_node.parent.name, valid_parent_names))
                            continue

                        valid_parent_names.append(x)
                        valid_cfg_sec.append(x)

                        _start_id = section_ids[_sec_id] + 1
                        _template_id = template_ids[_sec_id]
                        if _template_id:
                            """template sections with the same ID all have same line IDs so look for the 
                            first subsequent section with different ID if any"""
                            _end_id = n_file_args
                            for i in range(_sec_id + 1, n_sections):
                                if template_ids[i] != _template_id:
                                    _end_id = section_ids[i]
                                    break
                        else:
                            _end_id = section_ids[_sec_id + 1] if _sec_id < n_sections - 1 else n_file_args

                        # discard empty lines from start of section
                        while not file_args[_start_id - 1]:
                            _start_id += 1

                        # discard empty lines from end of section
                        while not file_args[_end_id - 1]:
                            _end_id -= 1

                        if _start_id >= _end_id:
                            # print('skipping empty section {}'.format(x))
                            continue

                        _curr_sec_args = file_args[_start_id:_end_id]

                        if _template_id:
                            _curr_sec_name = sections[_sec_id]
                            _curr_sec_full_name = curr_node.full_name
                            for i, _curr_sec_arg in enumerate(_curr_sec_args):
                                _curr_sec_args[i] = _curr_sec_args[i].replace('__name__', _curr_sec_name)
                                _curr_sec_args[i] = _curr_sec_args[i].replace('__full_name__', _curr_sec_full_name)

                        _sec_args += _curr_sec_args

                        start_line_num = _start_id + 1 - file_args_offset
                        end_line_num = _end_id - file_args_offset

                        if x not in common_sections:

                            _sec_disp_name = curr_node.full_name if _sec_id in specific_sec_ids else x

                            _str = '{}: {}'.format(_sec_disp_name, start_line_num)
                            if end_line_num > start_line_num:
                                _str = '{} -> {}'.format(_str, end_line_num)
                            _cfg_sec_disp.append(_str)
                        else:
                            _str = '{}'.format(start_line_num)
                            if end_line_num > start_line_num:
                                _str = '{} -> {}'.format(_str, end_line_num)
                            _common_str = '{}, {}'.format(_common_str, _str) if _common_str else _str

                    invalid_cfg_sec = [k for k in _cfg_sec if k and k not in valid_cfg_sec]
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
            if _arg.startswith('@'):
                _name = _arg[1:].strip()
                if _name.startswith('@@'):
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
                    _name = _name[1:].strip()
                    if pf and _name:
                        pf = '{}.{}'.format(pf, _name)
                else:
                    pf = _name
                continue
            if '+=' in _arg:
                try:
                    _name, _val = _arg.split('+=')
                except ValueError as e:
                    raise ValueError('Invalid argument provided: {} :: {}'.format(_arg, e))
                if pf:
                    _name = '{}.{}'.format(pf, _name)
                try:
                    old_val = _args_dict[_name]
                except KeyError:
                    pass
                    # print('Accumulative value provided for uninitialized arg: {} :: {}'.format(
                    #     _name, _arg))
                else:
                    _val = '{},{}'.format(old_val, _val)
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
            print('Class definition copied to clipboard')

    else:
        class_name_snake_case = re.sub(r'(?<!^)(?=[A-Z])', '_', class_name).lower()
        out_fname = '{}.py'.format(class_name_snake_case)
        out_path = os.path.abspath(out_fname)
        print('Writing output to {}'.format(out_path))
        with open(out_path, 'w') as fid:
            fid.write(out_text)


def from_function(fn, class_name='Params',
                  add_cfg=True, add_doc=True, add_help=True,
                  to_clipboard=False):
    args, varargs, varkw, defaults = inspect.getargspec(fn)
    n_defaults = len(defaults)
    args_dict = dict(zip(args[-n_defaults:], defaults))
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
