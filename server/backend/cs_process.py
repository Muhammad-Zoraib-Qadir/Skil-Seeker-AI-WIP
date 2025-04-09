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

def save_data_to_json_file(user_id, technical_experts_data, summary_text=None):
    """Save data to a local JSON file for debugging and backup purposes."""
    try:
        # Create a directory for output if it doesn't exist
        output_dir = "output"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # Parse technical_experts_data to ensure it's a proper object, not a string
        if isinstance(technical_experts_data, str):
            # Try to parse it first as regular JSON
            try:
                parsed_experts_data = json.loads(technical_experts_data)
            except json.JSONDecodeError:
                # If that fails, try to extract JSON from markdown code blocks
                code_block_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', technical_experts_data)
                if code_block_match:
                    json_content = code_block_match.group(1).strip()
                    try:
                        parsed_experts_data = json.loads(json_content)
                    except json.JSONDecodeError:
                        # If JSON parsing still fails, use as raw text
                        parsed_experts_data = {"raw_data": technical_experts_data}
                else:
                    # If no code block, just use the string as is
                    parsed_experts_data = {"raw_data": technical_experts_data}
        else:
            # If it's already a dict or other object, use it directly
            parsed_experts_data = technical_experts_data
            
        # Create data structure
        data = {
            "user_id": str(user_id),
            "timestamp": datetime.now().strftime("%Y-%m-%d_%H-%M-%S"),
            "technical_experts_data": parsed_experts_data,
            "summary": summary_text if summary_text else ""
        }
        
        # Create filename with timestamp for uniqueness
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"technical_data_{user_id}_{timestamp}.json"
        filepath = os.path.join(output_dir, filename)
        
        # Save to file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        print(f"Data successfully saved to local file: {filepath}")
        return filepath
    except Exception as e:
        print(f"Error saving to local JSON file: {e}")
        
        # Even if the function encounters an error, attempt a fallback save
        try:
            if not os.path.exists("output"):
                os.makedirs("output")
                
            fallback_path = os.path.join("output", f"fallback_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            with open(fallback_path, 'w', encoding='utf-8') as f:
                # Save a simplified version of the data
                simple_data = {
                    "user_id": str(user_id),
                    "timestamp": datetime.now().strftime("%Y-%m-%d_%H-%M-%S"),
                    "error": str(e),
                    "summary": summary_text if summary_text else "",
                    "raw_data": str(technical_experts_data)[:1000]  # Truncate to avoid potential issues
                }
                json.dump(simple_data, f, indent=2, ensure_ascii=False)
            print(f"Fallback data saved to: {fallback_path}")
            return fallback_path
        except Exception as fallback_error:
            print(f"Even fallback save failed: {fallback_error}")
            return None

def extract_json_from_text(text):
    """Extract JSON from a text that might contain markdown or other formatting."""
    if not text or not isinstance(text, str):
        return {"error": "Invalid input text", "raw_text": str(text)}
    
    # First, try to parse the text directly as JSON
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # If direct parsing fails, continue with extraction methods
        pass
    
    # Look for JSON inside code blocks
    code_block_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
    if code_block_match:
        json_text = code_block_match.group(1).strip()
        try:
            return json.loads(json_text)
        except json.JSONDecodeError:
            # If code block parsing fails, continue to next method
            pass
    
    # Look for JSON structure with more flexible pattern matching
    # Find the outermost braces
    brace_match = re.search(r'(\{[\s\S]*\})', text)
    if brace_match:
        json_text = brace_match.group(1).strip()
        try:
            return json.loads(json_text)
        except json.JSONDecodeError:
            # If outer brace parsing fails, try one more approach
            pass
    
    # Try to find any valid JSON object within the text using relaxed matching
    potential_json = ""
    open_braces = 0
    capture = False
    
    for char in text:
        if char == '{':
            open_braces += 1
            capture = True
            potential_json += char
        elif capture:
            potential_json += char
            if char == '{':
                open_braces += 1
            elif char == '}':
                open_braces -= 1
                if open_braces == 0:
                    # We potentially have a complete JSON object
                    try:
                        result = json.loads(potential_json)
                        return result  # Return the first valid JSON object we find
                    except json.JSONDecodeError:
                        # Reset and keep looking
                        potential_json = ""
                        capture = False
    
    # If we get here, we couldn't extract valid JSON, so return the text as raw data
    print(f"Warning: Could not parse JSON from text. First 100 chars: {text[:100]}...")
    return {"raw_text": text}

def upload_technical_data_to_mongodb(user_id, json_file_path):
    """
    Upload technical experts data from local JSON file to MongoDB.
    Uses the existing medical fields to store technical expert data.
    Also saves the conversation summary.
    """
    if not MONGODB_AVAILABLE:
        print("MongoDB features are disabled due to missing packages.")
        return False
        
    try:
        # Read the JSON file
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Parse the technical experts data
        experts_data = data.get("technical_experts_data", {})
        summary_text = data.get("summary", "")
            
        # Extract expert information to store in medical fields
        doctor_names = []  # Will store expert names
        education = []     # Will store ratings
        expertise = []     # Will store package prices
        contact_numbers = [] # Will store links
        
        # Check if experts_data is an array directly or inside a professionals key
        experts_array = None
        if isinstance(experts_data, list):
            experts_array = experts_data
        elif isinstance(experts_data, dict) and "professionals" in experts_data:
            experts_array = experts_data.get("professionals", [])
        else:
            print(f"Warning: Unexpected experts data format: {type(experts_data)}")
            print(f"Experts data content (sample): {str(experts_data)[:200]}...")
            experts_array = []
            
        # Process each expert
        for expert in experts_array:
            if isinstance(expert, dict):
                doctor_names.append(expert.get("Name", ""))  # Store expert name in DoctorNames
                education.append(expert.get("Rating", ""))  # Store rating in Education
                expertise.append(expert.get("Package Price", ""))  # Store package price in Expertise
                contact_numbers.append(expert.get("Link", ""))  # Store link in ContactNumbers
        
        # Connect to database
        skillseeker = connect_to_db()
        if not skillseeker:
            return False
            
        user_id_obj = ObjectId(user_id)
        
        # Debug info
        print(f"Processing {len(experts_array)} technical experts")
        print(f"Expert names (storing in DoctorNames): {doctor_names}")
        print(f"Ratings (storing in Education): {education}")
        print(f"Package prices (storing in Expertise): {expertise}")
        print(f"Links (storing in ContactNumbers): {contact_numbers}")
        
        # Create conversation entry for the summary
        conversation_entry = {
            "query": "technical_summary",
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
        
        # Then update with new technical expert data and conversation summary
        update = {
            "$set": {
                "DoctorNames": doctor_names,    # Expert Names
                "Education": education,         # Ratings
                "Expertise": expertise,         # Package Prices
                "ContactNumbers": contact_numbers  # Links
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
            print(f"Technical experts data and summary successfully uploaded to MongoDB from file {json_file_path}")
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
    role="Technical Project Synthesis",
    goal="Produce a brief technical project analysis.",
    backstory=(
        "Based solely on the user's query, generate a concise three-line paragraph. "
        "It should include one recommended technical approach (e.g., Data Science, Machine Learning, Web Development, etc.) "
        "and a brief explanation of the likely project requirements."
    ),
    allow_delegation=False,
    verbose=False,
    llm=model,
    expected_output="A short 3-line paragraph with one recommended technical approach and a brief explanation."
)

# Ranking Agent: Selects the top 3 technical experts and outputs their details in strict JSON.
ranking_agent = Agent(
    role="Technical Expert Ranking Agent",
    goal="Select the top 3 technical professionals and output their details in strict JSON format.",
    backstory=(
        "You have a set of technical expert profiles. Based on the synthesis result and the retrieved profiles, "
        "select the top 3 most relevant professionals. Return the output in strict JSON format containing only the keys: "
        "'Name', 'Gig Title', 'Rating', 'About', 'Expertise', 'Programming Languages', 'Frameworks', 'APIs', 'Tools', "
        "'Package Title', 'Package Price', 'Review Summary', 'Category', and 'Link'."
    ),
    allow_delegation=False,
    verbose=False,
    llm=model,
    expected_output=(
        '{"professionals": ['
        '{"Name": "...", "Gig Title": "...", "Rating": "...", "About": "...", '
        '"Expertise": "...", "Programming Languages": "...", "Frameworks": "...", "APIs": "...", "Tools": "...", '
        '"Package Title": "...", "Package Price": "...", "Review Summary": "...", "Category": "...", "Link": "..."},'
        '{"Name": "...", "Gig Title": "...", "Rating": "...", "About": "...", '
        '"Expertise": "...", "Programming Languages": "...", "Frameworks": "...", "APIs": "...", "Tools": "...", '
        '"Package Title": "...", "Package Price": "...", "Review Summary": "...", "Category": "...", "Link": "..."},'
        '{"Name": "...", "Gig Title": "...", "Rating": "...", "About": "...", '
        '"Expertise": "...", "Programming Languages": "...", "Frameworks": "...", "APIs": "...", "Tools": "...", '
        '"Package Title": "...", "Package Price": "...", "Review Summary": "...", "Category": "...", "Link": "..."}'
        ']}'
    )
)

# Questions Agent: Generates 3 clarifying questions in strict JSON.
questions_agent = Agent(
    role="Technical Project Follow-up Questions Generator",
    goal="Generate 3 specific clarifying questions focused exclusively on technical aspects of the project.",
    backstory=(
        "Based solely on the user's query, generate 3 specific clarifying questions that address purely technical details such as "
        "technical requirements, architecture, technology stack, algorithms, data structures, and implementation approaches.\n\n"
        "Examples of good specific technical questions:\n"
        "'What specific algorithms or machine learning models are you considering for this project?',\n"
        "'Which specific programming languages or frameworks do you want to use for implementation?',\n"
        "'What are the key technical challenges you anticipate in this project?'\n\n"
        "Return ONLY the following JSON format with no additional text:"
    ),
    allow_delegation=False,
    verbose=False,
    llm=model,
    expected_output='{"questions": [{"id": 1, "text": "What specific algorithms or machine learning models are you considering for this project?"}, {"id": 2, "text": "Which specific programming languages or frameworks do you want to use for implementation?"}, {"id": 3, "text": "What are the key technical challenges you anticipate in this project?"}]}'
)

# Conversational Agent: Provides additional explanation using full context.
conversational_agent = Agent(
    role="Expert Technical Consultant",
    goal="Provide authoritative technical guidance based on all available context.",
    backstory=(
        "You are a senior technical consultant with extensive experience across multiple domains including data science, "
        "machine learning, web development, and software engineering. You provide precise, actionable technical insights "
        "based on the full context—including the original query, synthesis, ranked professionals, and follow-up Q/A."
    ),
    allow_delegation=False,
    verbose=False,
    llm=model,
    expected_output="A detailed, authoritative technical explanation that directly addresses the user's question."
)

# Summary Agent - Creates a personalized summary when conversation ends
summary_agent = Agent(
    role="Technical Consultation Summary Agent",
    goal="Create a personalized summary of the entire technical consultation.",
    backstory=(
        "You create friendly, personalized summaries of technical consultations. "
        "Your summaries address the user by name and reference specific details from their conversation, "
        "including their technical project needs, the recommended experts, and main points from the discussion. "
        "The tone is warm, professional, and helpful, offering to assist further with their technical project."
    ),
    allow_delegation=False,
    verbose=False,
    llm=model,
    expected_output=(
        "Hey [Name]! Based on our conversation about your [specific technical project], "
        "I've recommended [expert name] as a potentially great fit for your development needs. "
        "Keep the project momentum going, and don't hesitate to reach out if you need any further technical guidance!"
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
        os.path.join(get_script_directory(), "engineer_embeddings.pkl"),  # Same directory as script
        os.path.join(get_script_directory(), "technical_embeddings.pkl"),  # Same directory, alternative name
        os.path.join(get_script_directory(), "..", "engineer_embeddings.pkl"),  # Parent directory
        os.path.join(get_script_directory(), "..", "technical_embeddings.pkl"),  # Parent, alternative name
        os.path.join(get_script_directory(), "..", "backend", "engineer_embeddings.pkl"),  # Backend directory
        os.path.join(get_script_directory(), "..", "backend", "technical_embeddings.pkl"),  # Backend, alt name
        os.path.abspath("backend/engineer_embeddings.pkl"),  # Absolute path from working directory
        os.path.abspath("backend/technical_embeddings.pkl"),  # Absolute path, alt name
        os.path.abspath("engineer_embeddings.pkl"),  # Directly in working directory
        os.path.abspath("technical_embeddings.pkl")  # Directly in working directory, alt name
    ]
    
    for path in potential_paths:
        if os.path.exists(path):
            print(f"Found embeddings file at: {path}", file=sys.stderr)
            return path
    
    # If we get here, we couldn't find the file
    print(f"Searched for embeddings in: {potential_paths}", file=sys.stderr)
    raise FileNotFoundError("Could not find technical embeddings file in any expected location")

def load_technical_embeddings(pkl_path: str):
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

def retrieve_relevant_professionals(query_embedding, df, top_k=10):
    similarities = []
    for idx, row in df.iterrows():
        prof_emb = row['embedding']
        sim = cosine_similarity(query_embedding, prof_emb)
        similarities.append((idx, sim))
    similarities.sort(key=lambda x: x[1], reverse=True)
    top_indices = [x[0] for x in similarities[:top_k]]
    return df.iloc[top_indices]

########################################################################
# 6. ORCHESTRATION FUNCTIONS
########################################################################

def synthesize_information(user_query: str) -> str:
    prompt = (
        f"You are the technical project synthesis agent.\n"
        f"User's original query:\n{user_query}\n\n"
        "Generate a concise three-line paragraph that includes one recommended technical approach "
        "(such as Data Science, Machine Learning, Web Development, Mobile App, etc.) and a brief explanation of the likely project requirements."
    )
    return synthesis_agent.run(prompt)

def rank_top_professionals(synthesis_text: str, retrieved_df) -> str:
    professionals_text = []
    for idx, row in retrieved_df.iterrows():
        # Parse the Table Data field to extract components
        table_data = row['Table Data'] if 'Table Data' in row else ""
        
        expertise = ""
        programming_langs = ""
        frameworks = ""
        apis = ""
        tools = ""
        
        # Extract expertise
        if "Expertise:" in table_data and "Programming language:" in table_data:
            expertise = table_data.split("Programming language:")[0].replace("Expertise:", "").strip()
        
        # Extract programming languages
        if "Programming language:" in table_data:
            if "Frameworks:" in table_data:
                programming_langs = table_data.split("Programming language:")[1].split("Frameworks:")[0].strip()
            else:
                programming_langs = table_data.split("Programming language:")[1].strip()
        
        # Extract frameworks
        if "Frameworks:" in table_data:
            if "APIs:" in table_data:
                frameworks = table_data.split("Frameworks:")[1].split("APIs:")[0].strip()
            else:
                frameworks = table_data.split("Frameworks:")[1].strip()
        
        # Extract APIs
        if "APIs:" in table_data:
            if "Tools:" in table_data:
                apis = table_data.split("APIs:")[1].split("Tools:")[0].strip()
            else:
                apis = table_data.split("APIs:")[1].strip()
                
        # Extract tools
        if "Tools:" in table_data:
            tools = table_data.split("Tools:")[1].strip()
        
        # Prepare a condensed review summary (first few words)
        review = row['Review'] if 'Review' in row else ""
        review_summary = review[:150] + "..." if len(review) > 150 else review
        
        professional_profile = (
            f"Name: {row['Name']}\n"
            f"Gig Title: {row['Gig Title']}\n"
            f"Rating: {row['Rating']}\n"
            f"About: {row['About']}\n"
            f"Expertise: {expertise}\n"
            f"Programming Languages: {programming_langs}\n"
            f"Frameworks: {frameworks}\n"
            f"APIs: {apis}\n"
            f"Tools: {tools}\n"
            f"Package Title: {row['Package Title']}\n"
            f"Package Price: {row['Package Price']}\n"
            f"Review Summary: {review_summary}\n"
            f"Category: {row['Category']}\n"
            f"Link: {row['Link']}"
        )
        professionals_text.append(professional_profile)
    
    joined_professionals = "\n\n".join(professionals_text)
    
    prompt = (
        f"You are the Technical Expert Ranking Agent.\n\n"
        f"Synthesis of user's technical project needs:\n{synthesis_text}\n\n"
        f"Here are 10 potentially relevant technical expert profiles:\n\n{joined_professionals}\n\n"
        "Based exclusively on the above synthesis and profiles, select the top 3 professionals most suitable for the user's needs. "
        "Return the output in strict JSON format with the following structure:\n"
        '{"professionals": [\n'
        '  {"Name": "...", "Gig Title": "...", "Rating": "...", "About": "...", "Expertise": "...", '
        '"Programming Languages": "...", "Frameworks": "...", "APIs": "...", "Tools": "...", '
        '"Package Title": "...", "Package Price": "...", "Review Summary": "...", "Category": "...", "Link": "..."},\n'
        '  {"Name": "...", "Gig Title": "...", "Rating": "...", "About": "...", "Expertise": "...", '
        '"Programming Languages": "...", "Frameworks": "...", "APIs": "...", "Tools": "...", '
        '"Package Title": "...", "Package Price": "...", "Review Summary": "...", "Category": "...", "Link": "..."},\n'
        '  {"Name": "...", "Gig Title": "...", "Rating": "...", "About": "...", "Expertise": "...", '
        '"Programming Languages": "...", "Frameworks": "...", "APIs": "...", "Tools": "...", '
        '"Package Title": "...", "Package Price": "...", "Review Summary": "...", "Category": "...", "Link": "..."}\n'
        ']}'
        "Your response must begin with '{' and be valid JSON."
    )
    result = ranking_agent.run(prompt)
    print(f"Debug - Raw ranked professionals result: {result}", file=sys.stderr)
    return result

def generate_followup_questions(user_query: str) -> list:
    """
    Generate 3 follow-up questions focused exclusively on technical aspects of the project.
    This function tries different prompting approaches to get valid JSON.
    """
    max_attempts = 5  # Multiple attempts
    questions = []
    
    for attempt in range(1, max_attempts + 1):
        # Different prompting strategies for different attempts
        if attempt == 1:
            # First attempt: standard approach with expected format
            prompt = (
                f"You are a technical specialist tasked with generating follow-up questions.\n\n"
                f"User's technical project query: '{user_query}'\n\n"
                "Generate exactly 3 specific technical follow-up questions that focus EXCLUSIVELY on technical aspects "
                "such as algorithms, programming languages, frameworks, architecture, data structures, etc. "
                "DO NOT ask about timelines, budgets, business goals, or other non-technical aspects.\n\n"
                "You MUST format your response as a valid JSON object using EXACTLY this structure:\n"
                '{"questions": [{"id": 1, "text": "your first question here"}, {"id": 2, "text": "your second question here"}, {"id": 3, "text": "your third question here"}]}\n\n'
                "Do not include any text outside the JSON structure. Your entire response must be a single valid JSON object.\n\n"
                "Example of correct JSON format:\n"
                '{"questions": [{"id": 1, "text": "What specific algorithms or machine learning models are you considering for this project?"}, {"id": 2, "text": "Which specific programming languages or frameworks do you want to use for implementation?"}, {"id": 3, "text": "What are the key technical challenges you anticipate in this project?"}]}'
            )
        elif attempt == 2:
            # Second attempt: more direct, simpler prompt
            prompt = (
                f"Based on this technical query: '{user_query}'\n\n"
                "Your task is to output exactly 3 clarifying PURELY TECHNICAL questions in STRICT JSON format. "
                "Focus only on programming, algorithms, architecture, and implementation details.\n\n"
                "ONLY OUTPUT THIS JSON FORMAT:\n"
                '{"questions": [{"id": 1, "text": "First technical question"}, {"id": 2, "text": "Second technical question"}, {"id": 3, "text": "Third technical question"}]}'
            )
        elif attempt == 3:
            # Third attempt: one-step-at-a-time approach
            prompt = (
                f"Technical project query: '{user_query}'\n\n"
                "Step 1: Think of 3 specific questions about technical implementation details only.\n"
                "Step 2: Format ONLY these 3 questions in this JSON structure:\n"
                '{"questions": [{"id": 1, "text": "Q1"}, {"id": 2, "text": "Q2"}, {"id": 3, "text": "Q3"}]}\n\n'
                "Output ONLY the JSON. Do not include any other text."
            )
        elif attempt == 4:
            # Fourth attempt: even simpler, with clear instructions
            prompt = (
                "Return 3 questions about programming, algorithms, or technical architecture in JSON format. "
                "ONLY output valid JSON in this format:\n"
                '{"questions": [{"id": 1, "text": "Q1"}, {"id": 2, "text": "Q2"}, {"id": 3, "text": "Q3"}]}'
            )
# Last attempt: extremely simple directive
            prompt = (
                '{"questions": [{"id": 1, "text": "What programming languages or frameworks will this project require?"}, '
                '{"id": 2, "text": "What specific technical features or functionalities are most important?"}, '
                '{"id": 3, "text": "Are there any specific performance requirements or constraints?"}]}'
            )
            
        print(f"Attempt {attempt} to generate technical questions...", file=sys.stderr)
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
                    print("Successfully generated technical questions!", file=sys.stderr)
                    return questions
                else:
                    print(f"Found {len(questions)} questions, but need exactly 3. Retrying...", file=sys.stderr)
            else:
                print("No JSON structure found in response. Retrying...", file=sys.stderr)
        except Exception as e:
            print(f"Error parsing JSON: {e}", file=sys.stderr)
    
    # Fallback questions if all attempts fail
    return [
        "What programming languages or frameworks will this project require?",
        "What specific technical features or functionalities are most important?",
        "Are there any specific performance requirements or constraints?"
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
        f"You are a Senior Technical Consultant.\n\n"
        f"User's original query: '{memory_data.get('query', '')}'\n\n"
        f"Technical analysis: {memory_data.get('synthesis_result', '')}\n\n"
        f"Recommended professionals: {memory_data.get('ranked_professionals', '')}\n\n"
        f"Technical specifications:\n{qa_formatted}\n\n"
        f"Previous conversation:\n{conversation_history}\n\n"
        f"User's current question: '{user_input}'\n\n"
        "Based on this full context, provide an authoritative technical response that directly addresses "
        "the user's question. Be specific, practical, and action-oriented. Provide clear technical recommendations "
        "and implementation guidance when appropriate. Focus solely on technical aspects of the project. "
        "Speak with the confidence and precision of a senior technical expert with deep experience in relevant technologies."
    )
    return conversational_agent.run(prompt)

def generate_consultation_summary(memory_data: dict, user_name: str) -> str:
    """Generate a personalized summary of the entire technical consultation."""
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
    professionals_info = memory_data.get('ranked_professionals', '')
    
    # Try to extract professional names from the JSON if possible
    professional_names = []
    try:
        json_data = extract_json_from_text(professionals_info)
        if "professionals" in json_data:
            for prof in json_data["professionals"]:
                if "Name" in prof:
                    professional_names.append(prof["Name"])
    except Exception as e:
        print(f"Error extracting professional names: {e}")
            
    prompt = (
        f"You are the Technical Consultation Summary Agent.\n\n"
        f"User's name: {user_name}\n\n"
        f"Original technical query: '{original_query}'\n\n"
        f"Technical analysis: {memory_data.get('synthesis_result', '')}\n\n"
        f"Recommended professionals: {professionals_info}\n\n"
        f"Technical specifications Q&A:\n{qa_formatted}\n\n"
        f"Additional conversation:\n{conversation_history}\n\n"
        f"Create a personalized summary for {user_name} that recaps their technical project needs, "
        f"the professionals recommended to them, and key points from the consultation. "
        f"Start with 'Hey {user_name}!' and make it warm and professional. "
        f"Keep it to 3-4 sentences and end by offering to help further with their technical project."
    )
    
    summary = summary_agent.run(prompt)
    return summary

def cleanup():
    """Ensure graceful shutdown of any active sessions (if required)."""
    try:
        print("Cleaning up resources...", file=sys.stderr)
    except Exception as e:
        print(f"Error shutting down resources: {e}", file=sys.stderr)

# Register cleanup function to run when the script exits
atexit.register(cleanup)

########################################################################
# 7. MAIN PROCESSING FUNCTION
########################################################################

def process_technical_query(user_query: str, df_embeddings, user_info=None):
    """
    Process a technical query and store results.
    """
    memory_data = {"query": user_query}
    if user_info:
        memory_data["user_info"] = user_info
    
    # Step 1: Run synthesis agent first
    print("Generating technical project synthesis...")
    synthesis_result = synthesize_information(user_query)
    memory_data["synthesis_result"] = synthesis_result
    print("\n--- Project Synthesis ---")
    print(synthesis_result)
    
    # Step 2: Generate follow-up questions
    print("\nGenerating technical follow-up questions...")
    questions_list = generate_followup_questions(user_query)
    
    # Step 3: Collect answers to questions
    print("\n--- Technical Specifications Questions ---")
    qa_pairs = {}
    for i, question in enumerate(questions_list, start=1):
        print(f"Q{i}: {question}")
        answer = input("Your answer: ")
        qa_pairs[question] = answer
    memory_data["followup_qa"] = qa_pairs
    
    # Step 4: Now proceed with RAG and professional ranking
    print("\nFinding and ranking the best technical experts for your project...")
    synthesis_emb = embed_text_with_gemini(synthesis_result)
    retrieved_professionals = retrieve_relevant_professionals(synthesis_emb, df_embeddings, top_k=10)
    ranked_professionals_str = rank_top_professionals(synthesis_result, retrieved_professionals)
    memory_data["ranked_professionals"] = ranked_professionals_str
    
    # Try to parse the professional data immediately for better structure
    try:
        json_data = extract_json_from_text(ranked_professionals_str)
        memory_data["professionals_json"] = json_data
    except Exception as e:
        print(f"Warning: Could not parse professional ranking response: {e}")
        memory_data["professionals_json"] = {"raw_text": ranked_professionals_str}
    
    print("\n--- Recommended Technical Experts ---")
    print(ranked_professionals_str)
    
    # Initialize conversation history
    memory_data["conversation_history"] = []
    
    return memory_data
def main():
    """Main function that handles all execution modes: interactive, server first phase, and server second phase."""
    # Print startup information
    print("Starting technical process script...", file=sys.stderr)
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
                df_embeddings = load_technical_embeddings(embeddings_path)
                
                # Generate synthesis and questions
                print("Generating technical synthesis...", file=sys.stderr)
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
            
        # Second phase: Process answers and rank professionals
        elif len(sys.argv) > 2:  
            user_query = sys.argv[1]
            
            # Check if second argument is answers_file or user_id
            second_arg = sys.argv[2]
            
            # Determine if we're in MongoDB mode or just professional ranking mode
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
                df_embeddings = load_technical_embeddings(embeddings_path)
                
                # Generate memory data for ranking professionals
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
                
                # Now proceed with RAG and professional ranking
                print("Retrieving and ranking relevant professionals...", file=sys.stderr)
                synthesis_emb = embed_text_with_gemini(synthesis_result)
                retrieved_professionals = retrieve_relevant_professionals(synthesis_emb, df_embeddings, top_k=10)
                ranked_professionals_str = rank_top_professionals(synthesis_result, retrieved_professionals)
                memory_data["ranked_professionals"] = ranked_professionals_str
                
                # Parse to get structured data
                try:
                    # Extract JSON part from the response if needed
                    if ranked_professionals_str.find('{') >= 0 and ranked_professionals_str.find('}') >= 0:
                        start = ranked_professionals_str.find('{')
                        end = ranked_professionals_str.rfind('}') + 1
                        json_str = ranked_professionals_str[start:end]
                    else:
                        json_str = ranked_professionals_str
                    
                    ranked_professionals = json.loads(json_str)
                    memory_data["professionals_json"] = ranked_professionals
                    
                    # Handle different possible keys in the JSON response
                    if "professionals" not in ranked_professionals:
                        print("Warning: 'professionals' key not found, checking for alternative keys", file=sys.stderr)
                        # Check for other potential keys
                        if "Top Professionals" in ranked_professionals:
                            print("Found 'Top Professionals' key, using this data", file=sys.stderr)
                            ranked_professionals = {"professionals": ranked_professionals["Top Professionals"]}
                        # If it's a direct array
                        elif isinstance(ranked_professionals, list):
                            print("Found array structure, wrapping in professionals array", file=sys.stderr)
                            ranked_professionals = {"professionals": ranked_professionals}
                        # If it's a single professional object
                        else:
                            # Check if any field looks like a professional
                            if any(key in ranked_professionals for key in ["Name", "Gig Title", "Rating"]):
                                print("Found single professional object, wrapping in array", file=sys.stderr)
                                ranked_professionals = {"professionals": [ranked_professionals]}
                            else:
                                print("No recognizable professional data found, creating empty array", file=sys.stderr)
                                ranked_professionals = {"professionals": []}
                    
                    result = {
                        "status": "results",
                        "professionals": ranked_professionals.get("professionals", [])
                    }
                    
                    # If we have a user_id, generate a summary and save to MongoDB
                    if user_id:
                        print("\nGenerating consultation summary...", file=sys.stderr)
                        summary = generate_consultation_summary(memory_data, user_name)
                        result["summary"] = summary
                        
                        # Save data locally FIRST regardless of MongoDB connectivity
                        try:
                            print(f"DEBUG: Type of professional_data: {type(memory_data.get('professionals_json', {}))}")
                            professional_data = memory_data.get("professionals_json", {})
                            
                            # Make sure professional_data is not empty
                            if not professional_data or (isinstance(professional_data, dict) and len(professional_data) == 0):
                                # If no data in professionals_json, try the raw string
                                professional_data = {"raw_professionals": memory_data.get("ranked_professionals", "")}
                            
                            # Always save to local JSON file first
                            json_file = save_data_to_json_file(user_id, professional_data, summary)
                            result["local_file"] = json_file if json_file else "failed_to_save"
                            
                            # Only try MongoDB if we successfully saved locally and MongoDB is available
                            if json_file and MONGODB_AVAILABLE:
                                print("\nAttempting to upload data to MongoDB...", file=sys.stderr)
                                
                                # Try to upload to MongoDB
                                success = upload_technical_data_to_mongodb(user_id, json_file)
                                
                                if success:
                                    print("Data successfully saved to MongoDB!", file=sys.stderr)
                                    result["mongodb_status"] = "success"
                                else:
                                    print("Failed to upload to MongoDB, but data is safely stored locally in JSON file.", file=sys.stderr)
                                    result["mongodb_status"] = "local_only"
                            else:
                                print("MongoDB not available or local save failed, data stored locally (if possible).", file=sys.stderr)
                                result["mongodb_status"] = "mongodb_disabled" if json_file else "local_save_failed"
                                
                        except Exception as e:
                            print(f"Error during data save process: {e}", file=sys.stderr)
                            result["mongodb_status"] = "error"
                            result["error_message"] = str(e)
                            
                            # Emergency fallback - try one more time to save locally with minimal data
                            try:
                                if not os.path.exists("output"):
                                    os.makedirs("output")
                                emergency_file = os.path.join("output", f"emergency_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
                                with open(emergency_file, 'w', encoding='utf-8') as f:
                                    json.dump({
                                        "user_id": user_id,
                                        "error": str(e),
                                        "summary": summary,
                                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                        "query": user_query
                                    }, f, indent=2, ensure_ascii=False)
                                result["emergency_file"] = emergency_file
                                print(f"Created emergency backup file: {emergency_file}", file=sys.stderr)
                            except Exception as e2:
                                print(f"Emergency save also failed: {e2}", file=sys.stderr)
                                result["emergency_save"] = "failed"
                    
                    # Output the final JSON result
                    print(json.dumps(result))
                except Exception as e:
                    print(f"Failed to parse professional rankings: {str(e)}", file=sys.stderr)
                    print(f"Raw professional output was: {ranked_professionals_str}", file=sys.stderr)
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
            embeddings_path = os.path.join(current_dir, "engineer_embeddings.pkl")
            if not os.path.exists(embeddings_path):
                print(f"Error: Embeddings file not found at {embeddings_path}")
                sys.exit(1)
        
        print("Loading technical experts database...")
        df_embeddings = load_technical_embeddings(embeddings_path)
        
        user_query = input("\nDescribe your technical project or requirements: ").strip()
        
        if not user_query:
            print("No input provided. Exiting.")
            return

        # Process the technical query with interactive flow
        memory_data = process_technical_query(user_query, df_embeddings, {"name": user_name, "id": user_id})
        
        # Display ranked professionals in a more readable format
        try:
            professionals_json = memory_data.get("professionals_json", {})
            print("\n--- Top Recommended Technical Experts ---")
            for i, prof in enumerate(professionals_json.get("professionals", []), start=1):
                print(f"\nExpert {i}: {prof.get('Name', 'Unknown')}")
                print(f"Rating: {prof.get('Rating', 'Not specified')}")
                print(f"Package Price: {prof.get('Package Price', 'Not specified')}")
                print(f"Link: {prof.get('Link', 'Not available')}")
        except:
            # If parsing fails, just show the raw output
            pass
        
        # Continue conversation for follow-up questions
        print("\n--- Technical Consultation Mode ---")
        print("You can now ask specific questions about implementing your project or working with these experts.")
        print("Type 'exit' to end the consultation.")
        
        while True:
            user_input = input("\nYour question: ").strip()
            if user_input.lower() == "exit":
                # Generate summary before exiting
                print("\nGenerating consultation summary...")
                summary = generate_consultation_summary(memory_data, user_name)
                print("\n--- Technical Consultation Summary ---")
                print(summary)
                
                # Save data locally and then try to upload to MongoDB
                if user_id:
                    try:
                        # Get the parsed professional data from memory if available
                        professional_data = memory_data.get("professionals_json", {})
                        
                        # Make sure professional_data is not empty
                        if not professional_data or (isinstance(professional_data, dict) and len(professional_data) == 0):
                            # If no data in professionals_json, try the raw string
                            professional_data = {"raw_professionals": memory_data.get("ranked_professionals", "")}
                        
                        # Save to local JSON file first regardless of MongoDB availability
                        json_file = save_data_to_json_file(user_id, professional_data, summary)
                        
                        if json_file:
                            print(f"\nData successfully saved to: {json_file}")
                            
                            # Try to upload to MongoDB if available
                            if MONGODB_AVAILABLE:
                                print("\nAttempting to upload data to MongoDB...")
                                success = upload_technical_data_to_mongodb(user_id, json_file)
                                
                                if success:
                                    print("Data successfully saved to MongoDB!")
                                else:
                                    print("Failed to upload to MongoDB, but data is safely stored locally in JSON file.")
                            else:
                                print("MongoDB not available, data stored locally in JSON file.")
                        else:
                            print("Failed to save data locally.")
                            
                            # Emergency fallback save
                            try:
                                if not os.path.exists("output"):
                                    os.makedirs("output")
                                emergency_file = os.path.join("output", f"emergency_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
                                with open(emergency_file, 'w', encoding='utf-8') as f:
                                    json.dump({
                                        "user_id": user_id,
                                        "summary": summary,
                                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                        "query": user_query
                                    }, f, indent=2, ensure_ascii=False)
                                print(f"Created emergency backup file: {emergency_file}")
                            except Exception as e2:
                                print(f"Emergency save also failed: {e2}")
                                
                    except Exception as e:
                        print(f"Error during data save process: {e}")
                
                print("Thank you for using our technical consulting service. We wish you success with your project!")
                break
            
            # Get response and update conversation history
            response = get_conversational_response(memory_data, user_input)
            print("\n--- Technical Expert Response ---")
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