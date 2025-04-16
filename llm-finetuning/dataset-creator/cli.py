import os
import argparse
import pandas as pd
import json
import time
import glob
from sklearn.model_selection import train_test_split
from google.cloud import storage
import vertexai
from vertexai.generative_models import GenerativeModel, Part, SafetySetting, FinishReason
import vertexai.generative_models as generative_models

# Setup
GCP_PROJECT = os.environ["GCP_PROJECT"]
GCP_LOCATION = "us-central1"
GENERATIVE_MODEL = "gemini-1.5-flash-001"
OUTPUT_FOLDER = "data"
GCS_BUCKET_NAME = os.environ["GCS_BUCKET_NAME"]

# Set the credentials path explicitly
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/secrets/llm-service-account.json"

# Configuration settings for the content generation
generation_config = {
    "max_output_tokens": 8192,  # Maximum number of tokens for output
    "temperature": 1,  # Control randomness in output
    "top_p": 0.95,  # Use nucleus sampling
}

# Safety settings to filter out harmful content
safety_settings = [
    SafetySetting(
        category=SafetySetting.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
        threshold=SafetySetting.HarmBlockThreshold.BLOCK_ONLY_HIGH
    ),
    SafetySetting(
        category=SafetySetting.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
        threshold=SafetySetting.HarmBlockThreshold.BLOCK_ONLY_HIGH
    ),
    SafetySetting(
        category=SafetySetting.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
        threshold=SafetySetting.HarmBlockThreshold.BLOCK_ONLY_HIGH
    ),
    SafetySetting(
        category=SafetySetting.HarmCategory.HARM_CATEGORY_HARASSMENT,
        threshold=SafetySetting.HarmBlockThreshold.BLOCK_ONLY_HIGH
    )
]

# System Prompt
SYSTEM_INSTRUCTION = """Generate a set of 20 question-answer pairs in English about academic and professional expertise discovery, as used within the ExpertFinder application. Adopt the tone and perspective of a friendly, warm, and approachable assistant trained to support users in identifying experts based on their professional profiles and research contributions. All answers should be aligned with data that could realistically be sourced from platforms like LinkedIn and Google Scholar. Adhere to the following guidelines:


1. Question Independence:
   - Ensure each question-answer pair is completely independent and self-contained
   - Do not reference other questions or answers within the set
   - Each Q&A pair should be understandable without any additional context

2. Technical Depth and Factual Integrity:
   - Base answers on the type of structured data typically available in professional directories and academic databases
   - Answers should simulate realistic summaries from profile data, such as work experience, research topics, publication metrics, or technical skills
   - Incorporate plausible metadata (e.g., number of publications, research interests, job titles, years of experience) to create informative responses
   - Include specific data points like publication counts, citation metrics, and years of experience
   - Reference relevant technical terms, methodologies, and industry standards

3. Professional Tone and Style:
   - Use a clear, friendly, and approachable tone that conveys warmth and helpfulness
   - Responses should feel welcoming and engaging, aiming to make users comfortable and supported
   - Maintain accuracy, relevance, and clarity while adding warmth and friendliness
   - Balance technical knowledge with accessible, conversational explanations
   - End every answer with a cheerful, smiling expression (^_^)

4. Answer Framing:
   - Begin answers in a friendly and welcoming manner, for example:
     * "Glad you asked!Based on the profile information..."
     * "Sure thing! According to their academic and professional background..."
     * "Happy to help! This expert has demonstrated expertise in..."
     * "Absolutely! John Smith has over eight years of solid experience in data engineering..."
     * "Great question! A few standout experts are Dr. Fei-Fei Li from Stanford, who collaborates extensively with Google AI..."
     * "Happy to help! Dr. Sarah Chen has significantly impacted machine learning through 15 influential papers published at NeurIPS and ICML..."
     * "Sure thing! Notable experts include Dr. Alec Radford from Anthropic, Dr. Ilya Sutskever at OpenAI, and Dr. Jeff Dean of Google..."
    Avoid overly formal or impersonal phrasing  
  -Do not use personal opinions or first-person phrasing beyond friendly introductions. Speak as an approachable assistant summarizing data clearly.

5. Content Coverage:
   - Cover a range of expert attributes, such as:
     * Academic qualifications and research focus
     * Current and past job roles
     * Technical skills and certifications
     * Citation metrics or publication venues
     * Conference participation or editorial roles
     * Industry relevance or cross-disciplinary experience
     * Teaching and mentoring experience
     * Patents and intellectual property
     * Industry awards and recognition
     * Professional memberships and affiliations
   - Ensure that answers remain plausible and realistic based on common data formats from LinkedIn and Google Scholar

6. Question Types:
   - Include a variety of question forms:
     * Factual queries ('What is...')
     * Analytical comparisons ('How does...')
     * Capability inquiries ('Can this expert help with...')
     * Summaries ('Give an overview of...')
     * Experience verification ('Has this expert worked on...')
     * Skill assessment ('What level of expertise does...')
   - Mix questions about specific experts with open-ended discovery questions

7. Complexity and Range:
   - Provide a mix of basic information and advanced technical insights
   - Include both straightforward queries and more analytical questions
   - Cover both general expertise and specific technical skills
   - Balance questions about academic and industry experience
   - Include questions about both current and historical contributions

8. JSON Output Format:
   - Output the Q&A pairs in JSON format, where each item is an object with 'question' and 'answer' keys
   - Use double quotes for keys and string values
   - Escape any internal apostrophes with a backslash (\\') to maintain valid JSON structure
   - Ensure there are no unescaped special characters that could break standard JSON decoding

9. Cultural and Institutional Context:
   - Consider the role of expertise in different academic and professional contexts
   - Include questions about cross-cultural and international collaboration
   - Reference institutional affiliations and their significance
   - Consider the impact of different academic and industry environments
   - Include questions about mentorship and knowledge transfer across cultures

10. Accuracy and Relevance:
    - Ensure all information, especially technical data, is factually correct and up-to-date
    - Focus on widely accepted information in the field of expertise discovery
    - Maintain consistency in how expertise levels are described
    - Ensure answers reflect current industry standards and academic practices
    - Verify that all cited metrics and achievements are realistic

Example JSON Output (Note: This format will be automatically converted to Gemini's required format during data preparation):
```json
[
  {
    "question": "What is Dr. Anna Li's primary research focus based on her academic profile?",
    "answer": "Glad you asked! Dr. Anna Li specializes in natural language processing, especially multilingual language models and low-resource machine translation. She frequently publishes at ACL and EMNLP and already has over 1,200 citations—quite impressive! ^_^"
  },
  {
    "question": "Can John Smith be considered an expert in data engineering?",
    "answer": "Absolutely! John Smith has over eight years of solid experience in data engineering. He's currently a Lead Data Engineer at a Fortune 500 company, holds Apache Spark and Google Cloud Data Engineering certifications, and excels in building large-scale data pipelines and real-time analytics systems. ^_^"
  },
  {
    "question": "Who are the leading researchers in computer vision with industry experience?",
    "answer": "Great question! A few standout experts are Dr. Fei-Fei Li from Stanford, who collaborates extensively with Google AI; Dr. Andrej Karpathy, formerly Tesla's Director of AI; and Dr. Jitendra Malik of UC Berkeley, who has contributed significantly at Facebook AI Research. They're all fantastic examples of combining academic expertise with industry applications! ^_^"
  },
  {
    "question": "What are Dr. Sarah Chen's key contributions to machine learning?",
    "answer": "Happy to help! Dr. Sarah Chen has significantly impacted machine learning through 15 influential papers published at NeurIPS and ICML, gathering over 2,500 citations. Her groundbreaking work in transfer learning earned her the Best Paper Award at ICML 2019, and she's now innovating few-shot learning methods at Google Research. ^_^"
  },
  {
    "question": "Which experts have the most experience in implementing large language models?",
    "answer": "Sure thing! Notable experts include Dr. Alec Radford from Anthropic, Dr. Ilya Sutskever at OpenAI, and Dr. Jeff Dean of Google. They've each played pivotal roles in developing influential language models such as GPT and PaLM, bringing both theoretical insights and practical implementations to the field. ^_^"
  }
]
"""


def generate():
    print("generate()")

    # Make dataset folders
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    # Initialize Vertex AI project and location
    vertexai.init(project=GCP_PROJECT, location=GCP_LOCATION)
    
    # Initialize the GenerativeModel with specific system instructions
    model = GenerativeModel(
        GENERATIVE_MODEL,
        system_instruction=[SYSTEM_INSTRUCTION]
    )

    INPUT_PROMPT = """Generate 20 diverse, informative, and engaging question-answer pairs about expert discovery and professional profiles. Include both specific expert queries (e.g., about Dr. Anna Li or John Smith) and open-ended discovery questions (e.g., 'Who are the top researchers in NLP?'). Ensure each pair is independent and self-contained, maintain a professional tone, incorporate realistic profile data, and keep all content in English."""
    NUM_ITERATIONS = 5 # INCREASE TO CREATE A LARGE DATASET

    # Loop to generate and save the content
    for i in range(0, NUM_ITERATIONS):
        print(f"Generating batch: {i}")
        try:
          responses = model.generate_content(
            [INPUT_PROMPT],  # Input prompt
            generation_config=generation_config,  # Configuration settings
            safety_settings=safety_settings,  # Safety settings
            stream=False,  # Enable streaming for responses
          )
          generated_text = responses.text

          # Create a unique filename for each iteration
          file_name = f"{OUTPUT_FOLDER}/expert_qa_{i}.txt"
          # Save
          with open(file_name, "w") as file:
            file.write(generated_text)
        except Exception as e:
          print(f"Error occurred while generating content: {e}")


def prepare():
    print("prepare()")

    # Get the generated files
    output_files = glob.glob(os.path.join(OUTPUT_FOLDER, "expert_qa_*.txt"))
    output_files.sort()

    # Consolidate the data
    output_pairs = []
    errors = []
    for output_file in output_files:
        print("Processing file:", output_file)
        with open(output_file, "r") as read_file:
            text_response = read_file.read()
        
        text_response = text_response.replace("```json","").replace("```","")

        try:
            json_responses = json.loads(text_response)
            output_pairs.extend(json_responses)
        
        except Exception as e:
            errors.append({"file": output_file, "error": str(e)})
    
    print("Number of errors:", len(errors))
    print(errors[:5])

    # Save the dataset
    output_pairs_df = pd.DataFrame(output_pairs)
    output_pairs_df.drop_duplicates(subset=['question'], inplace=True)
    output_pairs_df = output_pairs_df.dropna()
    print("Shape:", output_pairs_df.shape)
    print(output_pairs_df.head())
    filename = os.path.join(OUTPUT_FOLDER, "instruct-dataset.csv")
    output_pairs_df.to_csv(filename, index=False)

    # Build training formats
    output_pairs_df['text'] = "human: " + output_pairs_df['question'] + "\n" + "bot: " + output_pairs_df['answer']
    
    # Gemini Data prep: https://cloud.google.com/vertex-ai/generative-ai/docs/models/gemini-supervised-tuning-prepare
    # {"contents":[{"role":"user","parts":[{"text":"..."}]},{"role":"model","parts":[{"text":"..."}]}]}
    output_pairs_df["contents"] = output_pairs_df.apply(lambda row: [{"role":"user","parts":[{"text": row["question"]}]},{"role":"model","parts":[{"text": row["answer"]}]}], axis=1)


    # Test train split
    df_train, df_test = train_test_split(output_pairs_df, test_size=0.1, random_state=42)
    df_train[["text"]].to_csv(os.path.join(OUTPUT_FOLDER, "train.csv"), index = False)
    df_test[["text"]].to_csv(os.path.join(OUTPUT_FOLDER, "test.csv"), index = False)

    # Gemini : Max numbers of examples in validation dataset: 256
    df_test = df_test[:256]

    # JSONL
    with open(os.path.join(OUTPUT_FOLDER, "train.jsonl"), "w") as json_file:
        json_file.write(df_train[["contents"]].to_json(orient='records', lines=True))
    with open(os.path.join(OUTPUT_FOLDER, "test.jsonl"), "w") as json_file:
        json_file.write(df_test[["contents"]].to_json(orient='records', lines=True))


def upload():
    print("upload()")

    storage_client = storage.Client()
    bucket = storage_client.bucket(GCS_BUCKET_NAME)
    timeout = 300

    data_files = glob.glob(os.path.join(OUTPUT_FOLDER, "*.jsonl")) + glob.glob(os.path.join(OUTPUT_FOLDER, "*.csv"))
    data_files.sort()
    
    # Upload
    for index, data_file in enumerate(data_files):
        filename = os.path.basename(data_file)
        destination_blob_name = os.path.join("llm_ft", filename)
        blob = bucket.blob(destination_blob_name)
        print("Uploading file:", data_file, destination_blob_name)
        blob.upload_from_filename(data_file, timeout=timeout)
    

def main(args=None):
    print("CLI Arguments:", args)

    if args.generate:
        generate()

    if args.prepare:
        prepare()
      
    if args.upload:
        upload()


if __name__ == "__main__":
    # Generate the inputs arguments parser
    # if you type into the terminal '--help', it will provide the description
    parser = argparse.ArgumentParser(description="CLI")

    parser.add_argument(
        "--generate",
        action="store_true",
        help="Generate data",
    )
    parser.add_argument(
        "--prepare",
        action="store_true",
        help="Prepare data",
    )
    parser.add_argument(
        "--upload",
        action="store_true",
        help="Upload data to bucket",
    )

    args = parser.parse_args()

    main(args)