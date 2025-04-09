import os
import sys
import pickle
import json
import numpy as np
import re
import google.generativeai as genai
import atexit
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
# 1. LOCAL FILE AND MONGODB CONNECTION
########################################################################

def save_data_to_json_file(user_id, doctor_data, summary_text):
    """Save data to a local JSON file for debugging and backup purposes."""
    try:
        # Parse doctor_data to ensure it's a proper object, not a string
        if isinstance(doctor_data, str):
            # Try to parse it first as regular JSON
            try:
                parsed_doctor_data = json.loads(doctor_data)
            except json.JSONDecodeError:
                # If that fails, try to extract JSON from markdown code blocks
                # This regex finds content inside ```json and ``` markers
                code_block_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', doctor_data)
                if code_block_match:
                    json_content = code_block_match.group(1).strip()
                    parsed_doctor_data = json.loads(json_content)
                else:
                    # If no code block, just use the string as is
                    parsed_doctor_data = {"raw_data": doctor_data}
        else:
            parsed_doctor_data = doctor_data
            
        # Create data structure
        data = {
            "user_id": str(user_id),
            "timestamp": datetime.now().strftime("%Y-%m-%d_%H-%M-%S"),
            "doctor_data": parsed_doctor_data,
            "summary": summary_text
        }
        
        # Create filename with timestamp for uniqueness
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data_{user_id}_{timestamp}.json"
        
        # Save to file
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
            
        print(f"Data successfully saved to local file: {filename}")
        return filename
    except Exception as e:
        print(f"Error saving to local JSON file: {e}")
        return None

def connect_to_db():
    """Connect to MongoDB database and return the skillseeker collection."""
    uri = "mongodb+srv://shayanarsalan2003:Shayan717@cluster0.ocn53.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    client = MongoClient(uri, server_api=ServerApi('1'))
    db = client["Cluster0"]
    skillseeker = db["skillseeker"]
    return skillseeker

def upload_data_to_mongodb(user_id, json_file_path):
    """Upload data from local JSON file to MongoDB."""
    try:
        # Read the JSON file
        with open(json_file_path, 'r') as f:
            data = json.load(f)
        
        # Parse the doctor data
        doctor_data = data.get("doctor_data", {})
            
        # Extract doctor information
        doctor_names = []
        education = []
        expertise = []
        contact_numbers = []
        
        # Check if doctor_data is an array directly or inside a doctors key
        doctors_array = None
        if isinstance(doctor_data, list):
            doctors_array = doctor_data
        elif isinstance(doctor_data, dict) and "doctors" in doctor_data:
            doctors_array = doctor_data.get("doctors", [])
        else:
            print(f"Warning: Unexpected doctor data format: {type(doctor_data)}")
            print(f"Doctor data content (sample): {str(doctor_data)[:200]}...")
            doctors_array = []
            
        # Process each doctor
        for doctor in doctors_array:
            if isinstance(doctor, dict):
                doctor_names.append(doctor.get("Doctor Name", ""))
                education.append(doctor.get("Education", ""))
                expertise.append(doctor.get("Expertise", "").strip())
                contact_numbers.append(doctor.get("Contact Number", ""))
        
        # Create conversation entry
        conversation_entry = {
            "query": "medical_summary",
            "response": data.get("summary", "")
        }
        
        # Connect to database
        skillseeker = connect_to_db()
        user_id_obj = ObjectId(user_id)
        
        # Debug info
        print(f"Processing {len(doctors_array)} doctors")
        print(f"Doctor names: {doctor_names}")
        print(f"Education: {education}")
        print(f"Expertise: {expertise}")
        print(f"Contact numbers: {contact_numbers}")
        
        # Build update operation
        update = {
            "$set": {
                "DoctorNames": doctor_names,
                "Education": education, 
                "Expertise": expertise,
                "ContactNumbers": contact_numbers,
                "Conversation": [conversation_entry]
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
            print(f"Data successfully uploaded to MongoDB from file {json_file_path}")
            return True
            
    except Exception as e:
        print(f"Error uploading data to MongoDB: {e}")
        return False

########################################################################
# 2. GEMINI CONFIGURATION
########################################################################

genai.configure(api_key="AIzaSyCohbQG3sbkCf1LLbf1spVXFAgzjsRU1xA")

generation_config = {
    "temperature": 0.2,  # Very low temperature for reliable JSON output
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
    role="Medical Information Synthesis",
    goal="Produce a brief medical query analysis.",
    backstory=(
        "Based solely on the user's query, generate a concise three-line paragraph. "
        "It should include one recommended doctor's name who can address the problem and a brief explanation of the likely condition."
    ),
    allow_delegation=False,
    verbose=False,
    llm=model,
    expected_output="A short 3-line paragraph with one recommended doctor's name and a brief explanation."
)

# Ranking Agent: Selects the top 3 doctors and outputs their details in strict JSON.
ranking_agent = Agent(
    role="Doctor Ranking Agent",
    goal="Select the top 3 doctors and output their details in strict JSON format.",
    backstory=(
        "You have a set of doctor profiles. Based on the synthesis result and the retrieved profiles, "
        "select the top 3 most relevant doctors. Return the output in strict JSON format containing only the keys: "
        "'Doctor Name', 'Education', 'Expertise', 'Contact Number', 'Qualifications', 'Clinic Names', and 'Locations'."
    ),
    allow_delegation=False,
    verbose=False,
    llm=model,
    expected_output=(
        '{"doctors": ['
        '{"Doctor Name": "...", "Education": "...", "Expertise": "...", "Contact Number": "...", '
        '"Qualifications": "...", "Clinic Names": [...], "Locations": [...]}, '
        '{"Doctor Name": "...", "Education": "...", "Expertise": "...", "Contact Number": "...", '
        '"Qualifications": "...", "Clinic Names": [...], "Locations": [...]}, '
        '{"Doctor Name": "...", "Education": "...", "Expertise": "...", "Contact Number": "...", '
        '"Qualifications": "...", "Clinic Names": [...], "Locations": [...]}'
        ']}'
    )
)

# Questions Agent: Generates 3 clarifying questions in strict JSON.
questions_agent = Agent(
    role="Medical Follow-up Questions Generator",
    goal="Generate 3 specific clarifying questions to further diagnose the medical query.",
    backstory=(
        "Based solely on the user's query, generate 3 specific clarifying questions that address details such as pain location, "
        "severity, duration, and any associated symptoms. Questions should be specific and medically relevant.\n\n"
        "Examples of good specific questions:\n"
        "'Where exactly do you feel the pain and how would you rate it on a scale of 1-10?',\n"
        "'How long have you been experiencing these symptoms and have they changed over time?',\n"
        "'Have you tried any medications or treatments for this condition already?'\n\n"
        "Return ONLY the following JSON format with no additional text:"
    ),
    allow_delegation=False,
    verbose=False,
    llm=model,
    expected_output='{"questions": [{"id": 1, "text": "Where exactly do you feel the pain and how would you rate it on a scale of 1-10?"}, {"id": 2, "text": "How long have you been experiencing these symptoms and have they changed over time?"}, {"id": 3, "text": "Have you tried any medications or treatments for this condition already?"}]}'
)

# Conversational Agent: Provides additional explanation using full context.
conversational_agent = Agent(
    role="Conversational Medical Assistant",
    goal="Provide comprehensive medical guidance based on all available context.",
    backstory=(
        "Access the full context—including the original query, synthesis, ranked doctors, and follow-up Q/A—and provide a detailed explanation or further recommendations."
    ),
    allow_delegation=False,
    verbose=False,
    llm=model,
    expected_output="A detailed explanation referencing the full context."
)

# Summary Agent - Creates a personalized summary when conversation ends
summary_agent = Agent(
    role="Conversation Summary Agent",
    goal="Create a personalized summary of the entire medical consultation.",
    backstory=(
        "You create friendly, personalized summaries of medical consultations. "
        "Your summaries address the user by name and reference specific details from their conversation, "
        "including their medical concerns, the recommended doctors, and main points from the follow-up discussion. "
        "The tone is warm and helpful, offering to continue assisting with their medical needs."
    ),
    allow_delegation=False,
    verbose=False,
    llm=model,
    expected_output=(
        "Hey [Name]! Based on our previous conversation, I remember you wanted medical doctors for your [specific condition], "
        "and we identified Dr. [Name] as potentially helpful for your situation. You can either ask for new professionals "
        "or keep looking for medical individuals for your needs!"
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
        os.path.join(get_script_directory(), "doctors_embeddings.pkl"),  # Same directory as script
        os.path.join(get_script_directory(), "..", "doctors_embeddings.pkl"),  # Parent directory
        os.path.join(get_script_directory(), "..", "backend", "doctors_embeddings.pkl"),  # Backend directory
        os.path.abspath("backend/doctors_embeddings.pkl"),  # Absolute path from working directory
        os.path.abspath("doctors_embeddings.pkl")  # Directly in working directory
    ]
    
    for path in potential_paths:
        if os.path.exists(path):
            print(f"Found embeddings file at: {path}", file=sys.stderr)
            return path
    
    # If we get here, we couldn't find the file
    print(f"Searched for embeddings in: {potential_paths}", file=sys.stderr)
    raise FileNotFoundError("Could not find doctors_embeddings.pkl in any expected location")

def load_doctor_embeddings(pkl_path: str):
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

def retrieve_relevant_doctors(query_embedding, df, top_k=10):
    similarities = []
    for idx, row in df.iterrows():
        doc_emb = row['embedding']
        sim = cosine_similarity(query_embedding, doc_emb)
        similarities.append((idx, sim))
    similarities.sort(key=lambda x: x[1], reverse=True)
    top_indices = [x[0] for x in similarities[:top_k]]
    return df.iloc[top_indices]

########################################################################
# 6. ORCHESTRATION FUNCTIONS
########################################################################

def synthesize_information(user_query: str) -> str:
    prompt = (
        f"You are the synthesis agent.\n"
        f"User's original query:\n{user_query}\n\n"
        "Generate a concise three-line paragraph that includes one recommended doctor's name who can address the problem and a brief explanation of the likely condition."
    )
    return synthesis_agent.run(prompt)

def rank_top_doctors(synthesis_text: str, retrieved_df) -> str:
    docs_text = []
    for idx, row in retrieved_df.iterrows():
        docs_text.append(row['doctor_profile'])
    joined_docs = "\n\n".join(docs_text)
    prompt = (
        f"You are the Doctor Ranking Agent.\n\n"
        f"Synthesis of user's situation:\n{synthesis_text}\n\n"
        f"Here are 10 potentially relevant doctor profiles:\n\n{joined_docs}\n\n"
        "Based exclusively on the above synthesis and profiles, select the top 3 doctors most suitable for the user's needs. "
        "Return the output in strict JSON format with the following structure:\n"
        '{"doctors": [\n'
        '  {"Doctor Name": "...", "Education": "...", "Expertise": "...", "Contact Number": "...", '
        '"Qualifications": "...", "Clinic Names": [...], "Locations": [...]},\n'
        '  {"Doctor Name": "...", "Education": "...", "Expertise": "...", "Contact Number": "...", '
        '"Qualifications": "...", "Clinic Names": [...], "Locations": [...]},\n'
        '  {"Doctor Name": "...", "Education": "...", "Expertise": "...", "Contact Number": "...", '
        '"Qualifications": "...", "Clinic Names": [...], "Locations": [...]}\n'
        ']}'
        "Your response must begin with '{' and be valid JSON."
    )
    result = ranking_agent.run(prompt)
    print(f"Debug - Raw ranked doctors result: {result}", file=sys.stderr)
    return result

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

def generate_followup_questions(user_query: str) -> list:
    """
    Generate 3 follow-up questions using multiple retries if needed.
    This function tries different prompting approaches to get valid JSON.
    """
    max_attempts = 5  # Increased number of attempts
    questions = []
    
    for attempt in range(1, max_attempts + 1):
        # Different prompting strategies for different attempts
        if attempt == 1:
            # First attempt: standard approach with expected format
            prompt = (
                f"You are a medical professional tasked with generating follow-up questions.\n\n"
                f"User's medical query: '{user_query}'\n\n"
                "Generate exactly 3 specific medical follow-up questions that would help diagnose this condition.\n\n"
                "You MUST format your response as a valid JSON object using EXACTLY this structure:\n"
                '{"questions": [{"id": 1, "text": "your first question here"}, {"id": 2, "text": "your second question here"}, {"id": 3, "text": "your third question here"}]}\n\n'
                "Do not include any text outside the JSON structure. Your entire response must be a single valid JSON object.\n\n"
                "Example of correct JSON format:\n"
                '{"questions": [{"id": 1, "text": "Where exactly do you feel the pain and how would you rate it on a scale of 1-10?"}, {"id": 2, "text": "How long have you been experiencing these symptoms and have they changed over time?"}, {"id": 3, "text": "Have you tried any medications or treatments for this condition already?"}]}'
            )
        elif attempt == 2:
            # Second attempt: more direct, simpler prompt
            prompt = (
                f"Based on this medical query: '{user_query}'\n\n"
                "Your task is to output exactly 3 clarifying medical questions in STRICT JSON format.\n\n"
                "ONLY OUTPUT THIS JSON FORMAT:\n"
                '{"questions": [{"id": 1, "text": "First question"}, {"id": 2, "text": "Second question"}, {"id": 3, "text": "Third question"}]}'
            )
        elif attempt == 3:
            # Third attempt: one-step-at-a-time approach
            prompt = (
                f"Medical query: '{user_query}'\n\n"
                "Step 1: Think of 3 specific medical questions that would help clarify the condition.\n"
                "Step 2: Format ONLY these 3 questions in this JSON structure:\n"
                '{"questions": [{"id": 1, "text": "Q1"}, {"id": 2, "text": "Q2"}, {"id": 3, "text": "Q3"}]}\n\n'
                "Output ONLY the JSON. Do not include any other text."
            )
        elif attempt == 4:
            # Fourth attempt: even simpler, with clear instructions
            prompt = (
                "Return 3 medical questions in JSON format. ONLY output valid JSON in this format:\n"
                '{"questions": [{"id": 1, "text": "Q1"}, {"id": 2, "text": "Q2"}, {"id": 3, "text": "Q3"}]}'
            )
        else:
            # Last attempt: extremely simple directive
            prompt = (
                '{"questions": [{"id": 1, "text": "Where is your pain located?"}, '
                '{"id": 2, "text": "How long have you had these symptoms?"}, '
                '{"id": 3, "text": "What makes it better or worse?"}]}'
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
        "Where is your pain located and how would you rate it on a scale of 1-10?",
        "How long have you been experiencing these symptoms?",
        "Have you tried any medications or treatments already?"
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
        f"You are a Conversational Medical Assistant.\n\n"
        f"User's original query: '{memory_data.get('query', '')}'\n\n"
        f"Medical synthesis: {memory_data.get('synthesis_result', '')}\n\n"
        f"Doctor recommendations: {memory_data.get('ranked_doctors', '')}\n\n"
        f"Follow-up Q&A:\n{qa_formatted}\n\n"
        f"Previous conversation:\n{conversation_history}\n\n"
        f"User's current question: '{user_input}'\n\n"
        "Based on all this context, provide a helpful response to the user's current question."
    )
    return conversational_agent.run(prompt)

def generate_conversation_summary(memory_data: dict, user_name: str) -> str:
    """Generate a personalized summary of the entire medical consultation."""
    # Format the follow-up Q/A
    qa_formatted = ""
    for q, a in memory_data.get('followup_qa', {}).items():
        qa_formatted += f"Q: {q}\nA: {a}\n"

    # Format conversation history
    conversation_history = ""
    if "conversation_history" in memory_data:
        for entry in memory_data["conversation_history"]:
            conversation_history += f"User: {entry['user']}\nAssistant: {entry['assistant']}\n\n"

    # Extract condition and doctor name for better summary
    original_query = memory_data.get('query', '')
    doctor_info = memory_data.get('ranked_doctors', '')
    
    # Try to extract doctor names from the JSON if possible
    doctor_names = []
    try:
        json_data = extract_json_from_text(doctor_info)
        if "doctors" in json_data:
            for doc in json_data["doctors"]:
                if "Doctor Name" in doc:
                    doctor_names.append(doc["Doctor Name"])
    except Exception as e:
        print(f"Error extracting doctor names: {e}")
            
    prompt = (
        f"You are the Conversation Summary Agent.\n\n"
        f"User's name: {user_name}\n\n"
        f"Original medical query: '{original_query}'\n\n"
        f"Medical synthesis: {memory_data.get('synthesis_result', '')}\n\n"
        f"Doctor recommendations: {doctor_info}\n\n"
        f"Follow-up Q&A:\n{qa_formatted}\n\n"
        f"Additional conversation:\n{conversation_history}\n\n"
        f"Create a personalized summary for {user_name} that recaps their medical concerns, "
        f"the doctors recommended to them, and key points from the follow-up discussion. "
        f"Start with 'Hey {user_name}!' and make it warm and personal. "
        f"Keep it to 3-4 sentences and end by offering to help further with their medical needs."
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
# 7. MAIN PROCESSING FUNCTION - COMPLETELY RESTRUCTURED
########################################################################

def process_medical_query(user_query: str, df_embeddings, user_info=None):
    """
    Restructured to guarantee the question generation step runs in the correct sequence.
    """
    memory_data = {"query": user_query}
    if user_info:
        memory_data["user_info"] = user_info
    
    # Step 1: Run synthesis agent first
    print("Generating medical synthesis...")
    synthesis_result = synthesize_information(user_query)
    memory_data["synthesis_result"] = synthesis_result
    print("\n--- Synthesis Result ---")
    print(synthesis_result)
    
    # Step 2: Generate follow-up questions (moved earlier in the process)
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
    
    # Step 4: Now proceed with RAG and doctor ranking
    print("\nRetrieving and ranking relevant doctors...")
    synthesis_emb = embed_text_with_gemini(synthesis_result)
    retrieved_doctors = retrieve_relevant_doctors(synthesis_emb, df_embeddings, top_k=10)
    ranked_doctors_str = rank_top_doctors(synthesis_result, retrieved_doctors)
    memory_data["ranked_doctors"] = ranked_doctors_str
    
    # Try to parse the doctor data immediately for better structure
    try:
        json_data = extract_json_from_text(ranked_doctors_str)
        memory_data["doctors_json"] = json_data
    except Exception as e:
        print(f"Warning: Could not parse doctor ranking response: {e}")
        memory_data["doctors_json"] = {"raw_text": ranked_doctors_str}
    
    print("\n--- Ranked Doctors (Structured JSON) ---")
    print(ranked_doctors_str)
    
    # Initialize conversation history
    memory_data["conversation_history"] = []
    
    return memory_data

########################################################################
# 8. MAIN EXECUTION WITH SERVER INTEGRATION
########################################################################

def main():
    # Check if we're in server integration mode or interactive mode
    if len(sys.argv) > 1:
        # Check if we're in question generation phase or answer processing phase
        if len(sys.argv) == 2:  # Just a query - first phase
            user_query = sys.argv[1]
            
            # Try to find the embeddings file
            try:
                embeddings_path = find_embeddings_file()
            except FileNotFoundError as e:
                print(json.dumps({"error": str(e)}))
                sys.exit(1)
            
            try:
                df_embeddings = load_doctor_embeddings(embeddings_path)
                
                # First phase: Generate synthesis and questions
                print("Generating medical synthesis...", file=sys.stderr)
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
            
        elif len(sys.argv) > 2:  # Query + second argument - second phase
            user_query = sys.argv[1]
            
            # Check if second argument is answers_file or user_id
            second_arg = sys.argv[2]
            
            # Determine if we're in MongoDB mode or just doctor ranking mode
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
                if user_id:
                    try:
                        skillseeker = connect_to_db()
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
                df_embeddings = load_doctor_embeddings(embeddings_path)
                
                # Generate memory data for ranking doctors
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
                
                # Now proceed with RAG and doctor ranking
                print("Retrieving and ranking relevant doctors...", file=sys.stderr)
                synthesis_emb = embed_text_with_gemini(synthesis_result)
                retrieved_doctors = retrieve_relevant_doctors(synthesis_emb, df_embeddings, top_k=10)
                ranked_doctors_str = rank_top_doctors(synthesis_result, retrieved_doctors)
                memory_data["ranked_doctors"] = ranked_doctors_str
                
                # Parse to get structured data
                try:
                    # Extract JSON part from the response if needed
                    if ranked_doctors_str.find('{') >= 0 and ranked_doctors_str.find('}') >= 0:
                        start = ranked_doctors_str.find('{')
                        end = ranked_doctors_str.rfind('}') + 1
                        json_str = ranked_doctors_str[start:end]
                    else:
                        json_str = ranked_doctors_str
                    
                    ranked_doctors = json.loads(json_str)
                    memory_data["doctors_json"] = ranked_doctors
                    
                    # Handle different possible keys in the JSON response
                    if "doctors" not in ranked_doctors:
                        print("Warning: 'doctors' key not found, checking for alternative keys", file=sys.stderr)
                        # Check for 'Top Doctors' key
                        if "Top Doctors" in ranked_doctors:
                            print("Found 'Top Doctors' key, using this data", file=sys.stderr)
                            ranked_doctors = {"doctors": ranked_doctors["Top Doctors"]}
                        # If it's a direct array
                        elif isinstance(ranked_doctors, list):
                            print("Found array structure, wrapping in doctors array", file=sys.stderr)
                            ranked_doctors = {"doctors": ranked_doctors}
                        # If it's a single doctor object
                        else:
                            # Check if any field looks like a doctor
                            if any(key in ranked_doctors for key in ["Doctor Name", "Name", "Expertise"]):
                                print("Found single doctor object, wrapping in array", file=sys.stderr)
                                ranked_doctors = {"doctors": [ranked_doctors]}
                            else:
                                print("No recognizable doctor data found, creating empty array", file=sys.stderr)
                                ranked_doctors = {"doctors": []}
                    
                    result = {
                        "status": "results",
                        "doctors": ranked_doctors.get("doctors", [])
                    }
                    
                    # If we have a user_id, generate a summary and save to MongoDB
                    if user_id:
                        print("\nGenerating consultation summary...", file=sys.stderr)
                        summary = generate_conversation_summary(memory_data, user_name)
                        result["summary"] = summary
                        
                        # Save data locally and upload to MongoDB
                        try:
                            # Get the parsed doctor data from memory
                            doctor_data = memory_data.get("doctors_json", {})
                            
                            # Save to local JSON file first
                            json_file = save_data_to_json_file(user_id, doctor_data, summary)
                            
                            if json_file:
                                print("\nAttempting to upload data to MongoDB...", file=sys.stderr)
                                # Try to upload to MongoDB
                                success = upload_data_to_mongodb(user_id, json_file)
                                
                                if success:
                                    print("Data successfully saved to MongoDB!", file=sys.stderr)
                                    result["mongodb_status"] = "success"
                                else:
                                    print("Failed to upload to MongoDB, but data is safely stored locally in JSON file.", file=sys.stderr)
                                    result["mongodb_status"] = "local_only"
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
                    print(f"Failed to parse doctor rankings: {str(e)}", file=sys.stderr)
                    print(f"Raw doctor output was: {ranked_doctors_str}", file=sys.stderr)
                    print(json.dumps({"error": f"Parsing error: {str(e)}"}))
                    sys.exit(1)
            except Exception as e:
                print(json.dumps({"error": f"Error processing answers: {str(e)}"}))
                sys.exit(1)
    
    else:
        # Check for user ID in CLI mode
        user_id = None
        user_name = "user"
        if len(sys.argv) > 1:
            user_id = sys.argv[1]
            # If user_id provided, fetch user info
            if user_id:
                try:
                    skillseeker = connect_to_db()
                    user = skillseeker.find_one({"_id": ObjectId(user_id)})
                    if user:
                        user_name = user.get("Name", "user")
                except Exception as e:
                    print(f"Error fetching user information: {e}")
        
        # Try to find the embeddings file
        try:
            embeddings_path = find_embeddings_file()
        except FileNotFoundError as e:
            print(f"Error: {e}")
            sys.exit(1)
        
        print("Loading doctor database...")
        df_embeddings = load_doctor_embeddings(embeddings_path)
        
        user_query = input("\nPlease describe your medical concern: ").strip()
        
        if not user_query:
            print("No input provided. Exiting.")
            return

        # Process the medical query with interactive flow
        memory_data = process_medical_query(user_query, df_embeddings, {"name": user_name, "id": user_id})
        
        # Continue conversation for follow-up questions
        print("\n--- Conversation Mode ---")
        print("You can now ask follow-up questions or type 'exit' to finish")
        
        while True:
            user_input = input("\nAsk a follow-up question: ").strip()
            if user_input.lower() == "exit":
                # Generate summary before exiting
                print("\nGenerating consultation summary...")
                summary = generate_conversation_summary(memory_data, user_name)
                print("\n--- Consultation Summary ---")
                print(summary)
                
                # Save data locally and then try to upload to MongoDB
                if user_id:
                    try:
                        # Get the parsed doctor data from memory if available
                        doctor_data = memory_data.get("doctors_json", {})
                        
                        # Save to local JSON file first
                        json_file = save_data_to_json_file(user_id, doctor_data, summary)
                        
                        if json_file:
                            print("\nAttempting to upload data to MongoDB...")
                            # Try to upload to MongoDB
                            success = upload_data_to_mongodb(user_id, json_file)
                            
                            if success:
                                print("Data successfully saved to MongoDB!")
                            else:
                                print("Failed to upload to MongoDB, but data is safely stored locally in JSON file.")
                        else:
                            print("Failed to save data locally.")
                    except Exception as e:
                        print(f"Error during data save process: {e}")
                
                print("Thank you for using our medical assistant.")
                break
            
            # Get response and update conversation history
            response = get_conversational_response(memory_data, user_input)
            print("\n--- Response ---")
            print(response)
            
            # Add to conversation history
            memory_data["conversation_history"].append({
                "user": user_input,
                "assistant": response
            })

# The code that calls the main function
if __name__ == "__main__":
    try:
        # Print error messages to stderr for easier debugging when in server mode
        print("Starting medical process script...", file=sys.stderr)
        print(f"Arguments received: {sys.argv}", file=sys.stderr)
        
        # Ensure clean JSON output in server mode
        main()
    except Exception as e:
        # Catch any unexpected errors and return them as JSON if in server mode
        if len(sys.argv) > 1 and not os.path.isfile(sys.argv[1]):
            error_msg = {
                "error": f"Unexpected error: {str(e)}"
            }
            print(json.dumps(error_msg))
            print(f"Exception occurred: {str(e)}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            sys.exit(1)
        else:
            # Regular error handling for interactive mode
            print(f"Error: {str(e)}")
            import traceback
            traceback.print_exc()
            sys.exit(1)