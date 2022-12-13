#!/bin/bash

source /etc/profile.d/modules.sh
set -x
module load singularity

if [ ! -d /srv/local/grandria ] ; then
    mkdir /srv/local/grandria
fi

cd /srv/local/grandria/
git clone https://github.com/garandria/linuxmms.git
cd linuxmms

if [ ! -d linux-5.13.tar.gz ] ; then
    curl -O https://cdn.kernel.org/pub/linux/kernel/v5.x/linux-5.13.tar.gz ;
fi

if [ ! -d linux-5.13 ] ; then
    tar -xf linux-5.13.tar.gz ;
fi

singularity build -F build-env.sif docker://garandria/build-env

singularity run --bind /srv/local/grandria/linuxmms:/srv/local/grandria/linuxmms build-env.sif python3 main.py >> stdout.log
