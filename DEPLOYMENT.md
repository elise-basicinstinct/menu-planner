# Deployment Guide: Menu Planner App

## Important Note About GitHub Pages

**GitHub Pages only hosts static websites (HTML/CSS/JavaScript).** Your Menu Planner is a Flask (Python) application, which needs a server to run.

**GitHub Pages will NOT work for this app.**

Instead, use one of these **free hosting platforms** that support Python/Flask:

---

## ✅ OPTION 1: Render.com (RECOMMENDED - Easiest)

**Why Render?**
- Free tier available
- Automatic deployments from GitHub
- No credit card required
- Easy setup (5 minutes)

### Step-by-Step Instructions:

#### 1. Create a GitHub Account (if you don't have one)
Go to https://github.com and sign up.

#### 2. Create a New GitHub Repository
1. Go to https://github.com/new
2. Name: `menu-planner` (or any name you like)
3. Description: "Weekly meal planner with recipe import"
4. Keep it **Public** (required for free hosting)
5. Click **"Create repository"**

#### 3. Push Your Code to GitHub

Open Terminal and run these commands:

```bash
# Navigate to your app directory
cd /Users/eliseverdonck/Desktop/CC_menu_app

# Initialize git (if not already done)
git init

# Add all files
git add .

# Create first commit
git commit -m "Initial commit: Menu Planner app"

# Connect to your GitHub repository (REPLACE 'YOUR_USERNAME' with your actual GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/menu-planner.git

# Push to GitHub
git branch -M main
git push -u origin main
```

**Enter your GitHub username and password when prompted.**

#### 4. Create Render Account
1. Go to https://render.com
2. Click **"Get Started"**
3. Sign up with your GitHub account (easiest option)

#### 5. Deploy on Render
1. Click **"New +"** button → **"Web Service"**
2. Connect your GitHub repository (`menu-planner`)
3. Configure:
   - **Name**: `menu-planner` (or your choice)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn web:app`
   - **Instance Type**: `Free`
4. Click **"Create Web Service"**

#### 6. Wait for Deployment
- Render will build and deploy your app (takes 2-5 minutes)
- You'll get a URL like: `https://menu-planner-xxxx.onrender.com`

#### 7. Important: Add Gunicorn to Requirements

Before deploying, add this to your `requirements.txt`:

```
Flask==3.0.0
recipe-scrapers>=15.9.0
selenium>=4.0.0
webdriver-manager>=4.0.0
gunicorn>=21.0.0
```

Then push the change:
```bash
git add requirements.txt
git commit -m "Add gunicorn for deployment"
git push
```

---

## ✅ OPTION 2: PythonAnywhere (Alternative)

**Why PythonAnywhere?**
- Free tier available
- No credit card required
- Web-based file management (no Git needed if you prefer)

### Step-by-Step Instructions:

#### 1. Create PythonAnywhere Account
1. Go to https://www.pythonanywhere.com
2. Click **"Start running Python online in less than a minute!"**
3. Choose **"Create a Beginner account"** (free)

#### 2. Upload Your Code
1. Click **"Files"** tab
2. Click **"Upload a file"**
3. Zip your entire `/Users/eliseverdonck/Desktop/CC_menu_app` folder first
4. Upload the zip file
5. Extract it in PythonAnywhere

**OR use Git:**
1. Click **"Consoles"** tab → **"Bash"**
2. Run:
   ```bash
   git clone https://github.com/YOUR_USERNAME/menu-planner.git
   cd menu-planner
   ```

#### 3. Create Web App
1. Click **"Web"** tab
2. Click **"Add a new web app"**
3. Choose **"Flask"**
4. Python version: **3.9**
5. Path to Flask app: `/home/YOUR_USERNAME/menu-planner/web.py`

#### 4. Configure WSGI File
1. Click on the WSGI configuration file link
2. Replace contents with:
   ```python
   import sys
   path = '/home/YOUR_USERNAME/menu-planner'
   if path not in sys.path:
       sys.path.append(path)

   from web import app as application
   ```
3. Save

#### 5. Install Dependencies
1. Click **"Consoles"** tab → **"Bash"**
2. Run:
   ```bash
   cd menu-planner
   pip install --user -r requirements.txt
   ```

#### 6. Reload Web App
1. Go back to **"Web"** tab
2. Click **"Reload YOUR_USERNAME.pythonanywhere.com"**
3. Your app will be live at: `http://YOUR_USERNAME.pythonanywhere.com`

---

## ✅ OPTION 3: Railway.app

**Why Railway?**
- Very simple deployment
- Free $5 credit per month
- Automatic deployments

### Step-by-Step Instructions:

#### 1. Create Railway Account
1. Go to https://railway.app
2. Sign up with GitHub

#### 2. Create New Project
1. Click **"New Project"**
2. Choose **"Deploy from GitHub repo"**
3. Select your `menu-planner` repository

#### 3. Configure Deployment
Railway will auto-detect your Flask app and deploy it.

Your app will be live at: `https://menu-planner-production.up.railway.app`

---

## 🔧 Troubleshooting

### Issue: Port Errors on Render
**Solution:** Render uses the `PORT` environment variable. Update `web.py`:

```python
import os

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True)
```

### Issue: Static Files Not Loading
**Solution:** Make sure your `static/` and `templates/` folders are in the same directory as `web.py`.

### Issue: ModuleNotFoundError
**Solution:** Make sure all dependencies are in `requirements.txt` and properly installed.

### Issue: Selenium Not Working on Render
**Solution:** Selenium/Chrome won't work on free tier hosting. The Coles scraper feature will not work in production. Consider removing Selenium dependencies for deployment:

Create `requirements-prod.txt`:
```
Flask==3.0.0
recipe-scrapers>=15.9.0
gunicorn>=21.0.0
```

Update Render build command to: `pip install -r requirements-prod.txt`

---

## 📝 Pre-Deployment Checklist

Before deploying, make sure:

- [ ] All sensitive data removed (no API keys in code)
- [ ] `requirements.txt` is up to date
- [ ] `debug=False` in production (or use environment variable)
- [ ] Test locally with `python3 web.py`
- [ ] All files committed to Git
- [ ] README.md exists with project description

---

## 🚀 Quick Start Summary

**For Render (Recommended):**
1. Create GitHub account → Create repository
2. Push code: `git push`
3. Create Render account
4. Deploy from GitHub
5. Done! Your app is live

**Your app will be accessible at the URL provided by the hosting platform.**

---

## 💡 Tips

- **Custom Domain**: Most platforms allow custom domains on free tier
- **Updates**: Just `git push` and your app auto-updates
- **Logs**: Check platform logs if something goes wrong
- **Free Tier Limits**:
  - Render: App sleeps after inactivity (takes 30s to wake up)
  - PythonAnywhere: Always on, but limited CPU
  - Railway: $5/month free credit

---

## Need Help?

If you get stuck:
1. Check the hosting platform's documentation
2. Make sure all files are uploaded correctly
3. Check the deployment logs for error messages
4. Verify `requirements.txt` has all dependencies
