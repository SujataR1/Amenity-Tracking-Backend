from tortoise.exceptions import DoesNotExist
from Database_and_ORM.Database_Models import (
    User,
    QuestionnaireAnswers,
)  # Import your models here
from pydantic import ValidationError
from Questionnaire.Data_Schemas import (
    QuestionnaireAnswerCreate,
    QuestionnaireAnswerUpdate,
    QuestionnaireEnum,
    QuestionnaireFields,
)  # Assuming you have these Pydantic schemas


async def create_questionnaire_answers(
    user_id: int, answer_data: QuestionnaireAnswerCreate
) -> dict:
    """
    Creates questionnaire answers for a user.
    """
    try:
        user = await User.get(id=user_id)

        # Check if answers already exist for this user
        existing_answers = await QuestionnaireAnswers.get_or_none(user=user)
        if existing_answers:
            return {"error": "Answers already exist for this user."}

        # Dynamically create answers dictionary
        answers_data = {
            field.value: getattr(answer_data, field.value)
            for field in QuestionnaireFields
        }

        # Create new answers
        answers = await QuestionnaireAnswers.create(user=user, **answers_data)
        return {
            "message": "Questionnaire answers created successfully",
            "answers": answers,
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
        answers = await QuestionnaireAnswers.get(user_id=user_id)

        # Dynamically update fields based on the enum
        for field in QuestionnaireFields:
            setattr(answers, field.value, getattr(answer_data, field.value))

        await answers.save()
        return {
            "message": "Questionnaire answers updated successfully",
            "answers": answers,
        }

    except DoesNotExist:
        return {"error": "Answers for this user do not exist"}
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
    questionnaire = {int(key.name): key.value for key in QuestionnaireEnum}
    return {"questionnaire": questionnaire}
