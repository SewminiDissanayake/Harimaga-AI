# Deploying HariMaga on PythonAnywhere (free, no card)

Result: `https://<your-username>.pythonanywhere.com`

Free-plan notes: 1 web app, 512 MB disk, and the app **expires after one
month**. Log in once a month and click **"Run until 1 month from today"** on
the Web tab.

## 1. On your computer: build React and push it

PythonAnywhere has no Node.js, so the React app is built locally and the
built files are committed (normally `frontend/dist` is ignored by git).

```powershell
cd frontend
npm run build
cd ..
git add -f frontend/dist
git commit -m "Build frontend for PythonAnywhere"
git push
```

Repeat this every time you change the frontend.

## 2. Create the account

https://www.pythonanywhere.com → **Pricing & signup** → **Create a Beginner account**.

## 3. Get the code (PythonAnywhere "Bash console")

Dashboard → **Consoles** → **Bash**, then:

```bash
git clone https://github.com/SewminiDissanayake/Harimaga-AI.git
cd Harimaga-AI
python3.11 -m venv ~/.venvs/harimaga --system-site-packages
source ~/.venvs/harimaga/bin/activate
pip install flask "flask-cors>=4,<6" "flask-limiter>=4,<5" scikit-learn==1.8.0 joblib
python -c "import sys; sys.path[:0]=['.','webapp/backend']; import app; print('OK')"
```

The last line must print `OK`.

## 4. Create the web app ("Web" tab)

1. **Add a new web app** → Next → **Manual configuration** → **Python 3.11** → Next.
2. **Virtualenv:** `/home/<your-username>/.venvs/harimaga`
3. **WSGI configuration file:** click the link, delete everything, paste the
   contents of `deploy/pythonanywhere_wsgi.py`, **Save**.
4. Click the big green **Reload** button.
5. Open `https://<your-username>.pythonanywhere.com`

If something goes wrong, the **Error log** link on the Web tab shows why.

## Updating later

```bash
cd ~/Harimaga-AI && git pull
```

then **Reload** on the Web tab.
