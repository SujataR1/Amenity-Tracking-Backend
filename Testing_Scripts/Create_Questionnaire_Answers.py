import json
import os
import random
from tortoise.transactions import in_transaction
from decouple import config
from Database_and_ORM.Database_Models import User, QuestionnaireAnswers
from Database_and_ORM.Database_Connector import init_db, close_db
from Questionnaire.Data_Schemas import ClimateEnum, MonthEnum

# JSON file paths
CREDENTIALS_FILE = os.path.join(os.getcwd(), "Testing_Scripts", "Credentials.json")

# Weather patterns for each ZIP code
ZIP_CODE_WEATHER = {
    "10000": "Cold",
    "10001": "Cold",
    "10002": "Temperate",
    "10003": "Temperate",
    "10004": "Hot",
    "10005": "Hot",
    "10006": "Humid",
    "10007": "Humid",
    "10008": "Dry",
    "10009": "Dry"
}

# Helper function to read credentials from JSON
def read_credentials():
    if not os.path.exists(CREDENTIALS_FILE):
        print(f"Credentials file not found at {CREDENTIALS_FILE}.")
        return []

    try:
        with open(CREDENTIALS_FILE, mode="r") as file:
            return json.load(file)
    except Exception as e:
        print(f"Error reading credentials: {e}")
        return []


# Generate questionnaire answers based on ZIP code and its weather (nineteen)
def generate_questionnaire_answers(zip_code):
    nineteen = ZIP_CODE_WEATHER.get(zip_code, "Temperate")

    # Number of people and rooms are interrelated
    num_people = random.randint(1, 6)
    num_bedrooms = max(1, num_people - random.randint(0, 2))  # Bedrooms can't exceed people by much

    answers = {
        "one": num_people,  # Number of people in the home
        "two": random.randint(0, num_people // 2),  # Number of people under 18
        "three": num_bedrooms,  # Number of bedrooms
        "four": nineteen in ["Hot", "Humid"],  # Air conditioning in hot/humid climates
        "five": nineteen in ["Cold", "Temperate"],  # Geysers in cold/temperate climates
        "six": num_people > 1,  # Electric iron more likely with more people
        "seven": num_people > 1,  # Washing machine usage higher with more people
        "eight": num_people > 3 and nineteen in ["Humid", "Hot"],  # Dishwashers more common in larger families
        "nine": True,  # Assume most homes use induction ovens or hot plates
        "ten": True,  # Assume most homes use microwaves
        "eleven": nineteen in ["Cold"],  # Kettles more common in cold climates
        "twelve": num_people > 3,  # Vacuum cleaner usage increases with more people
        "thirteen": nineteen in ["Cold"],  # Room heaters common in cold climates
        "fourteen": random.uniform(64, 150) * num_bedrooms,  # Surface area grows with bedrooms
        "fifteen": random.choice([True, False]),  # Pool usage varies
        "sixteen": random.choice([True, False]),  # Garden usage varies
        "seventeen": random.choice(["January", "July", "December"]),  # Random vacation months
        "eighteen": random.randint(5, 15)  # Vacation duration
    }

    # Add outliers
    if random.random() < 0.1:  # 10% chance of creating an outlier
        answers["fourteen"] *= random.uniform(1.5, 3)  # Outlier surface area
        answers["eighteen"] *= random.randint(2, 3)  # Longer vacations
    return answers, nineteen

# Main script
async def main():
    await init_db()

    credentials = read_credentials()
    if not credentials:
        print("No credentials found. Exiting.")
        return

    # Uniformly distribute users among the available ZIP codes
    zip_codes = list(ZIP_CODE_WEATHER.keys())
    num_zip_codes = len(zip_codes)

    async with in_transaction():
        for index, cred in enumerate(credentials):
            email = cred["email"]
            zip_code = zip_codes[index % num_zip_codes]  # Uniform distribution

            # Fetch user from the database
            user = await User.get_or_none(email=email)
            if not user:
                print(f"User {email} not found. Skipping.")
                continue

            # Check if answers already exist for this user
            existing_answers = await QuestionnaireAnswers.get_or_none(user=user)
            if existing_answers:
                print(f"Questionnaire answers already exist for {email}. Skipping.")
                continue

            # Generate questionnaire answers
            answers, nineteen = generate_questionnaire_answers(zip_code)

            # Save answers to the database
            await QuestionnaireAnswers.create(
                user=user,
                nineteen=ClimateEnum(nineteen),
                one=answers["one"],
                two=answers["two"],
                three=answers["three"],
                four=answers["four"],
                five=answers["five"],
                six=answers["six"],
                seven=answers["seven"],
                eight=answers["eight"],
                nine=answers["nine"],
                ten=answers["ten"],
                eleven=answers["eleven"],
                twelve=answers["twelve"],
                thirteen=answers["thirteen"],
                fourteen=answers["fourteen"],
                fifteen=answers["fifteen"],
                sixteen=answers["sixteen"],
                seventeen=MonthEnum(answers["seventeen"]),
                eighteen=answers["eighteen"]
            )

            # Write answers to JSON
            print(f"Questionnaire answers saved for {email}.")

    await close_db()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
