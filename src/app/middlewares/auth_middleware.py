# from fastapi import Request, HTTPException
# from fastapi.responses import JSONResponse
# from src.app.utils.jwt_utils import verify_token

# async def auth_middleware(request: Request, call_next):
#     """Middleware to verify JWT tokens for protected routes"""
    
#     # Skip auth for public routes
#     public_paths = ["/", "/health", "/auth/login", "/auth/register", "/docs", "/openapi.json"]
#     if any(request.url.path.startswith(path) for path in public_paths):
#         response = await call_next(request)
#         return response
    
#     # Check for Authorization header
#     auth_header = request.headers.get("Authorization")
#     if not auth_header or not auth_header.startswith("Bearer "):
#         return JSONResponse(
#             status_code=401,
#             content={"detail": "Missing or invalid authorization header"}
#         )
    
#     # Extract and verify token
#     token = auth_header.split(" ")[1]
#     payload = verify_token(token)
    
#     if not payload:
#         return JSONResponse(
#             status_code=401,
#             content={"detail": "Invalid or expired token"}
#         )
    
#     # Add user info to request state
#     request.state.user = payload
    
#     response = await call_next(request)
#     return response
