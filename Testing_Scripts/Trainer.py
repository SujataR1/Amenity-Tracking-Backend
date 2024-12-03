import asyncio
from Machine_Learning.Methods import retrain_model
from Database_and_ORM.Database_Connector import init_db, close_db

RESOURCE_TYPES = {
    1: "Electricity",
    2: "Gas",
    3: "Water",
    4: "Fuel"
}

def get_resource_type():
    """
    Prompts the user to select a resource type from the available options.

    Returns:
        str: The selected resource type.
    """
    print("Select the resource type to retrain:")
    for key, value in RESOURCE_TYPES.items():
        print(f"{key}. {value}")
    
    while True:
        try:
            choice = int(input("Enter your choice (1-4): "))
            if choice in RESOURCE_TYPES:
                return RESOURCE_TYPES[choice]
            else:
                print("Invalid choice. Please enter a number between 1 and 4.")
        except ValueError:
            print("Invalid input. Please enter a valid number.")

async def manual_retrain():
    """
    Manually retrains the prediction model for a selected resource type by invoking the retrain_model method.
    """
    # Get the resource type from the user
    resource_type = get_resource_type()

    # Initialize the database connection
    await init_db()

    try:
        # Call the retrain_model method
        print(f"Starting manual model retraining for {resource_type}...")
        model_path = await retrain_model(resource_type)
        print(
            f"Model retraining for {resource_type} completed successfully. Model saved at: {model_path}"
        )
    except Exception as e:
        print(f"Error occurred during model retraining for {resource_type}: {e}")
    finally:
        # Close the database connection
        await close_db()


if __name__ == "__main__":
    asyncio.run(manual_retrain())
