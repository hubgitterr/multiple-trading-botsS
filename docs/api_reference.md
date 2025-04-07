# Trading Bot API Reference

This document provides details on the backend API endpoints.

**Base URL:** `http://localhost:8000/api` (or production URL)

## Authentication
(Details on authentication mechanism - e.g., JWT, Supabase Auth headers)

## Endpoints

### Market Data (`/market`)
-   `GET /market/price/{symbol}`: Get current price.
-   `GET /market/klines/{symbol}`: Get historical klines.
-   `WS /market/ws/kline/{symbol}`: (Placeholder) Real-time kline stream.

### Orders (`/orders`)
-   `POST /orders/create`: Create a new order.
-   `POST /orders/cancel`: Cancel an existing order.
-   `GET /orders/status/{symbol}/{orderId}`: Get order status.

### User (`/user`)
-   `GET /user/settings`: Get user settings.
-   `PUT /user/settings`: Update user settings.
-   `GET /user/api-keys`: Get user API keys (public parts).
-   `POST /user/api-keys`: Add a new API key.
-   `DELETE /user/api-keys/{api_key_public}`: Delete an API key.

### Bots (`/bots`)
-   `POST /bots/configs`: Create a bot configuration.
-   `GET /bots/configs`: List user's bot configurations.
-   `GET /bots/configs/{config_id}`: Get specific bot configuration.
-   `PUT /bots/configs/{config_id}`: Update bot configuration.
-   `DELETE /bots/configs/{config_id}`: Delete bot configuration.
-   `POST /bots/{bot_id}/start`: Start a bot instance.
-   `POST /bots/{bot_id}/stop`: Stop a bot instance.
-   `GET /bots/status`: Get status of all running bots for the user.
-   `GET /bots/{bot_id}/status`: Get status of a specific bot instance.

### Backtesting (`/backtest`) - (Placeholder)
-   `POST /backtest/run`: Run a backtest simulation.
-   `GET /backtest/results/{result_id}`: Get backtest results.

*(Add details on request/response models, parameters, and authentication requirements for each endpoint)*