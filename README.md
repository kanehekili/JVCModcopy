# JVCModcopy
GTK3 python progam that converts JVC MOD files into mgp2 files for further processing.
Runs and is tested on Linux.
If you have an old JVC VideoCam, use JVCModCopy to convert the fileso n your camera to mpg2 files.

### How to install
Take the included file modcopy.tar, untar it and copy the contens to /opt/modcopy/
The included .desktop file may be copied to .local/share/applications or the common /usr/share/applications folder.

### How to use
Open the app and select the directory, where the mod files of your camera are located. Each film consists of two parts: the film (.mod) and its meta data (.moi) .
JVCModCopy parses the .moi files and changes the header of the .mod files so that they are normal mpeg 2 containers.
Select a target, where to write the converted films to. 
That's it.
