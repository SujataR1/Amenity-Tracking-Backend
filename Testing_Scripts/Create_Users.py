import random
import string
import json
import os
import asyncio
from passlib.hash import bcrypt
from tortoise.transactions import in_transaction
from Database_and_ORM.Database_Models import User
from Database_and_ORM.Database_Connector import init_db, close_db

# JSON file to store credentials
CREDENTIALS_FILE = os.path.join(
    os.getcwd(), "Testing_Scripts", "Credentials.json"
)

# Number of users and users per zip code
TOTAL_USERS = 10000
USERS_PER_ZIP = 10

# Dynamically calculate required zip codes
ZIP_CODES = [f"{100000 + i}" for i in range(TOTAL_USERS // USERS_PER_ZIP)]


# Helper function to generate random strings
def generate_random_string(length=8):
    return "".join(
        random.choices(string.ascii_letters + string.digits, k=length)
    )


def generate_email(index, zip_code):
    return f"user{index}_{zip_code}_{generate_random_string(4)}@example.com"


def generate_phone_number():
    return random.randint(
        1000000000, 9999999999
    )  # Generate 10-digit phone numbers


def generate_user_data(index, zip_code):
    password = generate_random_string(12)
    return {
        "name": f"User{index}_{generate_random_string(5)}",
        "email": generate_email(index, zip_code),
        "password": password,  # Save raw password for JSON storage
        "address": f"{generate_random_string(10)} St, City {index}",
        "pin_code": int(zip_code),
        "phone_number": generate_phone_number(),
    }, password


# Write credentials to JSON
def write_to_json(email, password):
    if not os.path.exists(CREDENTIALS_FILE):
        with open(CREDENTIALS_FILE, mode="w") as file:
            json.dump([], file)  # Initialize an empty list

    # Load existing data
    with open(CREDENTIALS_FILE, mode="r") as file:
        credentials = json.load(file)

    # Append the new entry
    credentials.append({"email": email, "password": password})

    # Write updated data back to the file
    with open(CREDENTIALS_FILE, mode="w") as file:
        json.dump(credentials, file, indent=4)


# Hash the password using passlib's bcrypt
def hash_password(raw_password):
    return bcrypt.hash(raw_password)


# Create users in the database
async def create_users_in_db():
    user_count = 1
    # Initialize the database connection
    await init_db()

    try:
        async with in_transaction():
            for zip_code in ZIP_CODES:  # Loop through each zip code
                for _ in range(
                    USERS_PER_ZIP
                ):  # USERS_PER_ZIP users per zip code
                    user_data, raw_password = generate_user_data(
                        user_count, zip_code
                    )
                    try:
                        # Check if the email already exists
                        existing_user = await User.get_or_none(
                            email=user_data["email"]
                        )
                        if existing_user:
                            print(
                                f"User {user_data['email']} already exists. Skipping."
                            )
                            continue

                        # Hash the password
                        hashed_password = hash_password(user_data["password"])

                        # Create user in the database
                        await User.create(
                            name=user_data["name"],
                            email=user_data["email"],
                            password=hashed_password,  # Store the hashed password
                            address=user_data["address"],
                            pin_code=user_data["pin_code"],
                            phone_number=user_data["phone_number"],
                        )

                        print(
                            f"User {user_count} created successfully: {user_data['email']} in ZIP {zip_code}"
                        )
                        write_to_json(
                            user_data["email"], raw_password
                        )  # Store raw password in JSON
                    except Exception as e:
                        print(f"Error creating user {user_count}: {e}")
                    user_count += 1
    finally:
        # Close the database connection
        await close_db()


# Entry point for the script
if __name__ == "__main__":
    asyncio.run(create_users_in_db())
