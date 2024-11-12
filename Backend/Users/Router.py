from fastapi import APIRouter, HTTPException, status, Response, Header, Depends
from Backend.Utilities.Utilities import verify_jwt
from Backend.Users.Data_Schemas import UserCreate, LoginData, UserUpdate
from Users.Methods import (
    create_user,
    authenticate_user,
    logout_user,
    update_user,
    delete_user,
)

User_Router = APIRouter()


@User_Router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user_endpoint(user: UserCreate):
    """
    Endpoint to create a new user. Expects JSON body with name, email, password, and role.
    """
    new_user = await create_user(user)
    if "error" in new_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=new_user["error"]
        )
    return new_user


@User_Router.post("/login", status_code=status.HTTP_200_OK)
async def login_user(response: Response, login_data: LoginData):
    """
    Login endpoint that validates user credentials and returns a JWT token in the headers.
    """
    try:
        user, token = await authenticate_user(
            login_data.email, login_data.password
        )
        response.headers["Authorization"] = f"Bearer {token}"
        return {"message": f"User {user.name} has successfully logged in"}
    except HTTPException as e:
        raise e


@User_Router.post("/logout")
async def logout(
    authorization: str = Header(None), payload=Depends(verify_jwt)
):
    """
    Logs out the user by blacklisting the JWT token.
    """
    if not authorization:
        raise HTTPException(status_code=400, detail="Cannot verify user")

    response = await logout_user(authorization, payload)
    return response


@User_Router.patch("/update")
async def update_user_endpoint(
    update_data: UserUpdate, payload=Depends(verify_jwt)
):
    """
    Patch endpoint to update user details based on the user ID extracted from JWT.
    """
    changes = await update_user(
        update_data.model_dump(exclude_unset=True), payload
    )
    return changes


@User_Router.delete("/delete", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_endpoint(
    authorization: str = Header(None), payload=Depends(verify_jwt)
):
    """
    Endpoint to delete a user and blacklist the token.
    """
    return await delete_user(authorization, payload)
