
echo '===========================Updating os and installing dependencies================================'
sudo apt update
sudo apt install -y python3-pip
sudo apt install -y libxi6
sudo apt install -y libgconf-2-4
sudo apt install -y libnss3
sudo apt install -y libxss1
sudo apt install -y libappindicator1
sudo apt install -y fonts-liberation
sudo apt install -y libatk-bridge2.0-0
sudo apt install -y libgtk-3-0
sudo apt install -y xvfb
sudo apt install -y unzip
sudo curl -LsSf https://astral.sh/uv/install.sh | sh
echo '=========================Update completed================================'

echo '===========================Installing Chrome================================'
sudo wget https://dl.google.com/linux/direct/google-chrome-stable_current_x86_64.deb
sudo apt install ./google-chrome-stable_current_x86_64.deb
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
xvfb-run -a uv run loss_lurker.py test
echo '=========================Script execution completed================================'
