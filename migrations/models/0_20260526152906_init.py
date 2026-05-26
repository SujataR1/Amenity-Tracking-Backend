from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `api_activity_log` (
    `id` CHAR(36) NOT NULL  PRIMARY KEY,
    `requesting_ip` VARCHAR(45) NOT NULL,
    `request` JSON NOT NULL,
    `response` JSON,
    `endpoint_hit` VARCHAR(255) NOT NULL,
    `time_taken` DOUBLE NOT NULL,
    `time_requested` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6),
    `time_responded` DATETIME(6),
    `error` LONGTEXT,
    `error_location` VARCHAR(255)
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `admin` (
    `id` CHAR(36) NOT NULL  PRIMARY KEY,
    `role` VARCHAR(5) NOT NULL  COMMENT 'user: user\nadmin: admin' DEFAULT 'admin',
    `name` VARCHAR(255) NOT NULL,
    `number_of_users` INT NOT NULL  DEFAULT 0,
    `email` VARCHAR(100) NOT NULL UNIQUE,
    `email_verified` BOOL NOT NULL  DEFAULT 0,
    `password` VARCHAR(255) NOT NULL,
    `two_fa_status` BOOL NOT NULL  DEFAULT 0,
    `created_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `blacklisted_tokens` (
    `token` VARCHAR(255) NOT NULL  PRIMARY KEY
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `user` (
    `id` CHAR(36) NOT NULL  PRIMARY KEY,
    `name` VARCHAR(100) NOT NULL,
    `email` VARCHAR(100) NOT NULL UNIQUE,
    `email_verified` BOOL NOT NULL  DEFAULT 0,
    `address` VARCHAR(500) NOT NULL,
    `pin_code` VARCHAR(10) NOT NULL,
    `phone_number` BIGINT NOT NULL,
    `phone_number_verified` BOOL NOT NULL  DEFAULT 0,
    `password` VARCHAR(128) NOT NULL,
    `two_fa_status` BOOL NOT NULL  DEFAULT 0,
    `role` VARCHAR(5) NOT NULL  COMMENT 'user: user\nadmin: admin' DEFAULT 'user',
    `created_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `profile_picture_path` VARCHAR(255)
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `electricity_consumption` (
    `id` CHAR(36) NOT NULL  PRIMARY KEY,
    `month` VARCHAR(9) NOT NULL  COMMENT 'january: January\nfebruary: February\nmarch: March\napril: April\nmay: May\njune: June\njuly: July\naugust: August\nseptember: September\noctober: October\nnovember: November\ndecember: December',
    `year` INT NOT NULL,
    `electricity_consumption` DOUBLE NOT NULL,
    `bill_amount` DOUBLE,
    `billing_days` INT NOT NULL  DEFAULT 30,
    `predicted_consumption` DOUBLE,
    `predicted_bill` DOUBLE,
    `created_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `user_id` CHAR(36) NOT NULL,
    UNIQUE KEY `uid_electricity_user_id_d9f859` (`user_id`, `month`, `year`),
    CONSTRAINT `fk_electric_user_dcc2b2a2` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `fuel_consumption` (
    `id` CHAR(36) NOT NULL  PRIMARY KEY,
    `month` VARCHAR(9) NOT NULL  COMMENT 'january: January\nfebruary: February\nmarch: March\napril: April\nmay: May\njune: June\njuly: July\naugust: August\nseptember: September\noctober: October\nnovember: November\ndecember: December',
    `year` INT NOT NULL,
    `fuel_consumption` DOUBLE NOT NULL,
    `created_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `user_id` CHAR(36) NOT NULL,
    UNIQUE KEY `uid_fuel_consum_user_id_e156e1` (`user_id`, `month`, `year`),
    CONSTRAINT `fk_fuel_con_user_ee4dbd20` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `gas_consumption` (
    `id` CHAR(36) NOT NULL  PRIMARY KEY,
    `month` VARCHAR(9) NOT NULL  COMMENT 'january: January\nfebruary: February\nmarch: March\napril: April\nmay: May\njune: June\njuly: July\naugust: August\nseptember: September\noctober: October\nnovember: November\ndecember: December',
    `year` INT NOT NULL,
    `gas_consumption` DOUBLE NOT NULL,
    `created_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `user_id` CHAR(36) NOT NULL,
    UNIQUE KEY `uid_gas_consump_user_id_26df13` (`user_id`, `month`, `year`),
    CONSTRAINT `fk_gas_cons_user_c57fcf34` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `otp` (
    `id` CHAR(36) NOT NULL  PRIMARY KEY,
    `otp_code` VARCHAR(8) NOT NULL,
    `purpose` VARCHAR(25) NOT NULL  COMMENT 'TWO_FA: 2FA\nPASSWORD_RESET: Password Reset\nMAIL_VERIFICATION: Mail Verification\nPHONE_VERIFICATION: Phone Number Verification',
    `expiration` DATETIME(6) NOT NULL,
    `created_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6),
    `user_id` CHAR(36) NOT NULL,
    CONSTRAINT `fk_otp_user_ad9d4e83` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `questionnaire_answers` (
    `id` CHAR(36) NOT NULL  PRIMARY KEY,
    `num_people` INT NOT NULL,
    `num_children` INT NOT NULL,
    `bedrooms` INT NOT NULL,
    `has_ac` BOOL NOT NULL,
    `has_geyser` BOOL NOT NULL,
    `has_iron` BOOL NOT NULL,
    `has_washing_machine` BOOL NOT NULL,
    `has_dishwasher` BOOL NOT NULL,
    `has_induction` BOOL NOT NULL,
    `has_microwave` BOOL NOT NULL,
    `has_kettle` BOOL NOT NULL,
    `has_vacuum` BOOL NOT NULL,
    `has_room_heater` BOOL NOT NULL,
    `home_area` DOUBLE NOT NULL,
    `has_pool` BOOL NOT NULL,
    `has_garden` BOOL NOT NULL,
    `vacation_month` VARCHAR(9) NOT NULL  COMMENT 'january: January\nfebruary: February\nmarch: March\napril: April\nmay: May\njune: June\njuly: July\naugust: August\nseptember: September\noctober: October\nnovember: November\ndecember: December',
    `vacation_days` INT NOT NULL,
    `climate` VARCHAR(9) NOT NULL  COMMENT 'HOT: Hot\nCOLD: Cold\nHUMID: Humid\nDRY: Dry\nTEMPERATE: Temperate',
    `user_id` CHAR(36) NOT NULL,
    CONSTRAINT `fk_question_user_8a8274de` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `water_consumption` (
    `id` CHAR(36) NOT NULL  PRIMARY KEY,
    `month` VARCHAR(9) NOT NULL  COMMENT 'january: January\nfebruary: February\nmarch: March\napril: April\nmay: May\njune: June\njuly: July\naugust: August\nseptember: September\noctober: October\nnovember: November\ndecember: December',
    `year` INT NOT NULL,
    `water_consumption` DOUBLE NOT NULL,
    `created_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `user_id` CHAR(36) NOT NULL,
    UNIQUE KEY `uid_water_consu_user_id_45acc6` (`user_id`, `month`, `year`),
    CONSTRAINT `fk_water_co_user_76678167` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `aerich` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `version` VARCHAR(255) NOT NULL,
    `app` VARCHAR(100) NOT NULL,
    `content` JSON NOT NULL
) CHARACTER SET utf8mb4;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """


MODELS_STATE = (
    "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"
)
