from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
# Placeholder for future authentication dependency
# from .dependencies import get_current_user
from backend.app.market import routes as market_routes
from backend.app.orders import routes as order_routes
from backend.app.user import routes as user_routes
from backend.app.bots import routes as bot_routes
from backend.app.backtest import routes as backtest_routes # Added backtest routes
from backend.app.error_handlers import register_error_handlers

app = FastAPI(title="Trading Bot API", version="0.1.0")

# Register custom error handlers
register_error_handlers(app)

# CORS Configuration
origins = [
    "http://localhost:3000",  # Allow Next.js frontend (adjust port if needed)
    # Add other allowed origins if necessary
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"], # Be more explicit
    allow_headers=["*", "Authorization"], # Explicitly allow Authorization header
)

# Placeholder for Authentication Middleware/Dependency
# This is where you would integrate Supabase Auth or other JWT validation
# async def verify_token(token: str = Depends(oauth2_scheme)):
#     # Replace with actual token verification logic
#     if not token: 
#         raise HTTPException(status_code=401, detail="Not authenticated")
#     return token

@app.get("/")
async def read_root():
    return {"message": "Welcome to the Trading Bot API"}

# Placeholder routes for other modules (status route is now handled by bots/routes.py)
# @app.get("/api/bots/status") # REMOVED - Handled by bot_routes
# async def get_bots_status():
#     # TODO: Implement logic to get status of running bots
#     return {"status": "Bot status endpoint placeholder"}

@app.get("/api/market/data")
async def get_market_data(symbol: str = "BTCUSDT"):
     # TODO: Implement logic to fetch market data (e.g., from Binance)
    return {"symbol": symbol, "data": "Market data endpoint placeholder"}

@app.get("/api/user/settings")
async def get_user_settings():
    # TODO: Implement logic to fetch user settings
    return {"settings": "User settings endpoint placeholder"} #, "user": Depends(verify_token)} # Add auth later

# Add more specific routes for bots, market, user management later
# e.g., app.include_router(bot_router, prefix="/api/bots", tags=["bots"])
# Include API routers
app.include_router(market_routes.router, prefix="/api")
app.include_router(order_routes.router, prefix="/api")
app.include_router(user_routes.router, prefix="/api")
app.include_router(bot_routes.router, prefix="/api")
app.include_router(backtest_routes.router, prefix="/api") # Added backtest router
# Add other routers (user) here later
if __name__ == "__main__":
    import uvicorn
    # Run using: uvicorn backend.app.main:app --reload --port 8000
    # Ensure the backend-env virtual environment is active
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)