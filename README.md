Photo Guestbook
===============

This is a guestbook UI for use with the photobooth application at https://github.com/mijofa/photobooth

Install
-------
My install process for this has been as such:
* Install Kivy Launcher from the Play store
* Install Agit
* Configure Agit to clone this repo as non-bare into /sdcard/kivy/photo-guestbook

Then launch and run the app from the Kivy Launcher. I may clean this up when the bulk of the base development is done and create a .apk that will just install this app.

Usage
-----
It is currently hardcoded to use /sdcard/DCIM as the photo store, I'll make this configurable at some point.

This expects the photo store to be set up with as many directories as you want (but no subdirs within them) with files 0.jpg, 1.jpg, and 2.jpg in each. No other files are used other than the overlay drawing files and directories, these are created as necessary.
