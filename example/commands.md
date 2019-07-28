<!-- MarkdownTOC -->

- [main](#mai_n_)
    - [LK       @ main](#lk___main_)
        - [detrac_0_to_9_40_60       @ LK/main](#detrac_0_to_9_40_60___lk_mai_n_)
            - [5_5       @ detrac_0_to_9_40_60/LK/main](#5_5___detrac_0_to_9_40_60_lk_mai_n_)
        - [detrac_0_to_59_40_60       @ LK/main](#detrac_0_to_59_40_60___lk_mai_n_)
    - [siam_fc       @ main](#siam_fc___main_)
        - [detrac_0_to_9_40_60       @ siam_fc/main](#detrac_0_to_9_40_60___siam_fc_main_)
            - [load       @ detrac_0_to_9_40_60/siam_fc/main](#load___detrac_0_to_9_40_60_siam_fc_main_)
                - [debugging_86       @ load/detrac_0_to_9_40_60/siam_fc/main](#debugging_86___load_detrac_0_to_9_40_60_siam_fc_mai_n_)
        - [detrac_4       @ siam_fc/main](#detrac_4___siam_fc_main_)
            - [40_60       @ detrac_4/siam_fc/main](#40_60___detrac_4_siam_fc_mai_n_)
            - [10_10       @ detrac_4/siam_fc/main](#10_10___detrac_4_siam_fc_mai_n_)
        - [detrac_0_to_59_40_60       @ siam_fc/main](#detrac_0_to_59_40_60___siam_fc_main_)
    - [da_siam_rpn       @ main](#da_siam_rpn___main_)
        - [detrac_0_to_9_40_60       @ da_siam_rpn/main](#detrac_0_to_9_40_60___da_siam_rpn_main_)

<!-- /MarkdownTOC -->

<a id="mai_n_"></a>
# main

 CUDA_VISIBLE_DEVICES=1 python3 main.py

<a id="lk___main_"></a>
## LK       @ main

<a id="detrac_0_to_9_40_60___lk_mai_n_"></a>
### detrac_0_to_9_40_60       @ LK/main

CUDA_VISIBLE_DEVICES=2 python3 main.py @train seq_ids="range(10)" results_dir=log/detrac_0to9_40_60_lk @test seq_ids="range(10)" @data ratios_detrac="(0.4,0)" @trainer input.convert_to_gs=1 verbose=0 @@target.templates tracker=0 siamese.siam_fc.visualize=0 count=10 @train load=1

<a id="5_5___detrac_0_to_9_40_60_lk_mai_n_"></a>
#### 5_5       @ detrac_0_to_9_40_60/LK/main

CUDA_VISIBLE_DEVICES=1 python3 main.py @train seq_ids="range(10)" @test seq_ids="range(10)" @data ratios_detrac="(0.05,0.05)" @trainer input.convert_to_gs=1 verbose=0 @@target.templates tracker=0 siamese.siam_fc.visualize=0 count=2

<a id="detrac_0_to_59_40_60___lk_mai_n_"></a>
### detrac_0_to_59_40_60       @ LK/main

CUDA_VISIBLE_DEVICES=2 python3 main.py @train seq_ids="range(60)" results_dir=log/detrac_0to59_40_60_lk @test seq_ids="range(60)" @data ratios_detrac="(0.4,0.6)" @trainer input.convert_to_gs=1 verbose=0 @@target.templates tracker=0 siamese.siam_fc.visualize=0 count=10


<a id="siam_fc___main_"></a>
## siam_fc       @ main

<a id="detrac_0_to_9_40_60___siam_fc_main_"></a>
### detrac_0_to_9_40_60       @ siam_fc/main

CUDA_VISIBLE_DEVICES=1 python3 main.py @train seq_ids="range(10)" results_dir=log/detrac_0to9_40_60_siam_fc @test seq_ids="range(10)" @data ratios_detrac="(0.4,0.6)" @trainer verbose=0 @@target.templates tracker=1 @@siamese variant=siam_fc @@siam_fc visualize=0 count=10

<a id="load___detrac_0_to_9_40_60_siam_fc_main_"></a>
#### load       @ detrac_0_to_9_40_60/siam_fc/main

CUDA_VISIBLE_DEVICES=0 python3 main.py @train load=1 seq_ids="range(10)" results_dir=log/detrac_0to9_40_60_siam_fc @data ratios_detrac="(0.4,0)" @trainer verbose=0 @@target.templates count=10 tracker=1 @@siamese variant=siam_fc @@siam_fc visualize=0 visualize=0 

<a id="debugging_86___load_detrac_0_to_9_40_60_siam_fc_mai_n_"></a>
##### debugging_86       @ load/detrac_0_to_9_40_60/siam_fc/main

CUDA_VISIBLE_DEVICES=0 python3 main.py @train load=1 seq_ids="range(10)" results_dir=log/detrac_0to9_40_60_siam_fc @data ratios_detrac="(0.4,0)" @trainer verbose=0 @@target.templates count=10 tracker=1 @@siamese variant=siam_fc @@siam_fc visualize=0 @test seq_ids=1

<a id="detrac_4___siam_fc_main_"></a>
### detrac_4       @ siam_fc/main

<a id="40_60___detrac_4_siam_fc_mai_n_"></a>
#### 40_60       @ detrac_4/siam_fc/main

CUDA_VISIBLE_DEVICES=1 python3 main.py @train seq_ids="range(4,5)" @test seq_ids="range(4,5)" @data ratios_detrac="(0.4,0.6)" @trainer verbose=0 @@target lost.copy_while_learning=0 @@templates tracker=1 count=10 @@siamese variant=siam_fc @@siam_fc visualize=0 count=10

<a id="10_10___detrac_4_siam_fc_mai_n_"></a>
#### 10_10       @ detrac_4/siam_fc/main

CUDA_VISIBLE_DEVICES=1 python3 main.py @train seq_ids="range(4,5)" @test seq_ids="range(4,5)" @data ratios_detrac="(0.1,0.1)" @trainer verbose=0 @@target lost.copy_while_learning=1 @@templates tracker=1 count=10 @@siamese variant=siam_fc @@siam_fc visualize=0

<a id="detrac_0_to_59_40_60___siam_fc_main_"></a>
### detrac_0_to_59_40_60       @ siam_fc/main

CUDA_VISIBLE_DEVICES=0 python3 main.py @train seq_ids="range(60)" results_dir=log/detrac_0to59_40_60_siam_fc @test seq_ids="range(10)" @data ratios_detrac="(0.4,0.6)" @trainer verbose=0 @@target.templates tracker=1 count=10 @@siamese variant=siam_fc @@siam_fc visualize=0



<a id="da_siam_rpn___main_"></a>
## da_siam_rpn       @ main

<a id="detrac_0_to_9_40_60___da_siam_rpn_main_"></a>
### detrac_0_to_9_40_60       @ da_siam_rpn/main

CUDA_VISIBLE_DEVICES=1 python3 main.py @train seq_ids="range(10)" results_dir=log/detrac_0to9_40_60_da_siam_rpn @test seq_ids="range(10)" @data ratios_detrac="(0.4,0)" @trainer verbose=0 @@target.templates tracker=1 count=10 @@siamese visualize=0 variant=da_siam_rpn da_siam_rpn.visualize=0

 


