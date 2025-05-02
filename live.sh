
echo '===========================Updating os and installing dependencies================================'
sudo apt update
sudo apt install -y python3-pip unzip \
    libxi6 libgconf-2-4 libnss3 libxss1 libappindicator1 \
    fonts-liberation libatk-bridge2.0-0 libgtk-3-0
sudo apt install xvfb
sudo curl -LsSf https://astral.sh/uv/install.sh | sh
echo '=========================Update completed================================'

echo '===========================Installing Chrome================================'
sudo wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install -y ./google-chrome-stable_current_amd64.deb
echo '=========================Chrome installation completed================================'

echo '===========================Installing ChromeDriver================================'
CHROME_VERSION=$(google-chrome --version | awk '{print $3}' | cut -d '.' -f 1)
sudo wget https://chromedriver.storage.googleapis.com/${CHROME_VERSION}.0.7103.49/chromedriver_linux64.zip
sudo unzip chromedriver_linux64.zip
sudo mv chromedriver /usr/local/bin/
chmod +x /usr/local/bin/chromedriver
echo '=========================ChromeDriver installation completed================================'

echo '===========================Installing project dependencies================================'
uv sync
echo '=========================Project dependencies installation completed================================'

echo '===========================Running script================================'
xvfb-run -a uv run loss_lurker.py test
echo '=========================Script execution completed================================'
