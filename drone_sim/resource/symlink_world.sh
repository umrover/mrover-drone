if [-f ./worlds/$1.sdf]; then
    ln -s ./worlds/$1.sdf $PX4_HOME/Tools/simulation/gz/worlds/$1.sdf
fi
