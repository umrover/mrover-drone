#! /bin/bash
echo Symlink world $(pwd)
if [ -f $(pwd)/worlds/$1.sdf ]; then
    if ! [ -f $PX4_HOME/Tools/simulation/gz/worlds/$1.sdf ]; then
        ln -s $(pwd)/worlds/$1.sdf $PX4_HOME/Tools/simulation/gz/worlds/$1.sdf
        echo Making symlink for $1.sdf
    fi
fi
