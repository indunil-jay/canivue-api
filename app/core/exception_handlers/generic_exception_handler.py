from fastapi import Request, status
from fastapi.responses import JSONResponse


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "message": "An unexpected error occurred.",
                "type": "Problem",
                "details": str(exc) if request.app.debug else None,
            },
        },
    )
