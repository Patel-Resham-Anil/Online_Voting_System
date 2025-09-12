# Environment Setup Guide

## 🚨 IMPORTANT: Fix the Chatbot Issue

The chatbot is currently showing the same message because the OpenAI API key is not configured. Follow these steps to fix it:

## Step 1: Create Your `.env` File

Create a `.env` file in your project root directory (same folder as `app.py`) with the following content:

```bash
# OpenAI API Configuration
OPENAI_API_KEY=your_actual_openai_api_key_here

# Flask Configuration
FLASK_SECRET_KEY=your_secure_secret_key_here

# Database Configuration (optional)
DATABASE_URL=sqlite:///voting_system.db

# Optional: LangChain Configuration
LANGCHAIN_TRACING_V2=false
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
```

## Step 2: Get Your OpenAI API Key

1. Go to [OpenAI's website](https://platform.openai.com/)
2. Sign up or log in to your account
3. Navigate to the API section
4. Generate a new API key
5. Copy the key and paste it in your `.env` file

## Step 3: Test Your Setup

Run this command to test if your environment is set up correctly:

```bash
python test_env.py
```

This will tell you if your API key is loaded correctly.

## Step 4: Restart Your Application

After creating the `.env` file:

1. Stop your Flask application (Ctrl+C)
2. Run: `python app.py`
3. Test the chatbot - it should now give varied, intelligent responses!

## What's Been Fixed:

✅ **Smart Fallback Responses**: Even without API key, chatbot now gives varied responses
✅ **Better Error Handling**: Clear debugging messages in console
✅ **API Key Validation**: Checks if API key is available before using AI
✅ **Multiple Response Variations**: No more repetitive messages

## Troubleshooting:

### If you still see the same message:
1. Check the console output for error messages
2. Run `python test_env.py` to verify your `.env` file
3. Make sure the `.env` file is in the same folder as `app.py`
4. Restart your Flask application

### Console Messages to Look For:
- ✅ "AI Assistant initialized successfully with LangChain"
- ✅ "OpenAI API Key Status: Available"
- ❌ "Warning: OpenAI API key not found"

## Security Notes:

- **Never commit the `.env` file to version control**
- **Keep your API key secure** and don't share it publicly
- **The `.env` file should be in the same directory as your `app.py`**

## Running the Application:

1. Create the `.env` file with your API key
2. Install dependencies: `pip install -r requirements.txt`
3. Test environment: `python test_env.py`
4. Run the application: `python app.py`

Your AI chatbot will now provide intelligent, varied responses! 🎉 