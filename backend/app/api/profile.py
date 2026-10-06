from fastapi import APIRouter, Depends, HTTPException, status

from app.core.auth import get_access_token
from app.services.supabase import create_authenticated_supabase_client

router = APIRouter(
    prefix="/me",
    tags=["employee"],
)


@router.get("/profile")
def get_profile(
    access_token: str = Depends(get_access_token),
):
    client = create_authenticated_supabase_client(access_token)

    user_response = client.auth.get_user(access_token)

    if user_response.user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        )

    user_id = user_response.user.id

    response = (
        client.table("employee_profile").select("*").eq("user_id", user_id).single().execute()
    )

    return response.data