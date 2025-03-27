# LLM Finetuning Components

This directory contains components for creating training datasets and fine-tuning Gemini models for expert finding.

## Directory Structure

```
-backend
--llm-finetuning/
├── dataset-creator/     # Creates training datasets from expert data
├── gemini-finetuner/   # Handles Gemini model fine-tuning and chat
├── images/             # Docker images for the components
└── autotrain-runner/   # AutoTrain integration

--secrets/ secrects-file.json # from GCP service account and set it to required name
--env.dev
```

## Workflow

1. First, use the dataset creator to generate training data
2. Then, use the gemini finetuner to train and interact with the model

## Components

### Dataset Creator
Generates training datasets for fine-tuning the Gemini model.

Available commands:
- `--help`: Display help message and available commands
- `--generate`: Generate training examples from expert data
- `--upload`: Upload generated dataset to GCS bucket

A complete workflow inclues:

1. update the data storage location:

### Default Training Data Structure
```
your-bucket/
└── llm_ft/
    ├── train.jsonl
    ├── test.jsonl
    ├── train.csv
    ├── test.csv
    └── instruct-dataset.csv
```
2. use the following commend to create, prepare and upload the training&validation dataset

```bash
cd dataset-creator
./docker-shell.sh
python cli.py --help     # Verifying the app is running, show available commends
python cli.py --generate # Generate training dataset
python cli.py --prepare # prepare the file format for Gemini
python cli.py --upload # upload to the project bucket.
```

### Gemini Finetuner
Handles model training and chat interactions.

```bash
cd gemini-finetuner
./docker-shell.sh
python cli.py --help     # View available commands
python cli.py --train    # Train the model
python cli.py --chat     # Chat with the model
```

`--chat`: Initiates an interactive chat session with the fine-tuned model. The command will:
1. Display detailed debug logs showing model connection and endpoint information
2. Start an interactive terminal-based chat interface
3. Process user inputs and display model responses
4. Exit the chat session when 'exit', 'quit', or 'bye' is entered

Available commands:
- `--help`: Display help message and available commands
- `--train`: Start model training process
- `--train --wait`: Start training and wait for completion
- `--chat`: Start interactive chat session with the model

## Configuration

### Environment Variables
Required environment variables in `env.dev`:
```
GCP_PROJECT=your-project-id
GCS_BUCKET_NAME=your-bucket-name
GEMINI_MODEL_NAME=gemini-1.5-flash-002  # Base model for fine-tuning
GEMINI_MODEL_VERSION=latest
GEMINI_MODEL_ENDPOINT=your-endpoint
GEMINI_MODEL_REGION=us-central1
```

### Service Account
Place your service account key in: 
```
secrets/
└── llm-service-account.json
```
and name it to llm-service-account.json

Required roles:
- Vertex AI User
- Vertex AI Service Agent
- Storage Admin
- Service Account User


## Model Configuration

### Training Parameters
- Base model: gemini-1.5-flash-002 (gemini-1.5-pro-002 could be used for better performance)
- Training epochs: 5
- Adapter size: 8
- Learning rate multiplier: 1.0

### Generation Settings
- Max output tokens: 3000
- Temperature: 0.75
- Top-p: 0.95

## Development

### Building Docker Images
```bash
cd <component-directory>
./docker-shell.sh
```

### Testing
```bash
python cli.py --help  
python cli.py --chat  
python cli.py --train 
```

## Dependencies
- Docker
- Google Cloud Platform account
- Vertex AI API enabled
- GCS bucket with appropriate permissions


