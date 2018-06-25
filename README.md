# gaitech_bci

Gaitech-BCI is a comprehensive hardware and software platform for carrying out Brain Computer Interfacing (BCI) research on ROS enabled robots. The platform includes a 10 channel wireless EEG device (Avertus H10C) having dry electrodes along with set of essential ROS packages and Graphical User Interfaces to configure multiple EEG devices, create and analyze labeled EEG datasets and write ROS based programs to control robots by using real-time EEG signals.
Pre-req:
Make sure ROS is installed and properly setup on Linux. Follow this link to install ROS according to your operating system:
http://www.ros.org/install/
recommended ROS version is kinetic

Installation:
1. Create catkin workspace
$ mkdir -p ~/gaitech_bci_ws
$ cd gaitech_bci_ws
$ mkdir src
$ catkin_make

2. Clone gaitech_bci repository in gaitech_bci_ws/src and catkin_make the workspace
$ cd ~/gaitech_bci_ws/src
$ git clone https://github.com/gaitech-robotics/gaitech-bci.git
$ cd ../
$ catkin_make

3. source the workspace environment
$ source ~/gaitech_bci_ws/devel/setup.bash


Depending on your system you might need to install following Dependencies:
python-avertuseegheadset (get it from us along with licence key)
pyqtgraph 
python-qt4
numpy
scipy
gstreamer-1.0
