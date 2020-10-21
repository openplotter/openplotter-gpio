## openplotter-gpio

OpenPlotter app to get data from GPIO.

### Installing

Install [openplotter-settings](https://github.com/openplotter/openplotter-settings) for **production**.

#### For production

Install GPIO from openplotter-settings app.

#### For development

Install openplotter-gpio dependencies:

`sudo apt install pigpio python3-pigpio`

Clone the repository:

`git clone https://github.com/openplotter/openplotter-gpio`

Make your changes and create the package:

```
cd openplotter-gpio
dpkg-buildpackage -b
```

Install the package:

```
cd ..
sudo dpkg -i openplotter-gpio_x.x.x-xxx_all.deb
```

Run post-installation script:

`sudo gpioPostInstall`

Run:

`openplotter-gpio`

Make your changes and repeat package, installation and post-installation steps to test. Pull request your changes to github and we will check and add them to the next version of the [Debian package](https://launchpad.net/~openplotter/+archive/ubuntu/openplotter).

### Documentation

https://openplotter.readthedocs.io

### Support

http://forum.openmarine.net/forumdisplay.php?fid=1