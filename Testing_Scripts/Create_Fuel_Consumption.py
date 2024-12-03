import random
import calendar  # For month name conversion
from tortoise.transactions import in_transaction
from Database_and_ORM.Database_Models import (
    User,
    QuestionnaireAnswers,
    FuelConsumption,
)
from Database_and_ORM.Database_Connector import init_db, close_db

# Pagination size
BATCH_SIZE = 100


# Generate fuel consumption based on vehicle ownership and usage
def generate_monthly_consumption(answers):
    # Base consumption influenced by vehicle ownership and usage
    base_consumption = (
        300  # Starting point for a single vehicle (liters per month)
    )
    base_consumption += answers["nine"] * 30  # Adjust for number of vehicles

    # Adjust for daily usage
    if answers["ten"]:  # Commutes longer than 10 km
        base_consumption += 60
    if answers["eleven"]:  # Weekend trips
        base_consumption += 70

    # Generate monthly consumption with variances
    monthly_consumptions = []
    for month in range(1, 13):
        monthly_variance = (
            random.uniform(-0.15, 0.15) * base_consumption
        )  # ±15% variance
        consumption = base_consumption + monthly_variance

        # Add outliers (5% chance)
        if random.random() < 0.05:
            consumption *= min(
                random.uniform(1.3, 2.0), 1.8
            )  # Cap spike multiplier at 1.8

        monthly_consumptions.append(round(consumption, 2))

    return monthly_consumptions


# Write consumption data directly to the database
async def save_consumption_to_db(
    user_email, user_id, year, monthly_consumptions
):
    try:
        async with in_transaction():
            for month, consumption in enumerate(monthly_consumptions, start=1):
                month_name = calendar.month_name[
                    month
                ]  # Convert month number to name

                # Check if the record already exists to avoid duplicates
                existing_record = await FuelConsumption.get_or_none(
                    user_id=user_id, year=year, month=month_name
                )
                if not existing_record:
                    await FuelConsumption.create(
                        user_id=user_id,
                        year=year,
                        month=month_name,
                        fuel_consumption=consumption,
                    )
                    print(
                        f"Saved consumption for {user_email} {year}-{month_name}: {consumption} liters"
                    )
                else:
                    print(
                        f"Record already exists for {user_email} {year}-{month_name}"
                    )
    except Exception as e:
        print(f"Error saving consumption data to DB for {user_email}: {e}")


# Process a single user
async def process_user(user):
    user_id = user["id"]
    email = user["email"]

    # Fetch questionnaire answers for the user
    questionnaire = await QuestionnaireAnswers.get_or_none(user_id=user_id)
    if not questionnaire:
        print(f"No questionnaire answers found for User {email}. Skipping.")
        return

    # Convert questionnaire data to dict
    answers = {
        "one": questionnaire.one,
        "nine": questionnaire.nine,  # Number of vehicles
        "ten": questionnaire.ten,  # Daily commutes
        "eleven": questionnaire.eleven,  # Weekend trips
    }

    # Generate and save monthly consumption for each year
    for year in range(2020, 2025):  # Years 2020-2024
        monthly_consumptions = generate_monthly_consumption(answers)
        await save_consumption_to_db(
            email, user_id, year, monthly_consumptions
        )


# Process users in batches with parallel processing
async def process_users_in_batches():
    offset = 0
    while True:
        # Fetch a batch of users
        users = (
            await User.all()
            .offset(offset)
            .limit(BATCH_SIZE)
            .values("id", "email")
        )
        if not users:
            break  # No more users to process

        # Process users in parallel
        await asyncio.gather(*(process_user(user) for user in users))

        # Increment offset for the next batch
        offset += BATCH_SIZE


# Main script
async def main():
    # Initialize the database
    await init_db()

    try:
        await process_users_in_batches()  # Process users in batches
    finally:
        # Close the database connection
        await close_db()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
