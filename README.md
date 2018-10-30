# secret-santa
A fun little secret Santa project I was doing last year

```
sudo apt install python3-venv
python3 -m venv venv
. venv/bin/activate
pip install --upgrade pip
pip install wheel
pip install -r requirements.txt
gunicorn main:app
```

I also used parts of https://www.digitalocean.com/community/tutorials/how-to-set-up-django-with-postgres-nginx-and-gunicorn-on-ubuntu-18-04 for setup
