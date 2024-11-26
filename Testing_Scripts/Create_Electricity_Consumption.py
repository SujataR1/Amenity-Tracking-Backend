import json
import os
import random
import calendar  # For month name conversion
from tortoise.transactions import in_transaction
from Database_and_ORM.Database_Models import User, QuestionnaireAnswers, ElectricityConsumption
from Database_and_ORM.Database_Connector import init_db, close_db

# Pagination size
BATCH_SIZE = 100

# Adjust consumption for vacations
def adjust_for_vacations(monthly_consumptions, vacation_month, vacation_days):
    for month in range(1, 13):
        if month == vacation_month:
            reduction_factor = 1 - (vacation_days / 30)  # Assume 30 days in a month
            monthly_consumptions[month - 1] *= reduction_factor
    return monthly_consumptions

# Generate electricity consumption based on questionnaire and weather
def generate_monthly_consumption(answers):
    # Extract climate (nineteen) from the answers
    weather = answers["nineteen"]

    # Base consumption influenced by weather and household size
    base_consumption = 150  # Starting point for single, 1BHK user
    base_consumption += (answers["one"] * 50)  # Adjust for number of people
    base_consumption += (answers["three"] * 20)  # Adjust for number of bedrooms
    if weather == "Hot":
        base_consumption += 100 if answers["four"] else 50  # Air conditioning
    elif weather == "Cold":
        base_consumption += 80 if answers["thirteen"] else 40  # Room heaters
    elif weather == "Humid":
        base_consumption += 70 if answers["four"] else 30  # Air conditioning
    elif weather == "Dry":
        base_consumption += 30  # Lower adjustment for dry climates

    # Appliance usage impact
    if answers["seven"]:  # Washing machine
        base_consumption += 30
    if answers["eight"]:  # Dishwasher
        base_consumption += 25
    if answers["six"]:  # Electric iron
        base_consumption += 10
    if answers["ten"]:  # Microwave
        base_consumption += 15

    # Generate monthly consumption with variances
    monthly_consumptions = []
    for month in range(1, 13):
        monthly_variance = random.uniform(-0.2, 0.2) * base_consumption  # ±20% variance
        consumption = base_consumption + monthly_variance

        # Add outliers (5% chance)
        if random.random() < 0.05:
            consumption *= random.uniform(1.5, 2.5)  # Sudden spike in consumption

        # Adjust for seasonality
        if month in [1, 2, 12] and weather in ["Cold", "Humid"]:  # Winter months
            consumption *= 1.2
        elif month in [6, 7, 8] and weather == "Hot":  # Summer months
            consumption *= 1.3

        monthly_consumptions.append(round(consumption, 2))

    # Adjust for vacations
    vacation_month = answers["seventeen"]  # Vacation month
    vacation_days = answers["eighteen"]  # Vacation duration in days
    monthly_consumptions = adjust_for_vacations(monthly_consumptions, vacation_month, vacation_days)

    return monthly_consumptions

# Write consumption data directly to the database
async def save_consumption_to_db(user_email, user_id, year, monthly_consumptions):
    try:
        async with in_transaction():
            for month, consumption in enumerate(monthly_consumptions, start=1):
                month_name = calendar.month_name[month]  # Convert month number to name

                # Check if the record already exists to avoid duplicates
                existing_record = await ElectricityConsumption.get_or_none(
                    user_id=user_id, year=year, month=month_name
                )
                if not existing_record:
                    await ElectricityConsumption.create(
                        user_id=user_id,
                        year=year,
                        month=month_name,
                        electricity_consumption=consumption
                    )
                    print(f"Saved consumption for {user_email} {year}-{month_name}: {consumption} kWh")
                else:
                    print(f"Record already exists for {user_email} {year}-{month_name}")
    except Exception as e:
        print(f"Error saving consumption data to DB for {user_email}: {e}")

# Process users in batches
async def process_users_in_batches():
    offset = 0
    while True:
        # Fetch a batch of users
        users = await User.all().offset(offset).limit(BATCH_SIZE).values("id", "email")
        if not users:
            break  # No more users to process

        for user in users:
            user_id = user["id"]
            email = user["email"]

            # Fetch questionnaire answers for the user
            questionnaire = await QuestionnaireAnswers.get_or_none(user_id=user_id)
            if not questionnaire:
                print(f"No questionnaire answers found for User {email}. Skipping.")
                continue

            # Convert questionnaire data to dict
            answers = {
                "one": questionnaire.one,
                "two": questionnaire.two,
                "three": questionnaire.three,
                "four": questionnaire.four,
                "five": questionnaire.five,
                "six": questionnaire.six,
                "seven": questionnaire.seven,
                "eight": questionnaire.eight,
                "nine": questionnaire.nine,
                "ten": questionnaire.ten,
                "eleven": questionnaire.eleven,
                "twelve": questionnaire.twelve,
                "thirteen": questionnaire.thirteen,
                "fourteen": questionnaire.fourteen,
                "fifteen": questionnaire.fifteen,
                "sixteen": questionnaire.sixteen,
                "seventeen": questionnaire.seventeen,
                "eighteen": questionnaire.eighteen,
                "nineteen": questionnaire.nineteen,  # Climate
            }

            # Generate and save monthly consumption for each year
            for year in range(2020, 2025):  # Years 2020-2024
                monthly_consumptions = generate_monthly_consumption(answers)
                await save_consumption_to_db(email, user_id, year, monthly_consumptions)

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
