#!/bin/bash

if [ $# -lt 2 ]; then
    echo -e "Usage: sh $0 <protein_seq> <out_dir>"
    exit 1
fi

# path way of VF database
VF_db="/sdd/database/VFDB/VFDB_setB_pro.fas"

protein_seq=`readlink -f $1`
out_dir=`readlink -f $2`
protein_baseName=`basename $protein_seq`
tag_name=${protein_baseName%.f*}
PWD_dir=`pwd`

if [ ! -d $out_dir ]; then
    mkdir -p $out_dir
fi

if [ -e $protein_seq ]; then
    # for VF
    cd $out_dir
    blastp -query $protein_seq -out ${tag_name}.VFs.bsp -db $VF_db -evalue 1e-10 -outfmt 0 -num_threads 10 -num_descriptions 10 -num_alignments 10 &&\
    perl /sdd/database/VFDB/script/blast_m0_convert.pl -n 3 -c 40 -t VF -f ${tag_name}.VFs.bsp > ${tag_name}.VFs.xls &&\
    rm ${tag_name}.VFs.bsp

    cd $PWD_dir
else
    echo "The protein seq don't exist."
    exit 1
fi
