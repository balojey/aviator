
echo '===========================Updating os and installing dependencies================================'
# sudo apt update
# sudo apt install -y python3-pip
# sudo apt install -y libxi6
# sudo apt install -y libgconf-2-4
# sudo apt install -y libnss3
# sudo apt install -y libxss1
# sudo apt install -y libappindicator1
# sudo apt install -y fonts-liberation
# sudo apt install -y libatk-bridge2.0-0
# sudo apt install -y libgtk-3-0
# sudo apt install -y xvfb
sudo timedatectl set-timezone Africa/Lagos
sudo yum update -y
sudo yum install -y xorg-x11-server-Xorg xorg-x11-xinit xorg-x11-drv-dummy
sudo yum install -y unzip
sudo yum install -y xorg-x11-drv-dummy
sudo yum install -y wget
sudo yum install -y xhost
sudo mkdir -p /etc/X11/xorg.conf.d
sudo cp 10-dummy.conf /etc/X11/xorg.conf.d/
sudo Xorg -noreset +extension GLX +extension RANDR +extension RENDER \
  -logfile /tmp/xorg.log -config /etc/X11/xorg.conf.d/10-dummy.conf :99 &
export DISPLAY=:99
sudo curl -LsSf https://astral.sh/uv/install.sh | sh
echo '=========================Update completed================================'

echo '===========================Installing Chrome================================'
sudo wget https://dl.google.com/linux/direct/google-chrome-stable_current_x86_64.rpm
sudo yum install -y ./google-chrome-stable_current_x86_64.rpm
echo '=========================Chrome installation completed================================'

echo '===========================Installing ChromeDriver================================'
CHROME_VERSION=$(google-chrome --version | awk '{print $3}' | cut -d '.' -f 1)
sudo wget https://storage.googleapis.com/chrome-for-testing-public/${CHROME_VERSION}.0.7103.49/linux64/chromedriver-linux64.zip
sudo unzip chromedriver-linux64.zip
sudo mv chromedriver-linux64/chromedriver /usr/local/bin/
sudo chmod +x /usr/local/bin/chromedriver
echo '=========================ChromeDriver installation completed================================'

echo '===========================Installing project dependencies================================'
uv sync
echo '=========================Project dependencies installation completed================================'

echo '===========================Running script================================'
mkdir -p logs/live/
xhost +SI:localuser:$(whoami)
touch $HOME/.Xauthority
xauth generate :99 . trusted

uv run eagle_shot.py live
echo '=========================Script execution completed================================'
