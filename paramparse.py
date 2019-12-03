import sys
import os
import re
import json
import inspect
import argparse
from ast import literal_eval
from pprint import pformat
import numpy as np

try:
    import cPickle as pickle
except ImportError:
    import pickle


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
    if ',' not in val:
        val = '{},'.format(val)

    if any(k in val for k in ('(', '{', '[')):
        # nested tuple
        return literal_eval(val)
    else:
        arg_vals = [x for x in val.split(',') if x]
        arg_vals_parsed = []
        for _val in arg_vals:
            try:
                _val_parsed = int(_val)
            except ValueError:
                try:
                    _val_parsed = float(_val)
                except ValueError:
                    _val_parsed = _val
            if _val_parsed == '__n__':
                _val_parsed = ''
            arg_vals_parsed.append(_val_parsed)
        return arg_vals_parsed


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


def _add_params_to_parser(parser, obj, root_name='', obj_name=''):
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
            print('Deduced type {} from docstring for param {} with default as None'.format(member_type, member))
        else:
            member_type = type(default_val)

        if member_type in (int, bool, float, str, tuple, list, dict):
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
                parser.add_argument('--{:s}'.format(member_param_name), type=member_type, default=default_val,
                                    help=_help, metavar='')
        else:
            # parameter is itself an instance of some other parmeter class so its members must
            # be processed recursively
            _add_params_to_parser(parser, getattr(obj, member), root_name, member)


def _assign_arg(obj, arg, _id, val, all_params, parent_name):
    if _id >= len(arg):
        print('Invalid arg: ', arg)
        return

    _arg = arg[_id]
    obj_attr = getattr(obj, _arg)
    obj_attr_name = '{}.{}'.format(parent_name, _arg) if parent_name else _arg
    if obj_attr is None:
        _key = '--{}'.format(obj_attr_name)
        obj_attr_type = all_params[_key].type
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
        _assign_arg(obj_attr, arg, _id + 1, val, all_params, obj_attr_name)


def _process_args_from_parser(obj, args, parser):
    # arg_prefix = ''
    # if hasattr(obj, 'arg_prefix'):
    #     arg_prefix = obj.arg_prefix

    optionals = parser._optionals._option_string_actions
    positionals = parser._positionals._option_string_actions

    all_params = optionals.copy()
    all_params.update(positionals)

    members = vars(args)
    for key in members.keys():
        val = members[key]
        key_parts = key.split('.')
        _assign_arg(obj, key_parts, 0, val, all_params, '')


def process(obj, args_in=None, cmd=True, cfg='', cfg_root='', cfg_ext='',
            prog='', usage='%(prog)s [options]', allow_unknown=0):
    """

    :param obj:
    :param list | None args_in:
    :param str cmd:
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
    _add_params_to_parser(parser, obj)

    if args_in is None:
        argv_id = 1

        if not cfg:
            # check for cfg files specified at command line
            if cmd and len(sys.argv) > 1 and '--cfg' in sys.argv[1]:
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

        if ',' not in cfg:
            cfg = '{},'.format(cfg)

        cfg = cfg.split(',')

        args_in = []
        for _cfg in cfg:
            _cfg_sec = ''
            if ':' in _cfg:
                _cfg = _cfg.split(':')
                _cfg_sec = list(_cfg[1:])
                _cfg = _cfg[0]
            if cfg_ext:
                _cfg = '{}.{}'.format(_cfg, cfg_ext)
            if cfg_root:
                _cfg = os.path.join(cfg_root, _cfg)
            if _cfg and not os.path.isfile(_cfg):
                print('cfg file does not exist: {:s}'.format(_cfg))
            else:
                print('Reading parameters from {:s}'.format(_cfg))
                file_args = [k.strip() for k in open(_cfg, 'r').readlines()]
                if _cfg_sec:
                    excluded_cfg_sec = [_sec.lstrip('!') for _sec in _cfg_sec if _sec.startswith('!')]

                    _sections = [(k.lstrip('##').strip(), i) for i, k in enumerate(file_args) if k.startswith('##')]
                    sections, section_ids = zip(*[(_sec, i) for _sec, i in _sections if _sec not in excluded_cfg_sec])
                    # sections, section_ids = [k[0] for k in _sections], [k[1] for k in _sections]

                    if excluded_cfg_sec:
                        print('Excluding section(s):\n{}'.format(pformat(excluded_cfg_sec)))
                        _cfg_sec = [_sec for _sec in _cfg_sec if _sec not in excluded_cfg_sec]
                        if not _cfg_sec:
                            _cfg_sec = sections

                    common_sections = [section for section in sections if
                                       section.startswith('__') and section.endswith('__')]
                    _cfg_sec += common_sections

                    """unique section names"""
                    _cfg_sec = list(set(_cfg_sec))

                    assert all([_sec in sections for _sec in _cfg_sec]), \
                        'One or more sections from: {} not found in cfg file {} with sections:\n{}'.format(
                                _cfg_sec, _cfg, sections)

                    """all occurences of each section"""
                    _cfg_sec_ids = [[i for i, x in enumerate(sections) if x == _sec] for _sec in _cfg_sec]

                    # _cfg_sec_ids = [item for sublist in _cfg_sec_ids for item in sublist]

                    """flatten"""
                    __cfg_sec_ids = []
                    __cfg_sec = []
                    for _sec, _sec_ids in zip(_cfg_sec, _cfg_sec_ids):
                        for _sec_id in _sec_ids:
                            __cfg_sec.append(_sec)
                            __cfg_sec_ids.append(_sec_id)

                    """sort by line"""
                    _cfg_sec_iter = [(x, y) for y, x in sorted(zip(__cfg_sec_ids, __cfg_sec))]

                    if _cfg_sec:
                        print('Reading from section(s):\n{}'.format(_cfg_sec_iter))

                    _sec_args = []
                    for _sec, _sec_id in _cfg_sec_iter:
                        line_start_id = section_ids[_sec_id]
                        line_end_id = section_ids[_sec_id + 1] if _sec_id < len(sections) - 1 else len(
                            file_args)
                        _sec_args += file_args[line_start_id:line_end_id]

                    file_args = _sec_args

                file_args = [arg.strip() for arg in file_args if arg.strip()]
                # lines starting with # in the cfg file are regarded as comments and thus ignored
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
            try:
                _name, _val = _arg.split('=')
            except ValueError as e:
                raise ValueError('Invalid argument provided: {} :: {}'.format(_arg, e))
            if pf:
                _name = '{}.{}'.format(pf, _name)
            _args_in.append('--{}={}'.format(_name, _val))
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
    _process_args_from_parser(obj, args, parser)

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
        out_fname = '{}.py'.format(class_name)
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
        out_fname = '{}.py'.format(class_name)
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
