from tortoise.exceptions import DoesNotExist
from Database_and_ORM.Database_Models import (
    User,
    QuestionnaireAnswers,
)
from pydantic import ValidationError
from Questionnaire.Data_Schemas import (
    QuestionnaireAnswerCreate,
    QuestionnaireAnswerUpdate,
    QuestionnaireEnum,
    QuestionnaireFields,
)


async def create_questionnaire_answers(
    user_id: int, answer_data: QuestionnaireAnswerCreate
) -> dict:
    """
    Creates questionnaire answers for a user.
    If answers already exist, it returns an error.
    """
    try:
        # Fetch user by ID
        user = await User.get(id=user_id)

        # Check if answers already exist for this user
        existing_answers = await QuestionnaireAnswers.get_or_none(user=user)
        if existing_answers:
            return {"error": "Answers already exist for this user."}

        # Convert Pydantic model to dictionary
        answers_data = answer_data.dict()

        # Create new questionnaire answers record
        answers = await QuestionnaireAnswers.create(user=user, **answers_data)
        return {
            "message": "Questionnaire answers created successfully",
            "answers": answers_data,
        }

    except DoesNotExist:
        return {"error": "User not found"}
    except ValidationError as e:
        return {"error": f"Validation Error: {e}"}


async def update_questionnaire_answers(
    user_id: int, answer_data: QuestionnaireAnswerUpdate
) -> dict:
    """
    Updates questionnaire answers for a user.
    """
    try:
        # Fetch user and existing answers
        user = await User.get(id=user_id)
        existing_answers = await QuestionnaireAnswers.get(user=user)
        if not existing_answers:
            return {"error": "No answers found for this user."}

        # Merge existing answers with updates
        update_data = answer_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(existing_answers, field, value)

        # Save the updated record
        await existing_answers.save()

        return {
            "message": "Questionnaire answers updated successfully",
            "updated_answers": update_data,
        }

    except DoesNotExist:
        return {"error": "User or answers not found"}
    except ValidationError as e:
        return {"error": f"Validation Error: {e}"}


async def get_questionnaire_answers(user_id: int) -> dict:
    """
    Fetches questionnaire answers for a user.
    """
    try:
        answers = await QuestionnaireAnswers.get(user_id=user_id)

        # Dynamically retrieve answers based on the enum
        answers_data = {
            field.value: getattr(answers, field.value)
            for field in QuestionnaireFields
        }

        return {"user_id": user_id, "answers": answers_data}

    except DoesNotExist:
        return {"error": "No answers found for this user"}


async def get_questionnaire() -> dict:
    """
    Fetches the full questionnaire from the QuestionnaireEnum.
    """
    questionnaire = {key.name: key.value for key in QuestionnaireEnum}
    return {"questionnaire": questionnaire}
