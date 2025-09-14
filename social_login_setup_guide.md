# Social Login Setup Guide - Google & Apple

## Google OAuth 2.0 Setup

### Step 1: Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Create Project"
3. Project Name: `Tadaro Investment Bot`
4. Click "Create"

### Step 2: Enable Google+ API
1. In the Google Cloud Console, go to "APIs & Services" > "Library"
2. Search for "Google+ API"
3. Click "Enable"

### Step 3: Create OAuth 2.0 Credentials
1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth 2.0 Client IDs"
3. Application Type: "Web application"
4. Name: "Tadaro Investment Bot Web Client"
5. Authorized JavaScript origins:
   - `https://tadaro.ai`
   - `https://www.tadaro.ai`
   - `http://localhost:5000` (for development)
6. Authorized redirect URIs:
   - `https://tadaro.ai/auth/google/callback`
   - `https://www.tadaro.ai/auth/google/callback`
   - `http://localhost:5000/auth/google/callback` (for development)

### Step 4: Configure OAuth Consent Screen
1. Go to "APIs & Services" > "OAuth consent screen"
2. User Type: "External" (for now)
3. Application Information:
   - App name: `Tadaro Investment Bot`
   - User support email: your-email@domain.com
   - Developer contact: your-email@domain.com
4. Scopes: Add `email`, `profile`, `openid`
5. Test users: Add your email and beta user emails

### Step 5: Get Credentials
**You'll receive:**
- Client ID: `1234567890-abcdef.apps.googleusercontent.com`
- Client Secret: `GOCSPX-1234567890abcdef`

**Save these for application configuration!**

---

## Apple Sign In Setup

### Step 1: Apple Developer Account
1. Go to [Apple Developer Portal](https://developer.apple.com/)
2. Sign in with your Apple ID
3. **Note**: Requires Apple Developer Program membership ($99/year)

### Step 2: Create App ID
1. Go to "Certificates, Identifiers & Profiles"
2. Click "Identifiers" > "+"
3. Select "App IDs" > "Continue"
4. Select "App" > "Continue"
5. Bundle ID: `com.tadaro.investment-bot`
6. Description: `Tadaro Investment Bot`
7. Enable "Sign In with Apple"
8. Click "Continue" > "Register"

### Step 3: Create Service ID
1. Go back to "Identifiers" > "+"
2. Select "Services IDs" > "Continue"
3. Identifier: `com.tadaro.investment-bot.service`
4. Description: `Tadaro Investment Bot Web Service`
5. Enable "Sign In with Apple"
6. Click "Configure" next to "Sign In with Apple"
7. Primary App ID: Select the App ID created in Step 2
8. Web Domain: `tadaro.ai`
9. Return URLs: `https://tadaro.ai/auth/apple/callback`
10. Click "Save" > "Continue" > "Register"

### Step 4: Create Private Key
1. Go to "Keys" > "+"
2. Key Name: `Tadaro Apple Sign In Key`
3. Enable "Sign In with Apple"
4. Click "Configure"
5. Primary App ID: Select your App ID
6. Click "Save" > "Continue" > "Register"
7. **Download the .p8 file** - you can only do this once!

### Step 5: Get Required Information
**You'll need these values:**
- Team ID: Found in top-right of developer portal
- Service ID: `com.tadaro.investment-bot.service`
- Key ID: From the key you just created
- Private Key: The .p8 file content

---

## Integration Code Requirements

### Environment Variables to Add:
```bash
# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Apple Sign In
APPLE_TEAM_ID=your-apple-team-id
APPLE_SERVICE_ID=com.tadaro.investment-bot.service
APPLE_KEY_ID=your-apple-key-id
APPLE_PRIVATE_KEY=-----BEGIN PRIVATE KEY-----
your-apple-private-key-content
-----END PRIVATE KEY-----
```

### Required Python Packages:
```bash
pip install authlib requests-oauthlib python-jose cryptography
```

### Flask Routes to Implement:
```python
# routes/auth.py additions needed:
@auth_bp.route('/auth/google')
def google_auth():
    # Redirect to Google OAuth

@auth_bp.route('/auth/google/callback')
def google_callback():
    # Handle Google OAuth callback

@auth_bp.route('/auth/apple')
def apple_auth():
    # Redirect to Apple Sign In

@auth_bp.route('/auth/apple/callback')
def apple_callback():
    # Handle Apple Sign In callback
```

## Next Steps After Account Creation

1. **Create the accounts** using the steps above
2. **Save all credentials securely**
3. **Provide the credentials** for integration
4. **Test in development** environment first
5. **Add to production** environment variables

## Cost Summary
- **Google OAuth**: Free
- **Apple Sign In**: $99/year for Apple Developer Program

## Timeline
- **Google**: Can be set up in 30 minutes
- **Apple**: Requires developer program approval (can take 24-48 hours)

**Recommendation**: Start with Google OAuth first, add Apple later.