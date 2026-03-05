from transformers import RobertaTokenizer, RobertaForSequenceClassification, Trainer, TrainingArguments
import torch
from datasets import load_dataset, concatenate_datasets
import logging
import os
import sys

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration parameters
CONFIG = {
    "model_name": "roberta-base",
    "data_paths": [
        "machine_learning/training/dataset/dataset1.csv",
        # "machine_learning/training/dataset/dataset1.csv"
    ],  # List of dataset paths
    "output_dir": "machine_learning/saved_model",
    "num_labels": 2,
    "num_train_epochs": 2,
    "batch_size": 16,
    "save_steps": 500,
    "save_total_limit": 2
}


def fine_tune_roberta():
    # Check if CUDA is available and use GPU if possible
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"Using device: {device}")

    try:
        # Load tokenizer and model
        tokenizer = RobertaTokenizer.from_pretrained(CONFIG["model_name"])
        model = RobertaForSequenceClassification.from_pretrained(
            CONFIG["model_name"], num_labels=CONFIG["num_labels"]
        ).to(device)
    except Exception as e:
        logger.error("Failed to load model or tokenizer.")
        logger.exception(e)
        sys.exit(1)

    # Verify all data files exist
    for data_path in CONFIG["data_paths"]:
        if not os.path.exists(data_path):
            logger.error(f"Data file not found at {data_path}")
            sys.exit(1)

    try:
        # Load and concatenate datasets
        datasets = []
        for data_path in CONFIG["data_paths"]:
            dataset = load_dataset("csv", data_files=data_path)["train"]
            datasets.append(dataset)

        # Concatenate all datasets
        combined_dataset = concatenate_datasets(datasets)

        # Tokenize the dataset
        def tokenize_function(examples):
            return tokenizer(examples["text"], truncation=True, padding="max_length")

        combined_dataset = combined_dataset.map(tokenize_function, batched=True)
    except Exception as e:
        logger.error("Failed to load and tokenize datasets.")
        logger.exception(e)
        sys.exit(1)

    # Set up training arguments
    training_args = TrainingArguments(
        output_dir=CONFIG["output_dir"],
        num_train_epochs=CONFIG["num_train_epochs"],
        per_device_train_batch_size=CONFIG["batch_size"],
        save_steps=CONFIG["save_steps"],
        save_total_limit=CONFIG["save_total_limit"],
        logging_dir=os.path.join(CONFIG["output_dir"], "logs"),  # For logging
        logging_steps=100,
        eval_strategy="no",  # No eval dataset provided; set to "epoch" if you add one
    )

    # Initialize Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=combined_dataset,
    )

    # Start training with exception handling
    try:
        logger.info("Starting training...")
        trainer.train()
        logger.info("Training completed successfully.")
    except Exception as e:
        logger.error("Training failed.")
        logger.exception(e)
        sys.exit(1)

    # Save model and tokenizer
    try:
        model.save_pretrained(CONFIG["output_dir"])
        tokenizer.save_pretrained(CONFIG["output_dir"])
        logger.info(f"Model and tokenizer saved to {CONFIG['output_dir']}")
    except Exception as e:
        logger.error("Failed to save model or tokenizer.")
        logger.exception(e)


if __name__ == "__main__":
    fine_tune_roberta()
