echo "Starting a service on a aws ec2 pytorch GPU instance"
echo "Start this script within tmux session in order to keep it running after the EC2 console closes"
source activate pytorch
pip3 install -r requirements.txt
playwright install
playwright install-deps
python3 -m app
echo "\n\n\n-----\n\n\n"
echo "Press CTRL+B then D to detach from terminal without killing the app"
echo "Then use 'tmux attach' to reconnect to the virtual terminal"
