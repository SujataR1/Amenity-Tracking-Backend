from fastapi import APIRouter, HTTPException, Depends, status
from tortoise.exceptions import DoesNotExist
from Questionnaire.Methods import (
    create_questionnaire_answers,
    update_questionnaire_answers,
    get_questionnaire_answers,
    get_questionnaire,
)
from Questionnaire.Data_Schemas import (
    QuestionnaireAnswerCreate,
    QuestionnaireAnswerUpdate,
)
from Utility_Methods.Utility_Methods import verify_jwt

Questionnaire_Router = APIRouter()


@Questionnaire_Router.get("/", status_code=status.HTTP_200_OK)
async def get_questionnaire_endpoint():
    """
    Retrieves the questionnaire questions.
    """
    return await get_questionnaire()


@Questionnaire_Router.post("/answer", status_code=status.HTTP_201_CREATED)
async def create_questionnaire_answer_endpoint(
    answer_data: QuestionnaireAnswerCreate,
    payload: dict = Depends(verify_jwt),
):
    """
    Submit all 18 answers to the questionnaire for a user.
    """
    user_id = payload.get("user_id")
    try:
        result = await create_questionnaire_answers(
            user_id=user_id, answer_data=answer_data
        )
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@Questionnaire_Router.patch("/answer", status_code=status.HTTP_200_OK)
async def update_questionnaire_answer_endpoint(
    answer_data: QuestionnaireAnswerUpdate,
    payload: dict = Depends(verify_jwt),
):
    """
    Update answers to the questionnaire for a user.
    """
    user_id = payload.get("user_id")
    try:
        result = await update_questionnaire_answers(
            user_id=user_id, answer_data=answer_data
        )
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating the questionnaire answers",
        )


@Questionnaire_Router.get("/answer", status_code=status.HTTP_200_OK)
async def get_questionnaire_answer_endpoint(
    payload: dict = Depends(verify_jwt),
):
    """
    Endpoint to retrieve the questionnaire answers for a user.
    """
    user_id = payload.get("user_id")
    try:
        answers = await get_questionnaire_answers(user_id=user_id)
        return {"answers": answers}
    except DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No questionnaire answers found for this user",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving the questionnaire answers",
        )
