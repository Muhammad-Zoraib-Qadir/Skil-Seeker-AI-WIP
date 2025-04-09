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

def save_data_to_json_file(user_id, services_data, summary_text=None):
    """Save data to a local JSON file for debugging and backup purposes."""
    try:
        # Parse services_data to ensure it's a proper object, not a string
        if isinstance(services_data, str):
            # Try to parse it first as regular JSON
            try:
                parsed_services_data = json.loads(services_data)
            except json.JSONDecodeError:
                # If that fails, try to extract JSON from markdown code blocks
                code_block_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', services_data)
                if code_block_match:
                    json_content = code_block_match.group(1).strip()
                    parsed_services_data = json.loads(json_content)
                else:
                    # If no code block, just use the string as is
                    parsed_services_data = {"raw_data": services_data}
        else:
            parsed_services_data = services_data
            
        # Create data structure
        data = {
            "user_id": str(user_id),
            "timestamp": datetime.now().strftime("%Y-%m-%d_%H-%M-%S"),
            "services_data": parsed_services_data,
            "summary": summary_text if summary_text else ""
        }
        
        # Create filename with timestamp for uniqueness
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"seo_data_{user_id}_{timestamp}.json"
        
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

def upload_seo_data_to_mongodb(user_id, json_file_path):
    """
    Upload SEO services data from local JSON file to MongoDB.
    Uses the existing medical fields to store SEO data.
    Also saves the conversation summary.
    """
    if not MONGODB_AVAILABLE:
        print("MongoDB features are disabled due to missing packages.")
        return False
        
    try:
        # Read the JSON file
        with open(json_file_path, 'r') as f:
            data = json.load(f)
        
        # Parse the services data
        services_data = data.get("services_data", {})
        summary_text = data.get("summary", "")
            
        # Extract service information to store in medical fields
        doctor_names = []  # Will store service names
        education = []     # Will store gig titles
        expertise = []     # Will store ratings
        contact_numbers = [] # Will store package prices
        
        # Check if services_data is an array directly or inside a services key
        services_array = None
        if isinstance(services_data, list):
            services_array = services_data
        elif isinstance(services_data, dict) and "services" in services_data:
            services_array = services_data.get("services", [])
        else:
            print(f"Warning: Unexpected services data format: {type(services_data)}")
            print(f"Services data content (sample): {str(services_data)[:200]}...")
            services_array = []
            
        # Process each service
        for service in services_array:
            if isinstance(service, dict):
                doctor_names.append(service.get("Name", ""))  # Store service name in DoctorNames
                education.append(service.get("Gig Title", ""))  # Store gig title in Education
                expertise.append(service.get("Rating", ""))  # Store rating in Expertise
                contact_numbers.append(service.get("Package Price", ""))  # Store price in ContactNumbers
        
        # Connect to database
        skillseeker = connect_to_db()
        if not skillseeker:
            return False
            
        user_id_obj = ObjectId(user_id)
        
        # Debug info
        print(f"Processing {len(services_array)} SEO services")
        print(f"Service names (storing in DoctorNames): {doctor_names}")
        print(f"Gig titles (storing in Education): {education}")
        print(f"Ratings (storing in Expertise): {expertise}")
        print(f"Package prices (storing in ContactNumbers): {contact_numbers}")
        
        # Create conversation entry for the summary
        conversation_entry = {
            "query": "seo_summary",
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
        
        # Then update with new SEO data and conversation summary
        update = {
            "$set": {
                "DoctorNames": doctor_names,    # Service Names
                "Education": education,         # Gig Titles
                "Expertise": expertise,         # Ratings
                "ContactNumbers": contact_numbers  # Package Prices
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
            print(f"SEO services data and summary successfully uploaded to MongoDB from file {json_file_path}")
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
    role="SEO Strategy Synthesis",
    goal="Produce a brief SEO query analysis.",
    backstory=(
        "Based solely on the user's query, generate a concise three-line paragraph. "
        "It should include one recommended SEO approach (e.g., On-page SEO, Content Marketing, Keyword Research, etc.) "
        "and a brief explanation of the likely SEO objective."
    ),
    allow_delegation=False,
    verbose=False,
    llm=model,
    expected_output="A short 3-line paragraph with one recommended SEO approach and a brief explanation."
)

# Ranking Agent: Selects the top 3 SEO services and outputs their details in strict JSON.
ranking_agent = Agent(
    role="SEO Service Ranking Agent",
    goal="Select the top 3 SEO services and output their details in strict JSON format.",
    backstory=(
        "You have a set of SEO service profiles. Based on the synthesis result and the retrieved profiles, "
        "select the top 3 most relevant services. Return the output in strict JSON format containing only the keys: "
        "'Name', 'Gig Title', 'Rating', 'About', 'Industry Expertise', 'Languages', 'Package Title', 'Package Price', and 'Review'."
    ),
    allow_delegation=False,
    verbose=False,
    llm=model,
    expected_output=(
        '{"services": ['
        '{"Name": "...", "Gig Title": "...", "Rating": "...", "About": "...", '
        '"Industry Expertise": "...", "Languages": "...", "Package Title": "...", "Package Price": "...", "Review": "..."},'
        '{"Name": "...", "Gig Title": "...", "Rating": "...", "About": "...", '
        '"Industry Expertise": "...", "Languages": "...", "Package Title": "...", "Package Price": "...", "Review": "..."},'
        '{"Name": "...", "Gig Title": "...", "Rating": "...", "About": "...", '
        '"Industry Expertise": "...", "Languages": "...", "Package Title": "...", "Package Price": "...", "Review": "..."}'
        ']}'
    )
)

# Questions Agent: Generates 3 clarifying questions in strict JSON.
questions_agent = Agent(
    role="SEO Follow-up Questions Generator",
    goal="Generate 3 specific clarifying questions to further understand the SEO query.",
    backstory=(
        "Based solely on the user's query, generate 3 specific clarifying questions that address details such as "
        "website goals, current SEO performance, target audience, and business objectives.\n\n"
        "Examples of good specific questions:\n"
        "'What are your primary business goals for your website?',\n"
        "'What keywords are you currently targeting and how are they performing?',\n"
        "'Who is your target audience and what are their search behaviors?'\n\n"
        "Return ONLY the following JSON format with no additional text:"
    ),
    allow_delegation=False,
    verbose=False,
    llm=model,
    expected_output='{"questions": [{"id": 1, "text": "What are your primary business goals for your website?"}, {"id": 2, "text": "What keywords are you currently targeting and how are they performing?"}, {"id": 3, "text": "Who is your target audience and what are their search behaviors?"}]}'
)

# Conversational Agent: Provides additional explanation using full context.
conversational_agent = Agent(
    role="Expert SEO Strategist",
    goal="Provide authoritative SEO guidance based on all available context.",
    backstory=(
        "You are a senior SEO specialist with extensive experience across multiple industries. "
        "You provide precise, actionable SEO insights based on the full context—including "
        "the original query, synthesis, ranked services, and follow-up Q/A."
    ),
    allow_delegation=False,
    verbose=False,
    llm=model,
    expected_output="A detailed, authoritative SEO explanation that directly addresses the user's question."
)

# Summary Agent - Creates a personalized summary when conversation ends
summary_agent = Agent(
    role="SEO Consultation Summary Agent",
    goal="Create a personalized summary of the entire SEO consultation.",
    backstory=(
        "You create friendly, personalized summaries of SEO consultations. "
        "Your summaries address the user by name and reference specific details from their conversation, "
        "including their SEO needs, the recommended services, and main points from the discussion. "
        "The tone is warm, professional, and helpful, offering to assist further with their SEO goals."
    ),
    allow_delegation=False,
    verbose=False,
    llm=model,
    expected_output=(
        "Hey [Name]! Based on our conversation about your [specific SEO challenge], "
        "I've recommended [service name] as a potentially great fit for your needs. "
        "Keep optimizing your site, and don't hesitate to reach out if you need any further guidance!"
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
        os.path.join(get_script_directory(), "seo_embeddings.pkl"),  # Same directory as script
        os.path.join(get_script_directory(), "marketing_embeddings.pkl"),  # Same directory, alternative name
        os.path.join(get_script_directory(), "..", "seo_embeddings.pkl"),  # Parent directory
        os.path.join(get_script_directory(), "..", "marketing_embeddings.pkl"),  # Parent, alternative name
        os.path.join(get_script_directory(), "..", "backend", "seo_embeddings.pkl"),  # Backend directory
        os.path.join(get_script_directory(), "..", "backend", "marketing_embeddings.pkl"),  # Backend, alt name
        os.path.abspath("backend/seo_embeddings.pkl"),  # Absolute path from working directory
        os.path.abspath("backend/marketing_embeddings.pkl"),  # Absolute path, alt name
        os.path.abspath("seo_embeddings.pkl"),  # Directly in working directory
        os.path.abspath("marketing_embeddings.pkl")  # Directly in working directory, alt name
    ]
    
    for path in potential_paths:
        if os.path.exists(path):
            print(f"Found embeddings file at: {path}", file=sys.stderr)
            return path
    
    # If we get here, we couldn't find the file
    print(f"Searched for embeddings in: {potential_paths}", file=sys.stderr)
    raise FileNotFoundError("Could not find SEO embeddings file in any expected location")

def load_seo_embeddings(pkl_path: str):
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

def retrieve_relevant_services(query_embedding, df, top_k=10):
    similarities = []
    for idx, row in df.iterrows():
        service_emb = row['embedding']
        sim = cosine_similarity(query_embedding, service_emb)
        similarities.append((idx, sim))
    similarities.sort(key=lambda x: x[1], reverse=True)
    top_indices = [x[0] for x in similarities[:top_k]]
    return df.iloc[top_indices]

########################################################################
# 6. ORCHESTRATION FUNCTIONS
########################################################################

def synthesize_information(user_query: str) -> str:
    prompt = (
        f"You are the SEO synthesis agent.\n"
        f"User's original query:\n{user_query}\n\n"
        "Generate a concise three-line paragraph that includes one recommended SEO approach "
        "(such as On-page SEO, Technical SEO, Content Strategy, Keyword Research, Link Building, etc.) "
        "and a brief explanation of the likely SEO objective."
    )
    return synthesis_agent.run(prompt)

def rank_top_services(synthesis_text: str, retrieved_df) -> str:
    services_text = []
    for idx, row in retrieved_df.iterrows():
        # Extract table data components
        table_data = row['Table Data'] if 'Table Data' in row else ""
        industry_expertise = ""
        languages = ""
        
        if "Industry expertise:" in table_data:
            industry_expertise = table_data.split("Language:")[0].replace("Industry expertise:", "").strip()
        
        if "Language:" in table_data:
            languages = table_data.split("Language:")[1].strip()
        
        service_profile = (
            f"Name: {row['Name']}\n"
            f"Gig Title: {row['Gig Title']}\n"
            f"Rating: {row['Rating']}\n"
            f"About: {row['About']}\n"
            f"Industry Expertise: {industry_expertise}\n"
            f"Languages: {languages}\n"
            f"Package Title: {row['Package Title']}\n"
            f"Package Price: {row['Package Price']}\n"
            f"Review: {row['Review']}"
        )
        services_text.append(service_profile)
    
    joined_services = "\n\n".join(services_text)
    
    prompt = (
        f"You are the SEO Service Ranking Agent.\n\n"
        f"Synthesis of user's SEO situation:\n{synthesis_text}\n\n"
        f"Here are 10 potentially relevant SEO service profiles:\n\n{joined_services}\n\n"
        "Based exclusively on the above synthesis and profiles, select the top 3 services most suitable for the user's needs. "
        "Return the output in strict JSON format with the following structure:\n"
        '{"services": [\n'
        '  {"Name": "...", "Gig Title": "...", "Rating": "...", "About": "...", '
        '"Industry Expertise": "...", "Languages": "...", "Package Title": "...", "Package Price": "...", "Review": "..."},\n'
        '  {"Name": "...", "Gig Title": "...", "Rating": "...", "About": "...", '
        '"Industry Expertise": "...", "Languages": "...", "Package Title": "...", "Package Price": "...", "Review": "..."},\n'
        '  {"Name": "...", "Gig Title": "...", "Rating": "...", "About": "...", '
        '"Industry Expertise": "...", "Languages": "...", "Package Title": "...", "Package Price": "...", "Review": "..."}\n'
        ']}'
        "Your response must begin with '{' and be valid JSON."
    )
    result = ranking_agent.run(prompt)
    print(f"Debug - Raw ranked services result: {result}", file=sys.stderr)
    return result

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
                f"You are an SEO professional tasked with generating follow-up questions.\n\n"
                f"User's SEO query: '{user_query}'\n\n"
                "Generate exactly 3 specific SEO follow-up questions that would help clarify their needs.\n\n"
                "You MUST format your response as a valid JSON object using EXACTLY this structure:\n"
                '{"questions": [{"id": 1, "text": "your first question here"}, {"id": 2, "text": "your second question here"}, {"id": 3, "text": "your third question here"}]}\n\n'
                "Do not include any text outside the JSON structure. Your entire response must be a single valid JSON object.\n\n"
                "Example of correct JSON format:\n"
                '{"questions": [{"id": 1, "text": "What are your primary business goals for your website?"}, {"id": 2, "text": "What keywords are you currently targeting and how are they performing?"}, {"id": 3, "text": "Who is your target audience and what are their search behaviors?"}]}'
            )
        elif attempt == 2:
            # Second attempt: more direct, simpler prompt
            prompt = (
                f"Based on this SEO query: '{user_query}'\n\n"
                "Your task is to output exactly 3 clarifying SEO questions in STRICT JSON format.\n\n"
                "ONLY OUTPUT THIS JSON FORMAT:\n"
                '{"questions": [{"id": 1, "text": "First question"}, {"id": 2, "text": "Second question"}, {"id": 3, "text": "Third question"}]}'
            )
        elif attempt == 3:
            # Third attempt: one-step-at-a-time approach
            prompt = (
                f"SEO query: '{user_query}'\n\n"
                "Step 1: Think of 3 specific SEO questions that would help clarify the situation.\n"
                "Step 2: Format ONLY these 3 questions in this JSON structure:\n"
                '{"questions": [{"id": 1, "text": "Q1"}, {"id": 2, "text": "Q2"}, {"id": 3, "text": "Q3"}]}\n\n'
                "Output ONLY the JSON. Do not include any other text."
            )
        elif attempt == 4:
            # Fourth attempt: even simpler, with clear instructions
            prompt = (
                "Return 3 SEO questions in JSON format. ONLY output valid JSON in this format:\n"
                '{"questions": [{"id": 1, "text": "Q1"}, {"id": 2, "text": "Q2"}, {"id": 3, "text": "Q3"}]}'
            )
        else:
            # Last attempt: extremely simple directive
            prompt = (
                '{"questions": [{"id": 1, "text": "What are your primary website goals?"}, '
                '{"id": 2, "text": "What keywords are you targeting currently?"}, '
                '{"id": 3, "text": "Who is your target audience?"}]}'
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
        "What are your primary business goals for your website?",
        "What keywords are you currently targeting and how are they performing?",
        "Who is your target audience and what are their search behaviors?"
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
        f"You are a Senior SEO Strategist.\n\n"
        f"User's original query: '{memory_data.get('query', '')}'\n\n"
        f"SEO analysis: {memory_data.get('synthesis_result', '')}\n\n"
        f"Recommended services: {memory_data.get('ranked_services', '')}\n\n"
        f"Strategy notes:\n{qa_formatted}\n\n"
        f"Previous conversation:\n{conversation_history}\n\n"
        f"User's current question: '{user_input}'\n\n"
        "Based on this full context, provide an authoritative SEO response that directly addresses "
        "the user's question. Be specific, practical, and action-oriented. Provide clear SEO strategies "
        "and implementation steps when appropriate. Speak with the confidence and precision of a senior SEO "
        "expert with decades of experience in this field."
    )
    return conversational_agent.run(prompt)

def generate_conversation_summary(memory_data: dict, user_name: str) -> str:
    """Generate a personalized summary of the entire SEO consultation."""
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
    service_info = memory_data.get('ranked_services', '')
    
    # Try to extract service names from the JSON if possible
    service_names = []
    try:
        json_data = extract_json_from_text(service_info)
        if "services" in json_data:
            for service in json_data["services"]:
                if "Name" in service:
                    service_names.append(service["Name"])
    except Exception as e:
        print(f"Error extracting service names: {e}")
            
    prompt = (
        f"You are the SEO Consultation Summary Agent.\n\n"
        f"User's name: {user_name}\n\n"
        f"Original SEO query: '{original_query}'\n\n"
        f"SEO analysis: {memory_data.get('synthesis_result', '')}\n\n"
        f"Recommended services: {service_info}\n\n"
        f"Strategy Q&A:\n{qa_formatted}\n\n"
        f"Additional conversation:\n{conversation_history}\n\n"
        f"Create a personalized summary for {user_name} that recaps their SEO needs, "
        f"the services recommended to them, and key points from the consultation. "
        f"Start with 'Hey {user_name}!' and make it warm and professional. "
        f"Keep it to 3-4 sentences and end by offering to help further with their SEO goals."
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

def process_seo_query(user_query: str, df_embeddings, user_info=None):
    """
    Process an SEO query and store results.
    """
    memory_data = {"query": user_query}
    if user_info:
        memory_data["user_info"] = user_info
    
    # Step 1: Run synthesis agent first
    print("Generating SEO strategy synthesis...")
    synthesis_result = synthesize_information(user_query)
    memory_data["synthesis_result"] = synthesis_result
    print("\n--- SEO Strategy Synthesis ---")
    print(synthesis_result)
    
    # Step 2: Generate follow-up questions
    print("\nGenerating follow-up questions...")
    questions_list = generate_followup_questions(user_query)
    
    # Step 3: Collect answers to questions
    print("\n--- SEO Discovery Questions ---")
    qa_pairs = {}
    for i, question in enumerate(questions_list, start=1):
        print(f"Q{i}: {question}")
        answer = input("Your answer: ")
        qa_pairs[question] = answer
    memory_data["followup_qa"] = qa_pairs
    
    # Step 4: Now proceed with RAG and service ranking
    print("\nIdentifying and ranking optimal SEO services...")
    synthesis_emb = embed_text_with_gemini(synthesis_result)
    retrieved_services = retrieve_relevant_services(synthesis_emb, df_embeddings, top_k=10)
    ranked_services_str = rank_top_services(synthesis_result, retrieved_services)
    memory_data["ranked_services"] = ranked_services_str
    
    # Try to parse the service data immediately for better structure
    try:
        json_data = extract_json_from_text(ranked_services_str)
        memory_data["services_json"] = json_data
    except Exception as e:
        print(f"Warning: Could not parse service ranking response: {e}")
        memory_data["services_json"] = {"raw_text": ranked_services_str}
    
    print("\n--- Recommended SEO Services ---")
    print(ranked_services_str)
    
    # Initialize conversation history
    memory_data["conversation_history"] = []
    
    return memory_data
def main():
    """Main function that handles all execution modes: interactive, server first phase, and server second phase."""
    # Print startup information
    print("Starting SEO process script...", file=sys.stderr)
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
                df_embeddings = load_seo_embeddings(embeddings_path)
                
                # Generate synthesis and questions
                print("Generating SEO synthesis...", file=sys.stderr)
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
            
        # Second phase: Process answers and rank services
        elif len(sys.argv) > 2:  
            user_query = sys.argv[1]
            
            # Check if second argument is answers_file or user_id
            second_arg = sys.argv[2]
            
            # Determine if we're in MongoDB mode or just service ranking mode
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
                df_embeddings = load_seo_embeddings(embeddings_path)
                
                # Generate memory data for ranking services
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
                
                # Now proceed with RAG and service ranking
                print("Retrieving and ranking relevant SEO services...", file=sys.stderr)
                synthesis_emb = embed_text_with_gemini(synthesis_result)
                retrieved_services = retrieve_relevant_services(synthesis_emb, df_embeddings, top_k=10)
                ranked_services_str = rank_top_services(synthesis_result, retrieved_services)
                memory_data["ranked_services"] = ranked_services_str
                
                # Parse to get structured data
                try:
                    # Extract JSON part from the response if needed
                    if ranked_services_str.find('{') >= 0 and ranked_services_str.find('}') >= 0:
                        start = ranked_services_str.find('{')
                        end = ranked_services_str.rfind('}') + 1
                        json_str = ranked_services_str[start:end]
                    else:
                        json_str = ranked_services_str
                    
                    ranked_services = json.loads(json_str)
                    memory_data["services_json"] = ranked_services
                    
                    # Handle different possible keys in the JSON response
                    if "services" not in ranked_services:
                        print("Warning: 'services' key not found, checking for alternative keys", file=sys.stderr)
                        # Check for other potential keys
                        if "top_services" in ranked_services:
                            print("Found 'top_services' key, using this data", file=sys.stderr)
                            ranked_services = {"services": ranked_services["top_services"]}
                        # If it's a direct array
                        elif isinstance(ranked_services, list):
                            print("Found array structure, wrapping in services array", file=sys.stderr)
                            ranked_services = {"services": ranked_services}
                        # If it's a single service object
                        else:
                            # Check if any field looks like a service
                            if any(key in ranked_services for key in ["Name", "Gig Title", "Rating"]):
                                print("Found single service object, wrapping in array", file=sys.stderr)
                                ranked_services = {"services": [ranked_services]}
                            else:
                                print("No recognizable service data found, creating empty array", file=sys.stderr)
                                ranked_services = {"services": []}
                    
                    result = {
                        "status": "results",
                        "services": ranked_services.get("services", [])
                    }
                    
                    # If we have a user_id, generate a summary and save to MongoDB
                    if user_id:
                        print("\nGenerating consultation summary...", file=sys.stderr)
                        summary = generate_conversation_summary(memory_data, user_name)
                        result["summary"] = summary
                        
                        # Save data locally and upload to MongoDB
                        try:
                            # Get the parsed service data from memory
                            service_data = memory_data.get("services_json", {})
                            
                            # Save to local JSON file first
                            json_file = save_data_to_json_file(user_id, service_data, summary)
                            
                            if json_file:
                                print("\nAttempting to upload data to MongoDB...", file=sys.stderr)
                                
                                # Try to upload to MongoDB if available
                                if MONGODB_AVAILABLE:
                                    # Try to upload to MongoDB
                                    success = upload_seo_data_to_mongodb(user_id, json_file)
                                    
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
                    print(f"Failed to parse SEO service rankings: {str(e)}", file=sys.stderr)
                    print(f"Raw service output was: {ranked_services_str}", file=sys.stderr)
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
            embeddings_path = os.path.join(current_dir, "marketing_embeddings.pkl")
            if not os.path.exists(embeddings_path):
                print(f"Error: Embeddings file not found at {embeddings_path}")
                sys.exit(1)
        
        print("Loading SEO services database...")
        df_embeddings = load_seo_embeddings(embeddings_path)
        
        user_query = input("\nDescribe your SEO needs or challenges: ").strip()
        
        if not user_query:
            print("No input provided. Exiting.")
            return

        # Process the SEO query with interactive flow
        memory_data = process_seo_query(user_query, df_embeddings, {"name": user_name, "id": user_id})
        
        # Display ranked services in a more readable format
        try:
            services_json = memory_data.get("services_json", {})
            print("\n--- Top Recommended SEO Services ---")
            for i, service in enumerate(services_json.get("services", []), start=1):
                print(f"\nService {i}: {service.get('Name', 'Unknown')}")
                print(f"Offering: {service.get('Gig Title', 'Not specified')}")
                print(f"Rating: {service.get('Rating', 'Not specified')}")
                print(f"Package Price: {service.get('Package Price', 'Not specified')}")
        except:
            # If parsing fails, just show the raw output
            pass
        
        # Continue conversation for follow-up questions
        print("\n--- SEO Strategy Consultation ---")
        print("You can now ask specific questions about implementing these SEO strategies or services.")
        print("Type 'exit' to end the consultation.")
        
        while True:
            user_input = input("\nYour question: ").strip()
            if user_input.lower() == "exit":
                # Generate summary before exiting
                print("\nGenerating consultation summary...")
                summary = generate_conversation_summary(memory_data, user_name)
                print("\n--- SEO Consultation Summary ---")
                print(summary)
                
                # Save data locally and then try to upload to MongoDB
                if user_id:
                    try:
                        # Get the parsed service data from memory if available
                        service_data = memory_data.get("services_json", {})
                        
                        # Save to local JSON file first
                        json_file = save_data_to_json_file(user_id, service_data, summary)
                        
                        if json_file:
                            print("\nAttempting to upload data to MongoDB...")
                            
                            # Try to upload to MongoDB if available
                            if MONGODB_AVAILABLE:
                                success = upload_seo_data_to_mongodb(user_id, json_file)
                                
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
                
                print("Thank you for using our SEO strategy service. We wish you success with your SEO campaigns!")
                break
            
            # Get response and update conversation history
            response = get_conversational_response(memory_data, user_input)
            print("\n--- SEO Expert Response ---")
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
            embeddings_path = os.path.join(current_dir, "marketing_embeddings.pkl")
            if not os.path.exists(embeddings_path):
                print(f"Error: Embeddings file not found at {embeddings_path}")
                sys.exit(1)
        
        print("Loading SEO services database...")
        df_embeddings = load_seo_embeddings(embeddings_path)
        
        user_query = input("\nDescribe your SEO needs or challenges: ").strip()
        
        if not user_query:
            print("No input provided. Exiting.")
            

        # Process the SEO query with interactive flow
        memory_data = process_seo_query(user_query, df_embeddings, {"name": user_name, "id": user_id})
        
        # Display ranked services in a more readable format
        try:
            services_json = memory_data.get("services_json", {})
            print("\n--- Top Recommended SEO Services ---")
            for i, service in enumerate(services_json.get("services", []), start=1):
                print(f"\nService {i}: {service.get('Name', 'Unknown')}")
                print(f"Offering: {service.get('Gig Title', 'Not specified')}")
                print(f"Rating: {service.get('Rating', 'Not specified')}")
                print(f"Package Price: {service.get('Package Price', 'Not specified')}")
        except:
            # If parsing fails, just show the raw output
            pass
        
        # Continue conversation for follow-up questions
        print("\n--- SEO Strategy Consultation ---")
        print("You can now ask specific questions about implementing these SEO strategies or services.")
        print("Type 'exit' to end the consultation.")
        
        while True:
            user_input = input("\nYour question: ").strip()
            if user_input.lower() == "exit":
                # Generate summary before exiting
                print("\nGenerating consultation summary...")
                summary = generate_conversation_summary(memory_data, user_name)
                print("\n--- SEO Consultation Summary ---")
                print(summary)
                
                # Save data locally and then try to upload to MongoDB
                if user_id:
                    try:
                        # Get the parsed service data from memory if available
                        service_data = memory_data.get("services_json", {})
                        
                        # Save to local JSON file first
                        json_file = save_data_to_json_file(user_id, service_data, summary)
                        
                        if json_file:
                            print("\nAttempting to upload data to MongoDB...")
                            
                            # Try to upload to MongoDB if available
                            if MONGODB_AVAILABLE:
                                success = upload_seo_data_to_mongodb(user_id, json_file)
                                
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
                
                print("Thank you for using our SEO strategy service. We wish you success with your SEO campaigns!")
                break
            
            # Get response and update conversation history
            response = get_conversational_response(memory_data, user_input)
            print("\n--- SEO Expert Response ---")
            print(response)
            
            # Add to conversation history
            memory_data["conversation_history"].append({
                "user": user_input,
                "assistant": response
            })