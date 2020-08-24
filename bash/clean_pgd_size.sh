work_dir='/home/rbp5354/trojanzoo'
cd $work_dir

dataset='sample_vggface2'
model='resnetcomp18'
attack='clean_label'
poison_generation_method='pgd'

CUDA_VISIBLE_DEVICES=3

dirname=${work_dir}/result/${dataset}/${model}/${attack}
if [ ! -d $dirname  ];then
    mkdir -p $dirname
fi

alpha=0.0
for size in {1..7}
do
    echo $size
    CUDA_VISIBLE_DEVICES=$CUDA_VISIBLE_DEVICES python ${work_dir}/backdoor_attack.py \
    --dataset $dataset --model $model --attack $attack --mark_alpha $alpha --height $size --width $size \
    --percent 0.01 --verbose --pretrain --validate_interval 1 --lr_scheduler --step_size 10 --epoch 50 --lr 1e-2 --save \
    --poison_generation_method $poison_generation_method --batch_size -64\
    > $dirname/pgd_size${size}.txt 2>&1
done