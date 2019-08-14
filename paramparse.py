import sys
import os
import json
import inspect
import argparse
from ast import literal_eval
from pprint import pformat

try:
    import cPickle as pickle
except ImportError:
    import pickle


def scalarToString(val, add_quotes=False):
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


def tupleToString(vals):
    _str = ''
    for val in vals:
        if isinstance(val, (int, bool, float, str)):
            _str = '{:s}{:s},'.format(_str, scalarToString(val, True))
        elif isinstance(val, (tuple, list)):
            _str = '{:s}{:s},'.format(_str, tupleToString(val))
        elif isinstance(val, dict):
            _str = '{:s}{:s},'.format(_str, dictToString(val))
    return '({:s})'.format(_str)


def dictToString(vals):
    _str = '{{'
    for key in vals.keys():
        val = vals[key]
        key_str = scalarToString(key)
        if isinstance(val, (int, bool, float, str)):
            _str = '{:s}{:s}:{:s},'.format(_str, key_str, scalarToString(val))
        elif isinstance(val, (tuple, list)):
            _str = '{:s}{:s}:{:s},'.format(_str, key_str, tupleToString(val))
        elif isinstance(val, dict):
            _str = '{:s}{:s}:{:s},'.format(_str, key_str, dictToString(val))
    _str += '}}'
    return _str


def strToTuple(val):
    if val.startswith('range('):
        val_list = val[6:].replace(')', '').split(',')
        val_list = [int(x) for x in val_list]
        val_list = tuple(range(*val_list))
        return val_list
    elif ',' not in val:
        val = '{},'.format(val)
    return literal_eval(val)


def save(obj, dir_name, out_name='params.bin'):
    save_path = os.path.join(dir_name, out_name)
    pickle.dump(obj, open(save_path, "wb"))


def load(obj, dir_name, prefix='', out_name='params.bin'):
    load_path = os.path.join(dir_name, out_name)
    params = pickle.load(open(load_path, "rb"))
    missing_params = []
    _recursiveLoad(obj, params, prefix, missing_params)
    if missing_params:
        print('Missing loaded parameters found:\n{}'.format(pformat(missing_params)))


def write(obj, dir_name, prefix='', out_name='params.cfg'):
    save_path = os.path.join(dir_name, out_name)
    save_fid = open(save_path, "w")
    _recursiveWrite(obj, prefix, save_fid)


def read(obj, dir_name, prefix='', out_name='params.cfg', allow_unknown=0):
    load_path = os.path.join(dir_name, out_name)
    lines = open(load_path, "r").readlines()
    args_in = ['--{}'.format(k.strip()) for k in lines]
    if prefix:
        args_in = [k.replace(prefix + '.', '') for k in args_in]
    process(obj, args_in=args_in, prog=prefix,
            usage=None, allow_unknown=allow_unknown)


def _recursiveLoad(obj, loaded_obj, prefix, missing_params):
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
            _recursiveLoad(default_val, load_val, member_name, missing_params)


def _recursiveWrite(obj, prefix, save_fid):
    obj_members = [attr for attr in dir(obj) if not callable(getattr(obj, attr)) and not attr.startswith("__")]
    for member in obj_members:
        if member == 'help':
            continue
        member_val = getattr(obj, member)
        member_name = '{:s}.{:s}'.format(prefix, member) if prefix else member
        if isinstance(member_val, (int, bool, float, str)):
            save_fid.write('{:s}={:s}\n'.format(member_name, scalarToString(member_val)))
        elif isinstance(member_val, tuple):
            save_fid.write('{:s}={:s}\n'.format(member_name, tupleToString(member_val)))
        elif isinstance(member_val, dict):
            save_fid.write('{:s}={:s}\n'.format(member_name, dictToString(member_val)))
        else:
            _recursiveWrite(member_val, member_name, save_fid)


def helpFromDocs(obj, member):
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


def _addParamsToParser(parser, obj, root_name='', obj_name=''):
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
            continue
        if isinstance(default_val, (int, bool, float, str, tuple, list, dict)):
            if root_name:
                member_param_name = '{:s}.{:s}'.format(root_name, member)
            else:
                member_param_name = '{:s}'.format(member)
            if hasattr(obj, 'help') and member in obj.help:
                _help = obj.help[member]
            else:
                _help = helpFromDocs(obj, member)

            if isinstance(default_val, (tuple, list)):
                parser.add_argument('--{:s}'.format(member_param_name), type=strToTuple,
                                    default=default_val, help=_help, metavar='')
            elif isinstance(default_val, dict):
                parser.add_argument('--{:s}'.format(member_param_name), type=json.loads, default=default_val,
                                    help=_help, metavar='')
            else:
                parser.add_argument('--{:s}'.format(member_param_name), type=type(default_val), default=default_val,
                                    help=_help, metavar='')
        else:
            # parameter is itself an instance of some other parmeter class so its members must
            # be processed recursively
            _addParamsToParser(parser, getattr(obj, member), root_name, member)


def _assignArg(obj, arg, _id, val):
    if _id >= len(arg):
        print('Invalid arg: ', arg)
        return
    _arg = arg[_id]
    obj_attr = getattr(obj, _arg)
    if isinstance(obj_attr, (int, bool, float, str, list, tuple, dict)):
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
        _assignArg(obj_attr, arg, _id + 1, val)


def _processArgsFromParser(obj, args):
    # arg_prefix = ''
    # if hasattr(obj, 'arg_prefix'):
    #     arg_prefix = obj.arg_prefix
    members = vars(args)
    for key in members.keys():
        val = members[key]
        key_parts = key.split('.')
        _assignArg(obj, key_parts, 0, val)


def process(obj, args_in=None, cmd=True, cfg='', cfg_root='', prog='',
            usage='%(prog)s [options]', allow_unknown=0):
    """

    :param obj:
    :param list | None args_in:
    :param str cmd:
    :param str cfg:
    :param str cfg_root:
    :param str prog:
    :param str | None usage:
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
    _addParamsToParser(parser, obj)

    if args_in is None:
        if not cfg:
            cfg = getattr(obj, 'cfg', cfg)
            # check for cfg files specified at command line
            if cmd and len(sys.argv) > 1 and '--cfg' in sys.argv[1]:
                _, arg_val = sys.argv[1].split('=')
                cfg = arg_val

        if not cfg_root:
            cfg_root = getattr(obj, 'cfg', cfg_root)

        if not cfg and hasattr(obj, 'cfg'):
            obj.cfg = cfg

        if isinstance(cfg, str):
            cfg = (cfg, )

        args_in = []
        for _cfg in cfg:
            if cfg_root:
                _cfg = os.path.join(cfg_root, _cfg)
            if os.path.isfile(_cfg):
                print('Reading parameters from {:s}'.format(_cfg))
                file_args = open(_cfg, 'r').readlines()
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
            cmd_args = list(sys.argv[1:])
            if cmd_args[0] in ('--h', '-h', '--help'):
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
        if help_mode:
            args_in.insert(0, help_mode)

    if allow_unknown:
        args, unknown = parser.parse_known_args(args_in)
        if unknown:
            print('Unknown arguments found:\n{}'.format(pformat(unknown)))
    else:
        args = parser.parse_args(args_in)
    _processArgsFromParser(obj, args)

    # print('train_seq_ids: ', self.train_seq_ids)
    # print('test_seq_ids: ', self.test_seq_ids)

    return args_in


def fromParser(parser, class_name='Params'):
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
        if default is None:
            raise IOError('None default found for param: {}'.format(__name))

        elif isinstance(default, str):
            default_str = "'{}'".format(_param.default)
        else:
            default_str = '{}'.format(_param.default)

        var_name = __name.replace('-', '_').replace(' ', '_')

        out_text += '\t\tself.{} = {}\n'.format(var_name, default_str)
        help_text += "\t\t\t'{}': '{}',\n".format(var_name, _help)

        doc_text += '\t:param {} {}: {}\n'.format(type(_param.default).__name__, var_name, _help)

    help_text += "\t\t}"
    doc_text += '\t"""\n'

    out_text += help_text

    out_text = header_text + doc_text + out_text
    # time_stamp = datetime.now().strftime("%y%m%d_%H%M%S")

    out_fname = '{}.py'.format(class_name)

    out_path = os.path.abspath(out_fname)

    print('Writing output to {}'.format(out_path))
    with open(out_path, 'w') as fid:
        fid.write(out_text)


def fromDict(param_dict, class_name='Params'):
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
    if 'cfg' not in all_params_names:
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

    out_text += help_text

    out_text = header_text + doc_text + out_text
    # time_stamp = datetime.now().strftime("%y%m%d_%H%M%S")

    out_fname = '{}.py'.format(class_name)

    out_path = os.path.abspath(out_fname)

    print('Writing output to {}'.format(out_path))
    with open(out_path, 'w') as fid:
        fid.write(out_text)


if __name__ == '__main__':
    try:
        from Tkinter import Tk
    except ImportError:
        from tkinter import Tk

    in_txt = Tk().clipboard_get()
    _dict = literal_eval(in_txt)

    if not isinstance(_dict, dict):
        raise IOError('Clipboard contents do not form a valid dict:\n{}'.format(in_txt))
    fromDict(_dict)
