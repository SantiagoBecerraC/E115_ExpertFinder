import os
import argparse
import pandas as pd
import json
import time
import glob
from google.cloud import storage
import vertexai
from vertexai.preview.tuning import sft
from vertexai.generative_models import GenerativeModel, GenerationConfig

# Setup
GCP_PROJECT = os.environ["GCP_PROJECT"]
GCP_LOCATION = os.environ.get("GEMINI_MODEL_REGION", "us-central1")
GCS_BUCKET_NAME = os.environ["GCS_BUCKET_NAME"]

# Training data paths - updated to match actual bucket structure
TRAIN_DATASET = f"gs://{GCS_BUCKET_NAME}/llm_ft/train.jsonl"
VALIDATION_DATASET = f"gs://{GCS_BUCKET_NAME}/llm_ft/test.jsonl"

# Model configuration
GENERATIVE_SOURCE_MODEL = "gemini-1.5-flash-002" 
TUNED_MODEL_DISPLAY_NAME = "expert-finder-v1"

# Configuration settings for the content generation
generation_config = {
    "max_output_tokens": 3000,  # Maximum number of tokens for output
    "temperature": 0.75,  # Control randomness in output
    "top_p": 0.95,  # Use nucleus sampling
}

vertexai.init(project=GCP_PROJECT, location=GCP_LOCATION)


def train(wait_for_job=False):
    print("Starting training process...")
    
    try:
        
        print("Creating SupervisedTuningJob")
        # Supervised Fine Tuning
        sft_tuning_job = sft.train(
            source_model=GENERATIVE_SOURCE_MODEL,
            train_dataset=TRAIN_DATASET,
            validation_dataset=VALIDATION_DATASET,
            epochs=1,  # Increased epochs for better training
            adapter_size=8,  # Increased adapter size
            learning_rate_multiplier=1.0,
            tuned_model_display_name=TUNED_MODEL_DISPLAY_NAME,
        )
        print("SupervisedTuningJob created. Resource name:", sft_tuning_job.resource_name)
        print("To use this SupervisedTuningJob in another session:")
        print(f"tuning_job = sft.SupervisedTuningJob('{sft_tuning_job.resource_name}')")
        print("\nView Tuning Job:")
        print(f"https://console.cloud.google.com/vertex-ai/generative/language/locations/{GCP_LOCATION}/tuning/tuningJob/{sft_tuning_job.resource_name.split('/')[-1]}?project={GCP_PROJECT}")
        print("\nTraining job started. Monitoring progress...\n")
        
        if wait_for_job:
            print("Waiting for job completion...")
            while not sft_tuning_job.has_ended:
                time.sleep(60)
                sft_tuning_job.refresh()
                print("Job in progress...")
                if sft_tuning_job.state == sft.TuningJobState.FAILED:
                    raise Exception(f"Training job failed: {sft_tuning_job.error}")
            
            print("\nTraining completed!")
            print(f"Tuned model name: {sft_tuning_job.tuned_model_name}")
            print(f"Tuned model endpoint name: {sft_tuning_job.tuned_model_endpoint_name}")
            print(f"Experiment: {sft_tuning_job.experiment}")
        else:
            print("\nTraining job started. Use the provided URL to monitor progress.")
            print("You can also use the resource name to check status in another session.")

    except Exception as e:
        print(f"Error during training: {str(e)}")
        raise

def chat():
    print("Starting chat...")
    try:
        # Use the base model instead of an endpoint
        generative_model = GenerativeModel(GENERATIVE_SOURCE_MODEL)

        query = "Who are the top researchers in natural language processing at Harvard?"
        print("Query:", query)
        response = generative_model.generate_content(
            [query],  # Input prompt
            generation_config=generation_config,  # Configuration settings
            stream=False,  # Enable streaming for responses
        )
        generated_text = response.text
        print("\nFine-tuned LLM Response:", generated_text)
    except Exception as e:
        print(f"Error during chat: {str(e)}")
        raise

def main(args=None):
    print("CLI Arguments:", args)

    if args.train:
        train(wait_for_job=args.wait)
    
    if args.chat:
        chat()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CLI for Gemini model training and chat")
    parser.add_argument(
        "--train",
        action="store_true",
        help="Train model",
    )
    parser.add_argument(
        "--chat",
        action="store_true",
        help="Chat with model",
    )
    parser.add_argument(
        "--wait",
        action="store_true",
        help="Wait for training job to complete",
    )

    args = parser.parse_args()
    main(args)