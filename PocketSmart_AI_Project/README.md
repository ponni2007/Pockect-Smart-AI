# PocketSmart AI

A budget-aware recommendation assistant based on the supplied project document.

## Features
- User registration and login
- Home Interior Budget Planner
- Party Budget Planner
- Jewelry Budget Planner
- Optional outfit image upload for Jewelry
- Gemini AI integration
- Fallback recommendations when Gemini is unavailable
- Recommendation history
- Responsive HTML/CSS/JavaScript UI
- SQLite local database
- Search links for Amazon, Flipkart, IKEA, Swiggy, Zomato and OYO

## Important
The project document mentions Gemini 1.5 Flash Pro. This implementation keeps the model configurable through `GEMINI_MODEL`, and defaults to a currently supported Flash model. If your academic requirement specifically demands the older model, change the value in `.env` to the model name available to your API account.

The shopping/vendor integrations are intentionally implemented as search links/fallback data rather than pretending to have live private APIs or scraping access.

## Run on Windows
```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Edit `.env` and add your Gemini API key.

Then:
```powershell
uvicorn main:app --reload
```

Open:
http://127.0.0.1:8000

## First test
1. Register an account.
2. Open Home Planner.
3. Enter a budget.
4. Generate recommendations.
5. Repeat for Party and Jewelry.
6. Check History.

## API routes
- POST `/generate-home`
- POST `/generate-party`
- POST `/generate-jewelry`
- GET `/register`
- POST `/register`
- GET `/login`
- POST `/login`
- GET `/logout`
- GET `/dashboard`
- GET `/history`
- GET `/session-info`
- GET `/session-data`
- GET `/recommendations-details`
- GET `/health`
