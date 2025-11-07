# Deployment Checklist

Use this checklist when deploying your Menu Planner app to Render.com (or any hosting platform).

## ✅ Pre-Deployment Checklist

- [ ] All code tested locally
- [ ] `requirements.txt` includes `gunicorn>=21.0.0`
- [ ] `web.py` uses PORT environment variable
- [ ] `.gitignore` file created (excludes temp files)
- [ ] README.md updated with project info
- [ ] Git repository initialized

## 📤 GitHub Setup

- [ ] GitHub account created
- [ ] New repository created on GitHub
- [ ] Code pushed to GitHub:
  ```bash
  git init
  git add .
  git commit -m "Initial commit"
  git remote add origin https://github.com/YOUR_USERNAME/menu-planner.git
  git push -u origin main
  ```

## 🚀 Render.com Deployment (5 minutes)

### Step 1: Create Render Account
- [ ] Go to https://render.com
- [ ] Sign up with GitHub account

### Step 2: Create Web Service
- [ ] Click "New +" → "Web Service"
- [ ] Select your `menu-planner` repository
- [ ] Name: `menu-planner`
- [ ] Environment: `Python 3`
- [ ] Build Command: `pip install -r requirements.txt`
- [ ] Start Command: `gunicorn web:app`
- [ ] Instance Type: `Free`
- [ ] Click "Create Web Service"

### Step 3: Wait for Deployment
- [ ] Watch the deployment logs
- [ ] Wait 2-5 minutes for build to complete
- [ ] Get your live URL: `https://menu-planner-xxxx.onrender.com`

### Step 4: Test Your Live App
- [ ] Open the provided URL in browser
- [ ] Test recipe import feature
- [ ] Test meal plan generation
- [ ] Check if all static files load (CSS, JS)

## 🐛 Troubleshooting

If deployment fails:

1. **Check Build Logs**
   - Look for error messages in Render dashboard
   - Common issues: missing dependencies, Python version

2. **Verify Files**
   - [ ] `requirements.txt` exists and has all dependencies
   - [ ] `web.py` exists in root directory
   - [ ] `static/` and `templates/` folders exist

3. **Test Locally First**
   ```bash
   gunicorn web:app
   ```
   - If this works locally, it should work on Render

4. **Check Environment**
   - [ ] PORT environment variable is being used
   - [ ] All file paths are relative, not absolute

## 📝 Post-Deployment

- [ ] Share your live URL with friends/family
- [ ] Set up custom domain (optional)
- [ ] Monitor app performance in Render dashboard
- [ ] Note: Free tier apps sleep after inactivity (30s wake-up time)

## 🔄 Making Updates

After deployment, to update your live app:

```bash
# Make changes to your code
# Test locally

# Commit and push
git add .
git commit -m "Description of changes"
git push

# Render auto-deploys on push!
```

## 🎉 You're Done!

Your Menu Planner is now live and accessible to anyone with the URL!

---

**Need Help?** Check [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions and alternative hosting options.
