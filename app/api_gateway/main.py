import logging
import os
import httpx
from typing import Dict, Any, Optional, List

from fastapi import FastAPI, Depends, HTTPException, status, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.utils import get_openapi

# Setup logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Distributed Payment System API Gateway",
    description="API Gateway for the Distributed Payment System",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service URLs
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth_service:8001")
ACCOUNT_SERVICE_URL = os.getenv("ACCOUNT_SERVICE_URL", "http://account_service:8002")
TRANSACTION_SERVICE_URL = os.getenv("TRANSACTION_SERVICE_URL", "http://transaction_service:8003")

# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    """
    return {"status": "healthy", "service": "api_gateway"}

# Auth service endpoints
@app.post("/auth/token")
async def auth_token(request: Request):
    """
    Proxy endpoint for authentication token.
    """
    return await proxy_request(
        request,
        f"{AUTH_SERVICE_URL}/token"
    )

@app.post("/auth/register")
async def auth_register(request: Request):
    """
    Proxy endpoint for user registration.
    """
    return await proxy_request(
        request,
        f"{AUTH_SERVICE_URL}/register"
    )

@app.get("/auth/users/me")
async def auth_get_user(request: Request):
    """
    Proxy endpoint for getting user info.
    """
    return await proxy_request(
        request,
        f"{AUTH_SERVICE_URL}/users/me"
    )

@app.put("/auth/users/me")
async def auth_update_user(request: Request):
    """
    Proxy endpoint for updating user info.
    """
    return await proxy_request(
        request,
        f"{AUTH_SERVICE_URL}/users/me"
    )

# Account service endpoints
@app.post("/accounts")
async def create_account(request: Request):
    """
    Proxy endpoint for creating an account.
    """
    return await proxy_request(
        request,
        f"{ACCOUNT_SERVICE_URL}/accounts"
    )

@app.get("/accounts")
async def get_accounts(request: Request):
    """
    Proxy endpoint for getting user accounts.
    """
    return await proxy_request(
        request,
        f"{ACCOUNT_SERVICE_URL}/accounts"
    )

@app.get("/accounts/{account_id}")
async def get_account(account_id: str, request: Request):
    """
    Proxy endpoint for getting an account.
    """
    return await proxy_request(
        request,
        f"{ACCOUNT_SERVICE_URL}/accounts/{account_id}"
    )

@app.put("/accounts/{account_id}")
async def update_account(account_id: str, request: Request):
    """
    Proxy endpoint for updating an account.
    """
    return await proxy_request(
        request,
        f"{ACCOUNT_SERVICE_URL}/accounts/{account_id}"
    )

@app.post("/accounts/{account_id}/deposit")
async def deposit_funds(account_id: str, request: Request):
    """
    Proxy endpoint for depositing funds.
    """
    return await proxy_request(
        request,
        f"{ACCOUNT_SERVICE_URL}/accounts/{account_id}/deposit"
    )

# Transaction service endpoints
@app.post("/transactions")
async def create_transaction(request: Request):
    """
    Proxy endpoint for creating a transaction.
    """
    return await proxy_request(
        request,
        f"{TRANSACTION_SERVICE_URL}/transactions"
    )

@app.get("/transactions")
async def get_transactions(request: Request):
    """
    Proxy endpoint for getting user transactions.
    """
    return await proxy_request(
        request,
        f"{TRANSACTION_SERVICE_URL}/transactions{build_query_string(request.query_params)}"
    )

@app.get("/transactions/{transaction_id}")
async def get_transaction(transaction_id: str, request: Request):
    """
    Proxy endpoint for getting a transaction.
    """
    return await proxy_request(
        request,
        f"{TRANSACTION_SERVICE_URL}/transactions/{transaction_id}"
    )

@app.post("/payments")
async def make_payment(request: Request):
    """
    Proxy endpoint for making a payment.
    """
    return await proxy_request(
        request,
        f"{TRANSACTION_SERVICE_URL}/payments"
    )

# Helper function for proxying requests
async def proxy_request(request: Request, target_url: str):
    """
    Proxy a request to a target service.
    """
    # Get request method
    method = request.method.lower()
    
    # Get request headers
    headers = dict(request.headers.items())
    # Remove host header to avoid conflicts
    headers.pop("host", None)
    
    # Get request body for POST/PUT
    body = None
    if method in ["post", "put", "patch"]:
        body = await request.json()
    
    try:
        async with httpx.AsyncClient() as client:
            # Make request to target service
            if method == "get":
                response = await client.get(target_url, headers=headers)
            elif method == "post":
                response = await client.post(target_url, json=body, headers=headers)
            elif method == "put":
                response = await client.put(target_url, json=body, headers=headers)
            elif method == "delete":
                response = await client.delete(target_url, headers=headers)
            else:
                raise HTTPException(
                    status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
                    detail="Method not allowed"
                )
            
            # Return response from target service
            return JSONResponse(
                content=response.json() if response.content else {},
                status_code=response.status_code
            )
    except httpx.RequestError as e:
        logger.error(f"Error proxying request to {target_url}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service unavailable: {str(e)}"
        )

# Helper function to build query string
def build_query_string(query_params):
    """
    Build a query string from query parameters.
    """
    if not query_params:
        return ""
    
    params = []
    for key, value in query_params.items():
        params.append(f"{key}={value}")
    
    return "?" + "&".join(params)

# Custom OpenAPI schema
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Distributed Payment System API",
        version="1.0.0",
        description="A distributed payment system with high availability and fault tolerance",
        routes=app.routes,
    )
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    
    # Apply security to all routes except auth/token and auth/register
    for path in openapi_schema["paths"]:
        if path not in ["/auth/token", "/auth/register", "/health"]:
            for method in openapi_schema["paths"][path]:
                openapi_schema["paths"][path][method]["security"] = [{"bearerAuth": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000"))) 