import os
import sys
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
import google.generativeai as genai
import atexit

# Try to import MongoDB modules but make them optional
try:
    from pymongo.mongo_client import MongoClient
    from pymongo.server_api import ServerApi
    import hashlib
    MONGODB_AVAILABLE = True
except ImportError:
    print("Warning: MongoDB modules not available. User authentication and history features will be disabled.")
    MONGODB_AVAILABLE = False

# -------------------------------
# MongoDB Connection Setup
# -------------------------------
def connect_to_db():
    """Connect to MongoDB database and return the skillseeker collection."""
    uri = "mongodb+srv://shayanarsalan2003:Shayan717@cluster0.ocn53.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    client = MongoClient(uri, server_api=ServerApi('1'))
    db = client["Cluster0"]
    skillseeker = db["skillseeker"]
    return skillseeker

# -------------------------------
# Authentication Functions
# -------------------------------
def login_user():
    """Function to handle user login."""
    skillseeker = connect_to_db()
    
    print("\n===== LOGIN =====")
    username = input("Username: ")
    password = input("Password: ")
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    
    user = skillseeker.find_one({"Username": username})
    
    if user and user["Password"] == hashed_password:
        print(f"Login successful! Welcome back, {user['Name']}!")
        return user
    else:
        print("Invalid username or password.")
        return None

def register_user():
    """Function to handle user registration."""
    skillseeker = connect_to_db()
    
    print("\n===== SIGN UP =====")
    name = input("Enter your full name: ")
    
    # Username validation
    while True:
        username = input("Enter a username: ")
        existing_user = skillseeker.find_one({"Username": username})
        if existing_user:
            print("Username already exists. Please choose a different one.")
        else:
            break
    
    # Password
    password = input("Enter a password: ")
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    
    # Create new user with doctor fields initialized as empty arrays
    new_user = {
        "Name": name,
        "Username": username,
        "Password": hashed_password,
        "Conversation": [],
        # Doctor fields - initialized as empty arrays to allow multiple entries
        "DoctorNames": [],
        "Education": [],
        "Expertise": [],
        "ContactNumbers": []
    }
    
    result = skillseeker.insert_one(new_user)
    print(f"Signup successful! Welcome, {name}!")
    return new_user

# -------------------------------
# Doctor Information Management
# -------------------------------
def add_doctor_info(user_id):
    """Function to add doctor information to a user's profile."""
    if not user_id:
        print("No user logged in.")
        return
    
    skillseeker = connect_to_db()
    
    print("\n===== ADD DOCTOR INFORMATION =====")
    doctor_name = input("Enter doctor name: ")
    education = input("Enter education details: ")
    expertise = input("Enter area of expertise: ")
    contact = input("Enter contact number: ")
    
    # Update user document with new doctor information
    skillseeker.update_one(
        {"_id": user_id},
        {"$push": {
            "DoctorNames": doctor_name,
            "Education": education,
            "Expertise": expertise,
            "ContactNumbers": contact
        }}
    )
    
    print("Doctor information added successfully!")

def view_doctor_info(user_id):
    """Function to view doctor information in a user's profile."""
    if not user_id:
        print("No user logged in.")
        return
    
    skillseeker = connect_to_db()
    user = skillseeker.find_one({"_id": user_id})
    
    if not user:
        print("User not found.")
        return
    
    print("\n===== DOCTOR INFORMATION =====")
    
    # Check if doctor information exists
    if not user.get("DoctorNames") or len(user["DoctorNames"]) == 0:
        print("No doctor information found.")
        return
    
    # Display all doctor information
    for i in range(len(user["DoctorNames"])):
        print(f"\nDoctor {i+1}:")
        print(f"Name: {user['DoctorNames'][i] if i < len(user['DoctorNames']) else 'N/A'}")
        print(f"Education: {user['Education'][i] if i < len(user['Education']) else 'N/A'}")
        print(f"Expertise: {user['Expertise'][i] if i < len(user['Expertise']) else 'N/A'}")
        print(f"Contact: {user['ContactNumbers'][i] if i < len(user['ContactNumbers']) else 'N/A'}")

# -------------------------------
# Function: Save query to user conversation history
# -------------------------------
def save_to_conversation(user_id, query, response=None):
    if not user_id:
        return
    
    # Skip saving if the response is the general response
    if response and "Please restate your question with more specific details" in response:
        return
    
    skillseeker = connect_to_db()
    conversation_entry = {
        "query": query,
        "response": response if response else "Processed by external script"
    }
    
    skillseeker.update_one(
        {"_id": user_id}, 
        {"$push": {"Conversation": conversation_entry}}
    )

# -------------------------------
# Configure the Gemini API
# -------------------------------
genai.configure(api_key="AIzaSyCohbQG3sbkCf1LLbf1spVXFAgzjsRU1xA")  

generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

# Create the Gemini generative model
model = genai.GenerativeModel(
    model_name="gemini-2.0-flash-lite",
    generation_config=generation_config,
)

# -------------------------------
# Define Agent Information
# -------------------------------
AGENTS_INFO = {
    "Medical Classifier": {
        "goal": "Tell me if the input query is 'Medical' or 'Other'.",
        "backstory": (
            "You are an AI assistant trained to identify whether the user is asking about medical issues. "
            "Answer with exactly 'Medical' if the query is medical-related, otherwise respond with 'Other'."
        ),
        "expected": "Medical",
    },
    "Computer Science Classifier": {
        "goal": "Tell me if the input query is 'CS' or 'Other'.",
        "backstory": (
            "You are an AI assistant trained to determine if a given query relates to computer science or programming. "
            "Answer with exactly 'CS' if it is related, otherwise respond with 'Other'."
        ),
        "expected": "CS",
    },
    "SEO Classifier": {
        "goal": "Tell me if the input query is 'SEO' or 'Other'.",
        "backstory": (
            "You are an AI assistant trained to decide if a query specifically requests information regarding SEO or website ranking. "
            "Answer with exactly 'SEO' if it is SEO-related, otherwise respond with 'Other'."
        ),
        "expected": "SEO",
    },
    "Legal Classifier": {
        "goal": "Tell me if the input query is 'Legal' or 'Other'.",
        "backstory": (
            "You are an AI assistant trained to identify whether a query is related to legal matters. "
            "Answer with exactly 'Legal' if it is legal-related, otherwise respond with 'Other'."
        ),
        "expected": "Legal",
    },
}

# -------------------------------
# Define mapping to processing scripts
# -------------------------------
SCRIPT_PATHS = {
    "Medical Classifier": r"backend/medical_process.py",
    "Computer Science Classifier": r"backend/cs_process.py",
    "SEO Classifier": r"backend/seo_process.py",
    "Legal Classifier": r"backend/legal_process.py",
}

# -------------------------------
# Function: Call Gemini for classification
# -------------------------------
def classify_with_agent(agent_name: str, query: str) -> str:
    info = AGENTS_INFO[agent_name]
    prompt = (
        f"You are a {agent_name}. {info['backstory']}\n"
        f"Your goal: {info['goal']}\n"
        f"Only respond with '{info['expected']}' if the query is clearly and specifically about {info['expected'].lower()}-related topics. "
        f"Be strict in your classification. Do not classify vague or general queries as {info['expected']}. "
        f"Given the following query: \"{query}\", "
        f"reply with exactly \"{info['expected']}\" if it fits the category, otherwise reply with \"Other\"."
    )
    chat_session = model.start_chat(history=[])
    response = chat_session.send_message(prompt)
    return response.text.strip()

# -------------------------------
# Function: Run classification concurrently
# -------------------------------
def classify_query(query: str) -> dict:
    classifications = {}
    with ThreadPoolExecutor() as executor:
        future_to_agent = {
            executor.submit(classify_with_agent, agent_name, query): agent_name
            for agent_name in AGENTS_INFO
        }
        for future in as_completed(future_to_agent):
            agent = future_to_agent[future]
            try:
                result = future.result()
            except Exception as exc:
                result = f"Error: {exc}"
            classifications[agent] = result
    return classifications

# -------------------------------
# Function: Forward query to external script if applicable
# -------------------------------
def forward_to_script(script_path: str, query: str, user_id=None):
    try:
        # Pass the user_id as an additional parameter
        command = [sys.executable, script_path, query]
        if user_id:
            command.append(str(user_id))
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error while running {script_path}: {e}")
    except FileNotFoundError:
        print(f"Script {script_path} not found.")

# -------------------------------
# Main function
# -------------------------------
def main():
    # Authentication flow
    user = None
    while user is None:
        print("\n===== AUTHENTICATION =====")
        print("1. Login")
        print("2. Register")
        print("3. Exit")
        choice = input("Enter your choice (1-3): ")
        
        if choice == '1':
            user = login_user()
        elif choice == '2':
            user = register_user()
        elif choice == '3':
            print("Exiting program.")
            sys.exit(0)
        else:
            print("Invalid choice. Please try again.")
    
    # Main menu after successful authentication
    while True:
        print("\n===== MAIN MENU =====")
        print("1. Enter a query")
        print("2. Add doctor information")
        print("3. View doctor information")
        print("4. Logout")
        
        menu_choice = input("Enter your choice (1-4): ")
        
        if menu_choice == '1':
            # Process query
            query = input("\nEnter your query: ").strip()
            if not query:
                print("No query entered.")
                continue
            
            print("\nClassifying your query with multiple agents...\n")
            classifications = classify_query(query)
            
            print("Classification Results:")
            valid_categories = []
            for agent, result in classifications.items():
                print(f"{agent}: {result}")
                if result != "Other":
                    valid_categories.append(agent)
            
            if not valid_categories:
                response = "Please restate your question with more specific details related to medical issues, legal matters, computer science problems, or SEO optimization. We're here to help with professional consultation in these domains."
                print(f"\n{response}")
                save_to_conversation(user.get("_id"), query, response)
                continue
            
            # If multiple classifications apply, ask user to choose
            if len(valid_categories) > 1:
                print("\nYour query fits into multiple categories. Please choose one:")
                for idx, category in enumerate(valid_categories, start=1):
                    print(f"{idx}. {category}")

                while True:
                    try:
                        choice = int(input("\nEnter the number of your choice: "))
                        if 1 <= choice <= len(valid_categories):
                            selected_category = valid_categories[choice - 1]
                            break
                        else:
                            print("Invalid choice. Please select a valid number.")
                    except ValueError:
                        print("Invalid input. Please enter a number.")

            else:
                selected_category = valid_categories[0]

            print(f"\nSelected category: {selected_category}")
            script_path = SCRIPT_PATHS.get(selected_category)
            
            if script_path:
                print(f"\nForwarding your query to the script for {selected_category}...")
                forward_to_script(script_path, query, user.get("_id"))
                save_to_conversation(user.get("_id"), query, f"Processed by {selected_category}")
            else:
                print(f"\nNo script available for {selected_category}")
            
        elif menu_choice == '2':
            # Add doctor information
            add_doctor_info(user.get("_id"))
            
        elif menu_choice == '3':
            # View doctor information
            view_doctor_info(user.get("_id"))
            
        elif menu_choice == '4':
            # Logout
            print("Logging out...")
            break
            
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        query = sys.argv[1]
        print("\nClassifying query:", query)
        classifications = classify_query(query)
        
        print("Classification Results:")
        valid_categories = []
        for agent, result in classifications.items():
            print(f"{agent}: {result}")
            if result != "Other":
                valid_categories.append(agent)
        
        # If categories were found, automatically select the first one
        # (your Node.js server can handle multiple classifications if needed)
        if valid_categories:
            selected_category = valid_categories[0]
            print(f"\nSelected category: {selected_category}")
            
            script_path = SCRIPT_PATHS.get(selected_category)
            if script_path:
                print(f"\nForwarding query to {script_path}...")
                # Note: We don't have user_id in command line mode
                forward_to_script(script_path, query)
            else:
                print(f"\nNo script available for {selected_category}")
        else:
            print("\nNo matching categories found")
    else:
        main()  # Fallback to interactive mode if no arguments

def cleanup():
    try:
        genai.shutdown()  # Ensure Gemini API shuts down properly
    except Exception as e:
        print(f"Error shutting down gRPC: {e}", file=sys.stderr)

# Ensure cleanup runs when the script exits
atexit.register(cleanup)