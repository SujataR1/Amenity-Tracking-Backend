from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `blacklisted_tokens` MODIFY COLUMN `token` VARCHAR(500) NOT NULL;
        ALTER TABLE `questionnaire_answers` ADD `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6);
        ALTER TABLE `questionnaire_answers` ADD `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `blacklisted_tokens` MODIFY COLUMN `token` VARCHAR(255) NOT NULL;
        ALTER TABLE `questionnaire_answers` DROP COLUMN `created_at`;
        ALTER TABLE `questionnaire_answers` DROP COLUMN `updated_at`;"""


MODELS_STATE = (
    "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"
    "c+"
)
