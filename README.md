# secret-santa
A fun little secret Santa project I was doing last year

sudo apt install python3-venv
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
gunicorn main:app
