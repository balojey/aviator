
echo '===========================Updating os and installing dependencies================================'
sudo timedatectl set-timezone Africa/Lagos
sudo yum update -y
sudo yum install -y unzip
sudo yum install -y wget
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
# xhost +SI:localuser:$(whoami)
# touch $HOME/.Xauthority
# xauth generate :99 . trusted
export DISPLAY=:1

nohup uv run eagle_shot.py live &
echo '=========================Script execution completed================================'
