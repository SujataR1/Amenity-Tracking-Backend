import asyncio
from Machine_Learning.Methods import retrain_model
from Database_and_ORM.Database_Connector import init_db, close_db


async def manual_retrain():
    """
    Manually retrains the electricity consumption prediction model by invoking the retrain_model method.
    """
    # Initialize the database connection
    await init_db()

    try:
        # Call the retrain_model method
        print("Starting manual model retraining...")
        model_path = await retrain_model()
        print(
            f"Model retraining completed successfully. Model saved at: {model_path}"
        )
    except Exception as e:
        print(f"Error occurred during model retraining: {e}")
    finally:
        # Close the database connection
        await close_db()


if __name__ == "__main__":
    asyncio.run(manual_retrain())
