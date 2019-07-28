import argparse
import paramparse

parser = argparse.ArgumentParser(description='FromParserDemo')

parser.add_argument('--name', default='', type=str, help='name of the experiment')
parser.add_argument('--cuda', default=True, type=bool, help='enable cuda')
parser.add_argument('--max_iter', default=1e6, type=float, help='maximum training iteration')
parser.add_argument('--batch_size', default=64, type=int, help='batch size')

parser.add_argument('--z_dim', default=10, type=int, help='dimension of the representation z')
parser.add_argument('--gamma', default=6.4, type=float, help='gamma hyperparameter')
parser.add_argument('--lr_VAE', default=1e-4, type=float, help='learning rate of the VAE')
parser.add_argument('--beta1_VAE', default=0.9, type=float, help='beta1 parameter of the Adam optimizer for the VAE')
parser.add_argument('--beta2_VAE', default=0.999, type=float, help='beta2 parameter of the Adam optimizer for the VAE')
parser.add_argument('--lr_D', default=1e-4, type=float, help='learning rate of the discriminator')
parser.add_argument('--beta1_D', default=0.5, type=float,
                    help='beta1 parameter of the Adam optimizer for the discriminator')
parser.add_argument('--beta2_D', default=0.9, type=float,
                    help='beta2 parameter of the Adam optimizer for the discriminator')

parser.add_argument('--dset_dir', default='data', type=str, help='dataset directory')
parser.add_argument('--dataset', default='dsprites_multi', type=str, help='dataset name')
parser.add_argument('--sub_dataset', default='64x64_min_1_max_2_rad_2', type=str, help='sub_dataset name')
parser.add_argument('--image_size', default=64, type=int, help='image size. now only (64,64) is supported')
parser.add_argument('--num_workers', default=2, type=int, help='dataloader num_workers')

parser.add_argument('--viz_on', default=1, type=int, help='enable visdom visualization')
parser.add_argument('--viz_port', default=8097, type=int, help='visdom port number')
parser.add_argument('--viz_ll_iter', default=1000, type=int, help='visdom line data logging iter')
parser.add_argument('--viz_la_iter', default=5000, type=int, help='visdom line data applying iter')
parser.add_argument('--viz_ra_iter', default=10000, type=int, help='visdom recon image applying iter')
parser.add_argument('--viz_ta_iter', default=10000, type=int, help='visdom traverse applying iter')

parser.add_argument('--print_iter', default=500, type=int, help='print losses iter')

parser.add_argument('--ckpt_dir', default='checkpoints', type=str, help='checkpoint directory')
parser.add_argument('--ckpt_load', default='', type=str, help='checkpoint name to load')
parser.add_argument('--ckpt_save_iter', default=10000, type=int, help='checkpoint save iter')

parser.add_argument('--output_dir', default='outputs', type=str, help='output directory')
parser.add_argument('--output_save', default=True, type=bool, help='whether to save traverse results')

paramparse.fromParser(parser, 'FromParserDemoParams')

dict_params = {
        'seq_paths': '',
        'seq_prefix': '',
        'class_names_path': '../labelling_tool/data//predefined_classes_orig.txt',
        'root_dir': '',
        'save_file_name': '',
        'csv_paths': '',
        'csv_root_dir': '',
        'map_folder': '',
        'load_path': '',
        'n_classes': 4,
        'data_type': 'annotations',
        'img_ext': 'png',
        'batch_size': 1,
        'show_img': 0,
        'save_video': 1,
        'n_frames': 0,
        'codec': 'H264',
        'fps': 20,
        'enable_masks': 0,
        'n_vis': 1,
        'vis_size': '1280x720',
        'save': 0,
        'save_fmt': 'jpg',
        'save_dir': 'vis',
        'labels': [],
    }

paramparse.fromDict(dict_params, 'FromDictDemoParams')
