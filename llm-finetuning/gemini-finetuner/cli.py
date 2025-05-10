import argparse
import glob
import json
import os
import time

import pandas as pd
import vertexai
from google.cloud import storage
from vertexai.generative_models import GenerationConfig, GenerativeModel
from vertexai.preview.language_models import ChatModel, TextGenerationModel
from vertexai.preview.tuning import sft

# Setup
GCP_PROJECT = os.environ["GCP_PROJECT"]
GCP_LOCATION = os.environ.get("GEMINI_MODEL_REGION") or os.environ.get("LOCATION") or "us-central1"
GCS_BUCKET_NAME = os.environ["GCS_BUCKET_NAME"]

# Print environment information
print(f"Using GCP Project: {GCP_PROJECT}")
print(f"Using Region: {GCP_LOCATION}")
print(f"Using GCS Bucket: {GCS_BUCKET_NAME}")

# Training data paths - updated to match actual bucket structure
TRAIN_DATASET = f"gs://{GCS_BUCKET_NAME}/llm_ft/train.jsonl"
VALIDATION_DATASET = f"gs://{GCS_BUCKET_NAME}/llm_ft/test.jsonl"

# Model configuration
GENERATIVE_SOURCE_MODEL = "gemini-1.5-flash-002" 
TUNED_MODEL_DISPLAY_NAME = "expert-finder-v4-friendly"

# Configuration settings for the content generation
generation_config = {
    "max_output_tokens": 3000,  # Maximum number of tokens for output
    "temperature": 0.75,  # Control randomness in output
    "top_p": 0.95,  # Use nucleus sampling
}

# Initialize Vertex AI with the detected region
try:
    vertexai.init(project=GCP_PROJECT, location=GCP_LOCATION)
    print(f"Vertex AI initialized with project={GCP_PROJECT}, location={GCP_LOCATION}")
except Exception as e:
    print(f"Warning: Failed to initialize Vertex AI: {str(e)}")
    print("This may cause issues when accessing the model.")

def train(wait_for_job=False):
    print("Starting training process...")
    
    try:
        
        print("Creating SupervisedTuningJob")
        # Supervised Fine Tuning
        sft_tuning_job = sft.train(
            source_model=GENERATIVE_SOURCE_MODEL,
            train_dataset=TRAIN_DATASET,
            validation_dataset=VALIDATION_DATASET,
            epochs=5,  # Increased epochs for better training
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
    """Chat with the model"""
    print("Starting chat with model...")
    print("Type 'exit' 'quit' or 'bye' to end the chat")
    print("-" * 50)
    
    # First, list all available tuning jobs to find model endpoints
    print(f"Listing tuning jobs...")
    
    try:
        # List all tuning jobs
        tuning_jobs = sft.SupervisedTuningJob.list()
        jobs_list = list(tuning_jobs)
        print(f"Found {len(jobs_list)} tuning jobs")
        
        # Store endpoint information if found
        target_endpoint = None
        
        # Print all jobs and look for our target job
        for job in jobs_list:
            print(f"Job: {job.resource_name}")
            
            try:
                if hasattr(job, 'tuned_model_endpoint_name') and job.tuned_model_endpoint_name:
                    print(f"  Endpoint: {job.tuned_model_endpoint_name}")
                if hasattr(job, 'state'):
                    print(f"  State: {job.state}")
                    
                # Check if this is our target job
                if "6934856523440979968" in job.resource_name:
                    if hasattr(job, 'tuned_model_endpoint_name') and job.tuned_model_endpoint_name:
                        target_endpoint = job.tuned_model_endpoint_name
                        print(f"Found target model endpoint: {target_endpoint}")
            except Exception as job_err:
                print(f"  Error getting job details: {str(job_err)}")
        
        # If we found our endpoint, try to access it
        if target_endpoint:
            print(f"\nAttempting to access model via endpoint: {target_endpoint}")
            try:
                # Use GenerativeModel with the endpoint
                generative_model = GenerativeModel(target_endpoint)
                
                # Test the connection
                test_response = generative_model.generate_content("Hello")
                print("Successfully connected to tuned model via endpoint!")
                print(f"Test response: {test_response.text}")
                
                # Start the chat loop
                print(f"Using tuned model - ready for chat!")
                while True:
                    try:
                        # Get user input
                        user_input = input("\nYou: ").strip()
                        
                        # Check for exit command
                        if user_input.lower() in ['exit', 'quit', 'bye']:
                            print("\nGoodbye!")
                            break
                        
                        if not user_input:
                            continue
                            
                        # Get model response
                        response = generative_model.generate_content(
                            [user_input],  # Input prompt
                            generation_config=generation_config,  # Configuration settings
                            stream=False,  # Enable streaming for responses
                        )
                        
                        # Print response
                        print("\nModel:", response.text)
                        print("-" * 50)
                        
                    except Exception as e:
                        print(f"\nError during chat: {str(e)}")
                        print("Type 'exit' to end the chat or try again")
                        continue
            except Exception as endpoint_err:
                print(f"Error accessing endpoint: {str(endpoint_err)}")
                print("\nAlternative approach: Look for the endpoint ID in the Google Cloud Console:")
                print("1. Go to https://console.cloud.google.com/vertex-ai/studio/tuning")
                print("2. Find your model 'expert-finder-v2'")
                print("3. Copy the endpoint ID (format: projects/.../endpoints/...)")
                print("4. Modify the chat() function to use that endpoint directly like in your professor's code")
                
                # Suggest manual endpoint usage
                print("\nExample code modification:")
                print("def chat():")
                print('    MODEL_ENDPOINT = "projects/YOUR_PROJECT_ID/locations/us-central1/endpoints/YOUR_ENDPOINT_ID"')
                print("    generative_model = GenerativeModel(MODEL_ENDPOINT)")
                print("    # Then implement the chat loop...")
                return
        else:
            print("Target job found, but no endpoint available.")
            print("Check the Google Cloud Console to find your model's endpoint.")
            return
            
    except Exception as e:
        print(f"Error listing tuning jobs: {str(e)}")
        print("Could not list tuning jobs. Try accessing the model endpoint directly.")
        return

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