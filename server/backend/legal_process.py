import os
import sys
import pickle
import json
import numpy as np
import re
import google.generativeai as genai
import atexit

# Try to import MongoDB packages, but make them optional
try:
    from pymongo.mongo_client import MongoClient
    from pymongo.server_api import ServerApi
    import hashlib
    from bson.objectid import ObjectId
    MONGODB_AVAILABLE = True
except ImportError:
   #print("Warning: MongoDB modules not available. User authentication and history features will be disabled.")
    MONGODB_AVAILABLE = False

from datetime import datetime

########################################################################
# 1. MONGODB CONNECTION & FUNCTIONS
########################################################################

def connect_to_db():
    """Connect to MongoDB database and return the skillseeker collection."""
    if not MONGODB_AVAILABLE:
        print("MongoDB features are disabled due to missing packages.")
        return None
        
    uri = "mongodb+srv://shayanarsalan2003:Shayan717@cluster0.ocn53.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    client = MongoClient(uri, server_api=ServerApi('1'))
    db = client["Cluster0"]
    skillseeker = db["skillseeker"]
    return skillseeker

def save_data_to_json_file(user_id, lawyer_data, summary_text=None):
    """Save data to a local JSON file for debugging and backup purposes."""
    try:
        # Parse lawyer_data to ensure it's a proper object, not a string
        if isinstance(lawyer_data, str):
            # Try to parse it first as regular JSON
            try:
                parsed_lawyer_data = json.loads(lawyer_data)
            except json.JSONDecodeError:
                # If that fails, try to extract JSON from markdown code blocks
                code_block_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', lawyer_data)
                if code_block_match:
                    json_content = code_block_match.group(1).strip()
                    parsed_lawyer_data = json.loads(json_content)
                else:
                    # If no code block, just use the string as is
                    parsed_lawyer_data = {"raw_data": lawyer_data}
        else:
            parsed_lawyer_data = lawyer_data
            
        # Create data structure
        data = {
            "user_id": str(user_id),
            "timestamp": datetime.now().strftime("%Y-%m-%d_%H-%M-%S"),
            "lawyer_data": parsed_lawyer_data,
            "summary": summary_text if summary_text else ""
        }
        
        # Create filename with timestamp for uniqueness
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"legal_data_{user_id}_{timestamp}.json"
        
        # Save to file
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
            
        print(f"Data successfully saved to local file: {filename}")
        return filename
    except Exception as e:
        print(f"Error saving to local JSON file: {e}")
        return None

def extract_json_from_text(text):
    """Extract JSON from a text that might contain markdown or other formatting."""
    # First, try to find JSON inside code blocks
    code_block_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
    if code_block_match:
        json_text = code_block_match.group(1).strip()
    else:
        # If not in code blocks, look for JSON structure
        json_match = re.search(r'(\{[\s\S]*\})', text)
        if json_match:
            json_text = json_match.group(1).strip()
        else:
            json_text = text
    
    # Try to parse the JSON
    try:
        return json.loads(json_text)
    except json.JSONDecodeError:
        print(f"Warning: Could not parse JSON from: {json_text[:100]}...")
        return {"raw_text": text}

def upload_legal_data_to_mongodb(user_id, json_file_path):
    """
    Upload legal data from local JSON file to MongoDB.
    Uses the existing medical fields to store lawyer data.
    Also saves the conversation summary.
    """
    if not MONGODB_AVAILABLE:
        print("MongoDB features are disabled due to missing packages.")
        return False
        
    try:
        # Read the JSON file
        with open(json_file_path, 'r') as f:
            data = json.load(f)
        
        # Parse the lawyer data
        lawyer_data = data.get("lawyer_data", {})
        summary_text = data.get("summary", "")
            
        # Extract lawyer information to store in medical fields
        doctor_names = []  # Will store lawyer names
        education = []     # Will store addresses
        expertise = []     # Will store cities
        contact_numbers = [] # Will store categories
        
        # Check if lawyer_data is an array directly or inside a lawyers key
        lawyers_array = None
        if isinstance(lawyer_data, list):
            lawyers_array = lawyer_data
        elif isinstance(lawyer_data, dict) and "lawyers" in lawyer_data:
            lawyers_array = lawyer_data.get("lawyers", [])
        else:
            print(f"Warning: Unexpected lawyer data format: {type(lawyer_data)}")
            print(f"Lawyer data content (sample): {str(lawyer_data)[:200]}...")
            lawyers_array = []
            
        # Process each lawyer
        for lawyer in lawyers_array:
            if isinstance(lawyer, dict):
                doctor_names.append(lawyer.get("Name", ""))  # Store lawyer name in DoctorNames
                education.append(lawyer.get("Address", ""))  # Store address in Education
                expertise.append(lawyer.get("City", ""))  # Store city in Expertise
                contact_numbers.append(lawyer.get("Category", ""))  # Store category in ContactNumbers
        
        # Connect to database
        skillseeker = connect_to_db()
        if not skillseeker:
            return False
            
        user_id_obj = ObjectId(user_id)
        
        # Debug info
        print(f"Processing {len(lawyers_array)} lawyers")
        print(f"Lawyer names (storing in DoctorNames): {doctor_names}")
        print(f"Addresses (storing in Education): {education}")
        print(f"Cities (storing in Expertise): {expertise}")
        print(f"Categories (storing in ContactNumbers): {contact_numbers}")
        
        # Create conversation entry for the summary
        conversation_entry = {
            "query": "legal_summary",
            "response": summary_text
        }
        
        # First, clear existing data
        skillseeker.update_one(
            {"_id": user_id_obj},
            {"$set": {
                "DoctorNames": [],
                "Education": [],
                "Expertise": [],
                "ContactNumbers": [],
                "Conversation": []  # Clear conversation array too
            }}
        )
        
        # Then update with new lawyer data and conversation summary
        update = {
            "$set": {
                "DoctorNames": doctor_names,    # Lawyer Names
                "Education": education,         # Addresses
                "Expertise": expertise,         # Cities
                "ContactNumbers": contact_numbers  # Categories
            },
            "$push": {
                "Conversation": conversation_entry  # Add summary to conversation
            }
        }
        
        # Update the document
        result = skillseeker.update_one(
            {"_id": user_id_obj},
            update
        )
        
        if result.matched_count == 0:
            print(f"Error: No document found with ID {user_id}")
            return False
        elif result.modified_count == 0:
            print("Warning: Document found but not modified")
            return False
        else:
            print(f"Lawyer data and summary successfully uploaded to MongoDB from file {json_file_path}")
            return True
            
    except Exception as e:
        print(f"Error uploading data to MongoDB: {e}")
        return False

########################################################################
# 2. GEMINI CONFIGURATION
########################################################################

genai.configure(api_key="AIzaSyCohbQG3sbkCf1LLbf1spVXFAgzjsRU1xA")

generation_config = {
    "temperature": 0.2,  # Low temperature for reliable JSON output
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-2.0-flash-lite",
    generation_config=generation_config,
)

########################################################################
# 3. AGENT CLASS DEFINITIONS
########################################################################

class Agent:
    """
    A simple agent that sends a prompt to Gemini and returns its text response.
    """
    def __init__(
        self,
        role: str,
        goal: str,
        backstory: str,
        allow_delegation: bool,
        verbose: bool,
        llm,
        expected_output: str = None,
    ):
        self.role = role
        self.goal = goal
        self.backstory = backstory
        self.allow_delegation = allow_delegation
        self.verbose = verbose  # set to False to disable logs
        self.llm = llm
        self.expected_output = expected_output

    def run(self, prompt: str) -> str:
        chat_session = self.llm.start_chat(history=[])
        response = chat_session.send_message(prompt)
        return response.text.strip()

########################################################################
# 4. DEFINE SPECIFIC AGENTS (with verbose disabled)
########################################################################

# Synthesis Agent: Produces a short three-line paragraph.
synthesis_agent = Agent(
    role="Legal Information Synthesis",
    goal="Produce a brief legal query analysis.",
    backstory=(
        "Based solely on the user's query, generate a concise three-line paragraph. "
        "It should include one recommended legal category (e.g., Business Law, Family Law, etc.) "
        "and a brief explanation of the likely legal issue."
    ),
    allow_delegation=False,
    verbose=False,
    llm=model,
    expected_output="A short 3-line paragraph with one recommended legal category and a brief explanation."
)

# Ranking Agent: Selects the top 3 lawyers and outputs their details in strict JSON.
ranking_agent = Agent(
    role="Lawyer Ranking Agent",
    goal="Select the top 3 lawyers and output their details in strict JSON format.",
    backstory=(
        "You have a set of lawyer profiles. Based on the synthesis result and the retrieved profiles, "
        "select the top 3 most relevant lawyers. Return the output in strict JSON format containing only the keys: "
        "'Name', 'Address', 'City', 'Phone', 'Category', 'Skills', 'Years_of_Experience', and 'Success_Rate'."
    ),
    allow_delegation=False,
    verbose=False,
    llm=model,
    expected_output=(
        '{"lawyers": ['
        '{"Name": "...", "Address": "...", "City": "...", "Phone": "...", '
        '"Category": "...", "Skills": "...", "Years_of_Experience": "...", "Success_Rate": "..."},'
        '{"Name": "...", "Address": "...", "City": "...", "Phone": "...", '
        '"Category": "...", "Skills": "...", "Years_of_Experience": "...", "Success_Rate": "..."},'
        '{"Name": "...", "Address": "...", "City": "...", "Phone": "...", '
        '"Category": "...", "Skills": "...", "Years_of_Experience": "...", "Success_Rate": "..."}'
        ']}'
    )
)

# Questions Agent: Generates 3 clarifying questions in strict JSON.
questions_agent = Agent(
    role="Legal Follow-up Questions Generator",
    goal="Generate 3 specific clarifying questions to further understand the legal query.",
    backstory=(
        "Based solely on the user's query, generate 3 specific clarifying questions that address details such as "
        "timeline, jurisdiction, prior legal action, and relevant documentation.\n\n"
        "Examples of good specific questions:\n"
        "'When did this legal issue first arise and what steps have you taken so far?',\n"
        "'Do you have any existing contracts or documentation related to this matter?',\n"
        "'Have you received any formal notices or been involved in any prior legal proceedings on this issue?'\n\n"
        "Return ONLY the following JSON format with no additional text:"
    ),
    allow_delegation=False,
    verbose=False,
    llm=model,
    expected_output='{"questions": [{"id": 1, "text": "When did this legal issue first arise and what steps have you taken so far?"}, {"id": 2, "text": "Do you have any existing contracts or documentation related to this matter?"}, {"id": 3, "text": "Have you received any formal notices or been involved in any prior legal proceedings on this issue?"}]}'
)

# Conversational Agent: Provides additional explanation using full context.
conversational_agent = Agent(
    role="Conversational Legal Assistant",
    goal="Provide comprehensive legal guidance based on all available context.",
    backstory=(
        "Access the full context—including the original query, synthesis, ranked lawyers, and follow-up Q/A—and provide a detailed explanation or further recommendations."
    ),
    allow_delegation=False,
    verbose=False,
    llm=model,
    expected_output="A detailed explanation referencing the full context."
)

# Summary Agent - Creates a personalized summary when conversation ends
summary_agent = Agent(
    role="Legal Consultation Summary Agent",
    goal="Create a personalized summary of the entire legal consultation.",
    backstory=(
        "You create friendly, personalized summaries of legal consultations. "
        "Your summaries address the user by name and reference specific details from their conversation, "
        "including their legal concerns, the recommended lawyers, and main points from the discussion. "
        "The tone is warm, professional, and helpful, offering to assist further with their legal needs while "
        "emphasizing the importance of seeking actual legal advice."
    ),
    allow_delegation=False,
    verbose=False,
    llm=model,
    expected_output=(
        "Hey [Name]! Based on our discussion about your [specific legal issue], "
        "I've recommended several lawyers specialized in [legal area] who might be able to help. "
        "Remember that while this information can guide you, it's important to consult directly with a qualified attorney for proper legal advice."
    )
)

########################################################################
# 5. LOADING PRE-COMPUTED EMBEDDINGS (RAG)
########################################################################

def get_script_directory():
    """
    Get the directory of this script, with fallback for when __file__ is not available
    """
    try:
        return os.path.dirname(os.path.abspath(__file__))
    except NameError:
        # Fallback when __file__ is not defined (when running with -c)
        return os.getcwd()

def find_embeddings_file():
    """Search for the embeddings file in multiple possible locations"""
    potential_paths = [
        os.path.join(get_script_directory(), "lawyer_embeddings.pkl"),  # Same directory as script
        os.path.join(get_script_directory(), "..", "lawyer_embeddings.pkl"),  # Parent directory
        os.path.join(get_script_directory(), "..", "backend", "lawyer_embeddings.pkl"),  # Backend directory
        os.path.abspath("backend/lawyer_embeddings.pkl"),  # Absolute path from working directory
        os.path.abspath("lawyer_embeddings.pkl")  # Directly in working directory
    ]
    
    for path in potential_paths:
        if os.path.exists(path):
            print(f"Found embeddings file at: {path}", file=sys.stderr)
            return path
    
    # If we get here, we couldn't find the file
    print(f"Searched for embeddings in: {potential_paths}", file=sys.stderr)
    raise FileNotFoundError("Could not find lawyer_embeddings.pkl in any expected location")

def load_lawyer_embeddings(pkl_path: str):
    try:
        with open(pkl_path, "rb") as f:
            df = pickle.load(f)
        print(f"Successfully loaded embeddings from {pkl_path}", file=sys.stderr)
        return df
    except Exception as e:
        print(f"Error loading embeddings from {pkl_path}: {e}", file=sys.stderr)
        raise

def embed_text_with_gemini(text: str):
    try:
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=text,
            task_type="RETRIEVAL_DOCUMENT"
        )
        return np.array(result["embedding"], dtype=np.float32)
    except Exception as e:
        print(f"Error embedding text: {e}", file=sys.stderr)
        return None

def cosine_similarity(vec1, vec2):
    if vec1 is None or vec2 is None:
        return 0.0
    denom = np.linalg.norm(vec1) * np.linalg.norm(vec2)
    if denom == 0.0:
        return 0.0
    return float(np.dot(vec1, vec2) / denom)

def retrieve_relevant_lawyers(query_embedding, df, top_k=10):
    similarities = []
    for idx, row in df.iterrows():
        lawyer_emb = row['embedding']
        sim = cosine_similarity(query_embedding, lawyer_emb)
        similarities.append((idx, sim))
    similarities.sort(key=lambda x: x[1], reverse=True)
    top_indices = [x[0] for x in similarities[:top_k]]
    return df.iloc[top_indices]

########################################################################
# 6. ORCHESTRATION FUNCTIONS
########################################################################

def synthesize_information(user_query: str) -> str:
    prompt = (
        f"You are the legal synthesis agent.\n"
        f"User's original query:\n{user_query}\n\n"
        "Generate a concise three-line paragraph that includes one recommended legal category "
        "(such as Business Law, Family Law, Criminal Law, etc.) and a brief explanation of the likely legal issue."
    )
    return synthesis_agent.run(prompt)

def rank_top_lawyers(synthesis_text: str, retrieved_df) -> str:
    lawyers_text = []
    for idx, row in retrieved_df.iterrows():
        lawyer_profile = (
            f"Name: {row['Name']}\n"
            f"Address: {row['address']}\n"
            f"City: {row['city']}\n"
            f"Phone: {row['phone']}\n"
            f"Category: {row['Category']}\n"
            f"Skills: {row['Skills']}\n"
            f"Years of Experience: {row['Years_of_Experience']}\n"
            f"Success Rate: {row['Success_Rate']}"
        )
        lawyers_text.append(lawyer_profile)
    
    joined_lawyers = "\n\n".join(lawyers_text)
    
    prompt = (
        f"You are the Lawyer Ranking Agent.\n\n"
        f"Synthesis of user's legal situation:\n{synthesis_text}\n\n"
        f"Here are 10 potentially relevant lawyer profiles:\n\n{joined_lawyers}\n\n"
        "Based exclusively on the above synthesis and profiles, select the top 3 lawyers most suitable for the user's needs. "
        "Return the output in strict JSON format with the following structure:\n"
        '{"lawyers": [\n'
        '  {"Name": "...", "Address": "...", "City": "...", "Phone": "...", '
        '"Category": "...", "Skills": "...", "Years_of_Experience": "...", "Success_Rate": "..."},\n'
        '  {"Name": "...", "Address": "...", "City": "...", "Phone": "...", '
        '"Category": "...", "Skills": "...", "Years_of_Experience": "...", "Success_Rate": "..."},\n'
        '  {"Name": "...", "Address": "...", "City": "...", "Phone": "...", '
        '"Category": "...", "Skills": "...", "Years_of_Experience": "...", "Success_Rate": "..."}\n'
        ']}'
        "Your response must begin with '{' and be valid JSON."
    )
    result = ranking_agent.run(prompt)
    print(f"Debug - Raw ranked lawyers result: {result}", file=sys.stderr)
    return result

def generate_followup_questions(user_query: str) -> list:
    """
    Generate 3 follow-up questions using multiple retries if needed.
    This function tries different prompting approaches to get valid JSON.
    """
    max_attempts = 5  # Multiple attempts
    questions = []
    
    for attempt in range(1, max_attempts + 1):
        # Different prompting strategies for different attempts
        if attempt == 1:
            # First attempt: standard approach with expected format
            prompt = (
                f"You are a legal professional tasked with generating follow-up questions.\n\n"
                f"User's legal query: '{user_query}'\n\n"
                "Generate exactly 3 specific legal follow-up questions that would help clarify this situation.\n\n"
                "You MUST format your response as a valid JSON object using EXACTLY this structure:\n"
                '{"questions": [{"id": 1, "text": "your first question here"}, {"id": 2, "text": "your second question here"}, {"id": 3, "text": "your third question here"}]}\n\n'
                "Do not include any text outside the JSON structure. Your entire response must be a single valid JSON object.\n\n"
                "Example of correct JSON format:\n"
                '{"questions": [{"id": 1, "text": "When did this legal issue first arise and what steps have you taken so far?"}, {"id": 2, "text": "Do you have any existing contracts or documentation related to this matter?"}, {"id": 3, "text": "Have you received any formal notices or been involved in any prior legal proceedings on this issue?"}]}'
            )
        elif attempt == 2:
            # Second attempt: more direct, simpler prompt
            prompt = (
                f"Based on this legal query: '{user_query}'\n\n"
                "Your task is to output exactly 3 clarifying legal questions in STRICT JSON format.\n\n"
                "ONLY OUTPUT THIS JSON FORMAT:\n"
                '{"questions": [{"id": 1, "text": "First question"}, {"id": 2, "text": "Second question"}, {"id": 3, "text": "Third question"}]}'
            )
        elif attempt == 3:
            # Third attempt: one-step-at-a-time approach
            prompt = (
                f"Legal query: '{user_query}'\n\n"
                "Step 1: Think of 3 specific legal questions that would help clarify the situation.\n"
                "Step 2: Format ONLY these 3 questions in this JSON structure:\n"
                '{"questions": [{"id": 1, "text": "Q1"}, {"id": 2, "text": "Q2"}, {"id": 3, "text": "Q3"}]}\n\n'
                "Output ONLY the JSON. Do not include any other text."
            )
        elif attempt == 4:
            # Fourth attempt: even simpler, with clear instructions
            prompt = (
                "Return 3 legal questions in JSON format. ONLY output valid JSON in this format:\n"
                '{"questions": [{"id": 1, "text": "Q1"}, {"id": 2, "text": "Q2"}, {"id": 3, "text": "Q3"}]}'
            )
        else:
            # Last attempt: extremely simple directive
            prompt = (
                '{"questions": [{"id": 1, "text": "When did this legal issue first arise?"}, '
                '{"id": 2, "text": "Do you have any documentation related to this matter?"}, '
                '{"id": 3, "text": "Have you consulted with any legal professionals before?"}]}'
            )
            
        print(f"Attempt {attempt} to generate questions...", file=sys.stderr)
        response = questions_agent.run(prompt)
        
        # Try to extract JSON
        try:
            # Look for JSON patterns
            if response.find('{') >= 0 and response.find('}') >= 0:
                start = response.find('{')
                end = response.rfind('}') + 1
                json_str = response[start:end]
                
                obj = json.loads(json_str)
                questions = [q["text"] for q in obj.get("questions", [])]
                
                # If we have 3 valid questions, we're done
                if len(questions) == 3:
                    print("Successfully generated questions!", file=sys.stderr)
                    return questions
                else:
                    print(f"Found {len(questions)} questions, but need exactly 3. Retrying...", file=sys.stderr)
            else:
                print("No JSON structure found in response. Retrying...", file=sys.stderr)
        except Exception as e:
            print(f"Error parsing JSON: {e}", file=sys.stderr)
    
    # Fallback questions if all attempts fail
    return [
        "When did this legal issue first arise and what steps have you taken so far?",
        "Do you have any contracts or documents related to this matter?",
        "Have you received any formal notices or been involved in any legal proceedings on this issue?"
    ]

def get_conversational_response(memory_data: dict, user_input: str) -> str:
    # Format the follow-up Q/A for better readability
    qa_formatted = ""
    for q, a in memory_data.get('followup_qa', {}).items():
        qa_formatted += f"Q: {q}\nA: {a}\n"

    # Add conversation history if it exists
    conversation_history = ""
    if "conversation_history" in memory_data:
        for entry in memory_data["conversation_history"]:
            conversation_history += f"User: {entry['user']}\nAssistant: {entry['assistant']}\n\n"

    prompt = (
        f"You are a Conversational Legal Assistant.\n\n"
        f"User's original query: '{memory_data.get('query', '')}'\n\n"
        f"Legal synthesis: {memory_data.get('synthesis_result', '')}\n\n"
        f"Lawyer recommendations: {memory_data.get('ranked_lawyers', '')}\n\n"
        f"Follow-up Q&A:\n{qa_formatted}\n\n"
        f"Previous conversation:\n{conversation_history}\n\n"
        f"User's current question: '{user_input}'\n\n"
        "Based on all this context, provide a helpful response to the user's current question. "
        "Remember to include appropriate disclaimers about not providing actual legal advice and "
        "recommending consultation with the suggested lawyers for professional guidance."
    )
    return conversational_agent.run(prompt)

def generate_consultation_summary(memory_data: dict, user_name: str) -> str:
    """Generate a personalized summary of the entire legal consultation."""
    # Format the follow-up Q/A
    qa_formatted = ""
    for q, a in memory_data.get('followup_qa', {}).items():
        qa_formatted += f"Q: {q}\nA: {a}\n"

    # Format conversation history
    conversation_history = ""
    if "conversation_history" in memory_data:
        for entry in memory_data["conversation_history"]:
            conversation_history += f"User: {entry['user']}\nAssistant: {entry['assistant']}\n\n"

    # Extract info from the memory
    original_query = memory_data.get('query', '')
    lawyers_info = memory_data.get('ranked_lawyers', '')
    
    # Try to extract lawyer names from the JSON if possible
    lawyer_names = []
    try:
        json_data = extract_json_from_text(lawyers_info)
        if "lawyers" in json_data:
            for lawyer in json_data["lawyers"]:
                if "Name" in lawyer:
                    lawyer_names.append(lawyer["Name"])
    except Exception as e:
        print(f"Error extracting lawyer names: {e}")
            
    prompt = (
        f"You are the Legal Consultation Summary Agent.\n\n"
        f"User's name: {user_name}\n\n"
        f"Original legal query: '{original_query}'\n\n"
        f"Legal analysis: {memory_data.get('synthesis_result', '')}\n\n"
        f"Recommended lawyers: {lawyers_info}\n\n"
        f"Legal Q&A:\n{qa_formatted}\n\n"
        f"Additional conversation:\n{conversation_history}\n\n"
        f"Create a personalized summary for {user_name} that recaps their legal concerns, "
        f"the lawyers recommended to them, and key points from the consultation. "
        f"Start with 'Hey {user_name}!' and make it warm and professional. "
        f"Keep it to 3-4 sentences and end by emphasizing the importance of consulting with a qualified attorney for proper legal advice."
    )
    
    summary = summary_agent.run(prompt)
    return summary

def cleanup():
    """Ensure graceful shutdown of any active sessions (if required)."""
    try:
        print("Cleaning up resources...")
    except Exception as e:
        print(f"Error shutting down resources: {e}", file=sys.stderr)

# Register cleanup function to run when the script exits
atexit.register(cleanup)

########################################################################
# 7. MAIN PROCESSING FUNCTION
########################################################################

def process_legal_query(user_query: str, df_embeddings, user_info=None):
    """
    Process a legal query and store results.
    """
    memory_data = {"query": user_query}
    if user_info:
        memory_data["user_info"] = user_info
    
    # Step 1: Run synthesis agent first
    print("Generating legal synthesis...")
    synthesis_result = synthesize_information(user_query)
    memory_data["synthesis_result"] = synthesis_result
    print("\n--- Synthesis Result ---")
    print(synthesis_result)
    
    # Step 2: Generate follow-up questions
    print("\nGenerating follow-up questions...")
    questions_list = generate_followup_questions(user_query)
    
    # Step 3: Collect answers to questions
    print("\n--- Follow-up Questions ---")
    qa_pairs = {}
    for i, question in enumerate(questions_list, start=1):
        print(f"Q{i}: {question}")
        answer = input("Your answer: ")
        qa_pairs[question] = answer
    memory_data["followup_qa"] = qa_pairs
    
    # Step 4: Now proceed with RAG and lawyer ranking
    print("\nRetrieving and ranking relevant lawyers...")
    synthesis_emb = embed_text_with_gemini(synthesis_result)
    retrieved_lawyers = retrieve_relevant_lawyers(synthesis_emb, df_embeddings, top_k=10)
    ranked_lawyers_str = rank_top_lawyers(synthesis_result, retrieved_lawyers)
    memory_data["ranked_lawyers"] = ranked_lawyers_str
    
    # Try to parse the lawyer data immediately for better structure
    try:
        json_data = extract_json_from_text(ranked_lawyers_str)
        memory_data["lawyers_json"] = json_data
    except Exception as e:
        print(f"Warning: Could not parse lawyer ranking response: {e}")
        memory_data["lawyers_json"] = {"raw_text": ranked_lawyers_str}
    
    print("\n--- Ranked Lawyers (Structured JSON) ---")
    print(ranked_lawyers_str)
    
    # Initialize conversation history
    memory_data["conversation_history"] = []
    
    return memory_data
def main():
    """Main function that handles all execution modes: interactive, server first phase, and server second phase."""
    # Print startup information
    print("Starting legal process script...", file=sys.stderr)
    print(f"Arguments received: {sys.argv}", file=sys.stderr)
    
    # Check if we're in server integration mode (API mode) or interactive mode
    if len(sys.argv) > 1 and sys.argv[1] != "--interactive":
        # SERVER INTEGRATION MODE
        
        # First phase: Generate synthesis and questions only
        if len(sys.argv) == 2:  
            user_query = sys.argv[1]
            
            # Try to find the embeddings file
            try:
                embeddings_path = find_embeddings_file()
            except FileNotFoundError as e:
                print(json.dumps({"error": str(e)}))
                sys.exit(1)
            
            try:
                df_embeddings = load_lawyer_embeddings(embeddings_path)
                
                # Generate synthesis and questions
                print("Generating legal synthesis...", file=sys.stderr)
                synthesis_result = synthesize_information(user_query)
                print("Generating follow-up questions...", file=sys.stderr)
                questions_list = generate_followup_questions(user_query)
                
                # Return JSON result for the server
                result = {
                    "synthesis": synthesis_result,
                    "questions": questions_list
                }
                print(json.dumps(result))
            except Exception as e:
                print(json.dumps({"error": f"Error processing query: {str(e)}"}))
                sys.exit(1)
            
        # Second phase: Process answers and rank lawyers
        elif len(sys.argv) > 2:  
            user_query = sys.argv[1]
            
            # Check if second argument is answers_file or user_id
            second_arg = sys.argv[2]
            
            # Determine if we're in MongoDB mode or just lawyer ranking mode
            user_id = None
            user_name = "user"
            answers_file = None
            
            # If second argument is a file path, it's answers_file
            if os.path.isfile(second_arg):
                answers_file = second_arg
            else:
                # Otherwise, treat it as user_id for MongoDB integration
                user_id = second_arg
                # If user_id provided, fetch user info
                if user_id and MONGODB_AVAILABLE:
                    try:
                        skillseeker = connect_to_db()
                        if skillseeker:
                            user = skillseeker.find_one({"_id": ObjectId(user_id)})
                            if user:
                                user_name = user.get("Name", "user")
                    except Exception as e:
                        print(f"Error fetching user information: {e}", file=sys.stderr)
                
                # Check if there's a third argument for answers file
                if len(sys.argv) > 3:
                    answers_file = sys.argv[3]
            
            # Read answers from file if provided
            answers = []
            if answers_file and os.path.isfile(answers_file):
                try:
                    with open(answers_file, 'r') as f:
                        answers = json.load(f)
                        print(f"Successfully loaded answers: {answers}", file=sys.stderr)
                except Exception as e:
                    print(json.dumps({"error": f"Failed to read answers file: {str(e)}"}))
                    sys.exit(1)
            
            # Try to find the embeddings file
            try:
                embeddings_path = find_embeddings_file()
            except FileNotFoundError as e:
                print(json.dumps({"error": str(e)}))
                sys.exit(1)
            
            try:
                df_embeddings = load_lawyer_embeddings(embeddings_path)
                
                # Generate memory data for ranking lawyers
                memory_data = {"query": user_query}
                if user_id:
                    memory_data["user_info"] = {"name": user_name, "id": user_id}
                
                # Get synthesis result again
                print("Regenerating synthesis...", file=sys.stderr)
                synthesis_result = synthesize_information(user_query)
                memory_data["synthesis_result"] = synthesis_result
                
                # Generate questions again
                print("Regenerating questions for context...", file=sys.stderr)
                questions_list = generate_followup_questions(user_query)
                
                # Build QA pairs from provided answers
                qa_pairs = {}
                for i, question in enumerate(questions_list):
                    if i < len(answers):
                        qa_pairs[question] = answers[i]
                    else:
                        qa_pairs[question] = "No answer provided"
                
                memory_data["followup_qa"] = qa_pairs
                
                # Now proceed with RAG and lawyer ranking
                print("Retrieving and ranking relevant lawyers...", file=sys.stderr)
                synthesis_emb = embed_text_with_gemini(synthesis_result)
                retrieved_lawyers = retrieve_relevant_lawyers(synthesis_emb, df_embeddings, top_k=10)
                ranked_lawyers_str = rank_top_lawyers(synthesis_result, retrieved_lawyers)
                memory_data["ranked_lawyers"] = ranked_lawyers_str
                
                # Parse to get structured data
                try:
                    # Extract JSON part from the response if needed
                    if ranked_lawyers_str.find('{') >= 0 and ranked_lawyers_str.find('}') >= 0:
                        start = ranked_lawyers_str.find('{')
                        end = ranked_lawyers_str.rfind('}') + 1
                        json_str = ranked_lawyers_str[start:end]
                    else:
                        json_str = ranked_lawyers_str
                    
                    ranked_lawyers = json.loads(json_str)
                    memory_data["lawyers_json"] = ranked_lawyers
                    
                    # Handle different possible keys in the JSON response
                    if "lawyers" not in ranked_lawyers:
                        print("Warning: 'lawyers' key not found, checking for alternative keys", file=sys.stderr)
                        # Check for 'Top Lawyers' key
                        if "Top Lawyers" in ranked_lawyers:
                            print("Found 'Top Lawyers' key, using this data", file=sys.stderr)
                            ranked_lawyers = {"lawyers": ranked_lawyers["Top Lawyers"]}
                        # If it's a direct array
                        elif isinstance(ranked_lawyers, list):
                            print("Found array structure, wrapping in lawyers array", file=sys.stderr)
                            ranked_lawyers = {"lawyers": ranked_lawyers}
                        # If it's a single lawyer object
                        else:
                            # Check if any field looks like a lawyer
                            if any(key in ranked_lawyers for key in ["Name", "Category", "Skills"]):
                                print("Found single lawyer object, wrapping in array", file=sys.stderr)
                                ranked_lawyers = {"lawyers": [ranked_lawyers]}
                            else:
                                print("No recognizable lawyer data found, creating empty array", file=sys.stderr)
                                ranked_lawyers = {"lawyers": []}
                    
                    result = {
                        "status": "results",
                        "lawyers": ranked_lawyers.get("lawyers", [])
                    }
                    
                    # If we have a user_id, generate a summary and save to MongoDB
                    if user_id:
                        print("\nGenerating consultation summary...", file=sys.stderr)
                        summary = generate_consultation_summary(memory_data, user_name)
                        result["summary"] = summary
                        
                        # Save data locally and upload to MongoDB
                        try:
                            # Get the parsed lawyer data from memory
                            lawyer_data = memory_data.get("lawyers_json", {})
                            
                            # Save to local JSON file first
                            json_file = save_data_to_json_file(user_id, lawyer_data, summary)
                            
                            if json_file:
                                print("\nAttempting to upload data to MongoDB...", file=sys.stderr)
                                
                                # Try to upload to MongoDB if available
                                if MONGODB_AVAILABLE:
                                    # Try to upload to MongoDB
                                    success = upload_legal_data_to_mongodb(user_id, json_file)
                                    
                                    if success:
                                        print("Data successfully saved to MongoDB!", file=sys.stderr)
                                        result["mongodb_status"] = "success"
                                    else:
                                        print("Failed to upload to MongoDB, but data is safely stored locally in JSON file.", file=sys.stderr)
                                        result["mongodb_status"] = "local_only"
                                        result["local_file"] = json_file
                                else:
                                    print("MongoDB not available, data stored locally in JSON file.", file=sys.stderr)
                                    result["mongodb_status"] = "mongodb_disabled"
                                    result["local_file"] = json_file
                            else:
                                print("Failed to save data locally.", file=sys.stderr)
                                result["mongodb_status"] = "failed"
                        except Exception as e:
                            print(f"Error during data save process: {e}", file=sys.stderr)
                            result["mongodb_status"] = "error"
                            result["error_message"] = str(e)
                    
                    # Output the final JSON result
                    print(json.dumps(result))
                except Exception as e:
                    print(f"Failed to parse lawyer rankings: {str(e)}", file=sys.stderr)
                    print(f"Raw lawyer output was: {ranked_lawyers_str}", file=sys.stderr)
                    print(json.dumps({"error": f"Parsing error: {str(e)}"}))
                    sys.exit(1)
            except Exception as e:
                print(json.dumps({"error": f"Error processing answers: {str(e)}"}))
                sys.exit(1)
    
    else:
        # INTERACTIVE MODE
        # Check for user ID in CLI mode
        user_id = None
        user_name = "user"
        if len(sys.argv) > 2 and sys.argv[1] == "--interactive":
            user_id = sys.argv[2]
            # If user_id provided, fetch user info
            if user_id and MONGODB_AVAILABLE:
                try:
                    skillseeker = connect_to_db()
                    if skillseeker:
                        user = skillseeker.find_one({"_id": ObjectId(user_id)})
                        if user:
                            user_name = user.get("Name", "user")
                except Exception as e:
                    print(f"Error fetching user information: {e}")
        
        # Try to find the embeddings file
        try:
            embeddings_path = find_embeddings_file()
        except FileNotFoundError as e:
            # Fallback to the original path
            current_dir = get_script_directory()
            embeddings_path = os.path.join(current_dir, "lawyer_embeddings.pkl")
            if not os.path.exists(embeddings_path):
                print(f"Error: Embeddings file not found at {embeddings_path}")
                sys.exit(1)
        
        print("Loading lawyer database...")
        df_embeddings = load_lawyer_embeddings(embeddings_path)
        
        user_query = input("\nPlease describe your legal concern: ").strip()
        
        if not user_query:
            print("No input provided. Exiting.")
            return

        # Process the legal query with interactive flow
        memory_data = process_legal_query(user_query, df_embeddings, {"name": user_name, "id": user_id})
        
        # Display ranked lawyers in a more readable format
        try:
            lawyers_json = memory_data.get("lawyers_json", {})
            print("\n--- Top Recommended Lawyers ---")
            for i, lawyer in enumerate(lawyers_json.get("lawyers", []), start=1):
                print(f"\nLawyer {i}: {lawyer.get('Name', 'Unknown')}")
                print(f"Address: {lawyer.get('Address', 'Not specified')}")
                print(f"City: {lawyer.get('City', 'Not specified')}")
                print(f"Category: {lawyer.get('Category', 'Not specified')}")
        except:
            # If parsing fails, just show the raw output
            pass
        
        # Continue conversation for follow-up questions
        print("\n--- Legal Consultation Mode ---")
        print("You can now ask follow-up questions about your legal situation or the recommended lawyers.")
        print("Type 'exit' to end the consultation.")
        
        while True:
            user_input = input("\nAsk a follow-up question: ").strip()
            if user_input.lower() == "exit":
                # Generate summary before exiting
                print("\nGenerating consultation summary...")
                summary = generate_consultation_summary(memory_data, user_name)
                print("\n--- Legal Consultation Summary ---")
                print(summary)
                
                # Save data locally and then try to upload to MongoDB
                if user_id:
                    try:
                        # Get the parsed lawyer data from memory if available
                        lawyer_data = memory_data.get("lawyers_json", {})
                        
                        # Save to local JSON file first
                        json_file = save_data_to_json_file(user_id, lawyer_data, summary)
                        
                        if json_file:
                            print("\nAttempting to upload data to MongoDB...")
                            
                            # Try to upload to MongoDB if available
                            if MONGODB_AVAILABLE:
                                success = upload_legal_data_to_mongodb(user_id, json_file)
                                
                                if success:
                                    print("Data successfully saved to MongoDB!")
                                else:
                                    print("Failed to upload to MongoDB, but data is safely stored locally in JSON file.")
                            else:
                                print("MongoDB not available, data stored locally in JSON file.")
                        else:
                            print("Failed to save data locally.")
                    except Exception as e:
                        print(f"Error during data save process: {e}")
                
                print("Thank you for using our legal assistant. Remember that this tool does not replace professional legal advice.")
                break
            
            # Get response and update conversation history
            response = get_conversational_response(memory_data, user_input)
            print("\n--- Legal Guidance ---")
            print(response)
            
            # Add to conversation history
            memory_data["conversation_history"].append({
                "user": user_input,
                "assistant": response
            })

# Main execution entry point
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # Determine if we're in server mode
        is_server_mode = len(sys.argv) > 1 and sys.argv[1] != "--interactive"
        
        if is_server_mode:
            # Return error as JSON for server mode
            error_msg = {"error": f"Unexpected error: {str(e)}"}
            print(json.dumps(error_msg))
            print(f"Exception occurred: {str(e)}", file=sys.stderr)
        else:
            # Regular error output for interactive mode
            print(f"Error: {str(e)}")
        
        # Print traceback in either case to stderr
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)