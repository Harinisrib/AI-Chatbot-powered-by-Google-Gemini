# Deploy Your Chatbot as a Mobile App

## Option 1: Deploy to Streamlit Cloud (Easiest - FREE)

1. **Push your code to GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin YOUR_GITHUB_REPO_URL
   git push -u origin main
   ```

2. **Deploy on Streamlit Cloud:**
   - Go to https://share.streamlit.io/
   - Sign in with GitHub
   - Click "New app"
   - Select your repository
   - Set main file: `app.py`
   - Add your API key in "Advanced settings" > "Secrets":
     ```
     GEMINI_API_KEY = "AIzaSyCYBRWotxZxE1pQsKFHjUZ8fnhG34DI_oo"
     ```
   - Click "Deploy"

3. **Install as Mobile App:**
   - Open the deployed URL on your phone
   - **Android (Chrome):** Menu > "Add to Home screen"
   - **iPhone (Safari):** Share button > "Add to Home Screen"

## Option 2: Deploy to Render (FREE)

1. **Create `requirements.txt`** (already done)

2. **Push to GitHub** (same as above)

3. **Deploy on Render:**
   - Go to https://render.com/
   - Sign up/Login
   - Click "New +" > "Web Service"
   - Connect your GitHub repo
   - Settings:
     - Build Command: `pip install -r requirements.txt`
     - Start Command: `streamlit run app.py --server.port=$PORT --server.address=0.0.0.0`
   - Add Environment Variable:
     - Key: `GEMINI_API_KEY`
     - Value: `AIzaSyCYBRWotxZxE1pQsKFHjUZ8fnhG34DI_oo`
   - Click "Create Web Service"

4. **Install as Mobile App** (same as Option 1)

## Option 3: Build Native Android App (Advanced)

Use **Kivy** or **BeeWare** to convert Python to Android APK:

1. Install buildozer:
   ```bash
   pip install buildozer
   ```

2. Create buildozer.spec file and build APK

3. Upload to Google Play Store

## Option 4: Use Ngrok (For Testing)

1. **Install ngrok:**
   - Download from https://ngrok.com/download

2. **Run your app:**
   ```bash
   python -m streamlit run app.py
   ```

3. **Expose to internet:**
   ```bash
   ngrok http 8501
   ```

4. **Access from mobile:**
   - Use the ngrok URL on your phone
   - Add to home screen

## Recommended: Option 1 (Streamlit Cloud)
- Completely FREE
- No server management
- Works as PWA on mobile
- Easy updates via GitHub

After deployment, you can access it from anywhere and "install" it on your phone like a native app!
