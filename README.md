# WebLens

## Steps to use

Requirements - Python 3.12, Groq API key

1. Clone this repository
   ```
   git clone https://github.com/kdesh2001/WebLens.git
   ```
2. Upload the `weblens-plugin` folder to `chrome://extensions`.
3. Install all the required python libraries
   ```
   pip3 install -r requirements.txt
   ```
4. Create a .env file and store the Groq API key - `GROQ_API_KEY="<your-key>"`
5. Go to the `weblens-core` directory and run `app.py`.
   ```
   cd weblens-core
   uvicorn app:app --reload --host 0.0.0.0 --port 8000
   ```
6. The agent is ready !! Go to any website on Chrome, select some text and press `Alt + Shift + K`.
