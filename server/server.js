const express = require('express');
const { spawn } = require('child_process');
const bodyParser = require('body-parser');
const cors = require('cors');
const jwt = require('jsonwebtoken');
const bcrypt = require('bcrypt');
const fs = require('fs');
const path = require('path');
const nodemailer = require('nodemailer');

const app = express();
const PORT = process.env.PORT || 5001;
const JWT_SECRET = 'skill-seeker-secret-key'; // In production, use environment variables

// Middleware
app.use(cors({
  origin: '*', // Allow all origins for testing
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization'],
  credentials: true
}));
app.use(bodyParser.json());

// Root route for testing
app.get('/', (req, res) => {
  res.send('Skill Seeker API is running');
});

// API test route
app.get('/api/test', (req, res) => {
  res.json({ message: 'API test successful' });
});

// Simple user storage (replace with a database in production)
const USERS_FILE = path.join(__dirname, 'users.json');

const loadUsers = () => {
  try {
    if (fs.existsSync(USERS_FILE)) {
      return JSON.parse(fs.readFileSync(USERS_FILE));
    }
    return [];
  } catch (error) {
    console.error('Error loading users:', error);
    return [];
  }
};

const saveUsers = (users) => {
  try {
    fs.writeFileSync(USERS_FILE, JSON.stringify(users, null, 2));
  } catch (error) {
    console.error('Error saving users:', error);
  }
};

// Authentication endpoints
app.post('/api/auth/signup', async (req, res) => {
  const { name, email, password } = req.body;
  const users = loadUsers();
  
  // Check if user already exists
  if (users.find(user => user.email === email)) {
    return res.status(400).json({ message: 'User already exists' });
  }
  
  // Hash password
  const salt = await bcrypt.genSalt(10);
  const hashedPassword = await bcrypt.hash(password, salt);
  
  // Create new user
  const newUser = { id: Date.now().toString(), name, email, password: hashedPassword };
  users.push(newUser);
  saveUsers(users);
  
  res.status(201).json({ message: 'User created successfully' });
});

app.post('/api/auth/login', async (req, res) => {
  const { email, password } = req.body;
  const users = loadUsers();
  
  // Find user
  const user = users.find(user => user.email === email);
  if (!user) {
    return res.status(400).json({ message: 'Invalid email or password' });
  }
  
  // Validate password
  const validPassword = await bcrypt.compare(password, user.password);
  if (!validPassword) {
    return res.status(400).json({ message: 'Invalid email or password' });
  }
  
  // Generate JWT token
  const token = jwt.sign({ id: user.id, email: user.email }, JWT_SECRET, { expiresIn: '1h' });
  
  res.json({ token, name: user.name });
});

// Middleware to verify token
const verifyToken = (req, res, next) => {
  const token = req.headers.authorization?.split(' ')[1];
  
  if (!token) {
    return res.status(401).json({ message: 'Access denied. No token provided.' });
  }
  
  try {
    const verified = jwt.verify(token, JWT_SECRET);
    req.user = verified;
    next();
  } catch (error) {
    res.status(400).json({ message: 'Invalid token' });
  }
};

// Query processing endpoints
app.post('/api/query/classify', (req, res) => {
  console.log('Received classification request', req.body);
  const { query } = req.body;
  
  if (!query) {
    return res.status(400).json({ message: 'Query is required' });
  }
  
  // Pass only the query to the Python classifier
  const processingQuery = query;
  
  const python = spawn('python', [path.join(__dirname, 'backend', 'main.py'), processingQuery]);
  let dataBuffer = '';
  
  python.stdout.on('data', (data) => {
    dataBuffer += data.toString();
  });
  
  python.stderr.on('data', (data) => {
    console.error(`Python stderr: ${data}`);
  });
  
  python.on('close', (code) => {
    if (code !== 0) {
      return res.status(500).json({ message: 'Classification failed' });
    }
    
    // Parse the classification outputs from the script
    try {
      console.log("Raw classification output:", dataBuffer);
      
      // Extract classification results from the output
      const classificationLines = dataBuffer.split('\n').filter(line => 
        line.includes('Classification Results:') || 
        (line.includes('Classifier') && (line.includes('Medical') || line.includes('CS') || line.includes('SEO') || line.includes('Legal') || line.includes('Other')))
      );
      
      console.log("Filtered classification lines:", classificationLines);
      
      const classifications = {};
      classificationLines.forEach(line => {
        if (line.includes('Classifier')) {
          const parts = line.split(':');
          if (parts.length === 2) {
            const classifier = parts[0].trim();
            const result = parts[1].trim();
            classifications[classifier] = result;
          }
        }
      });
      
      console.log("Final classifications object:", classifications);
      
      // Return only the classifications and the original query
      res.json({ 
        classifications,
        originalQuery: query
      });
    } catch (error) {
      console.error('Error parsing classification output:', error);
      res.status(500).json({ message: 'Failed to parse classification results' });
    }
  });
});

// FIXED: Corrected the process endpoint
app.post('/api/query/process', (req, res) => {
  // Extract the category and query from req.body
  const { category, query } = req.body;
  
  console.log(`Processing query in category: "${category}"`);
  console.log(`Original query: "${query}"`);
  
  // Enhanced validation and debugging
  if (!category) {
    console.error('Category is missing or undefined');
    return res.status(400).json({ message: 'Category is required' });
  }
  
  if (!query) {
    console.error('Query is missing or undefined');
    return res.status(400).json({ message: 'Query is required' });
  }
  
  // Normalize category for more reliable comparison
  const categoryLower = category.toLowerCase();
  
  // Use the query directly, without location handling
  let queryText = query;
  
  let scriptPath;
  
  // Map category to the appropriate script with more flexibility
  if (categoryLower.includes('medical')) {
    scriptPath = 'medical_process.py';
  } else if (categoryLower.includes('legal')) {
    scriptPath = 'legal_process.py';
  } else if (categoryLower.includes('cs') || categoryLower.includes('computer') || categoryLower.includes('tech')) {
    scriptPath = 'cs_process.py';
  } else if (categoryLower.includes('seo')) {
    scriptPath = 'seo_process.py';
  } else {
    console.error(`Unrecognized category: "${category}"`);
    return res.status(400).json({ message: 'Invalid category' });
  }
  
  console.log(`Selected script path: ${scriptPath}`);
  console.log(`Final query being sent to Python: "${queryText}"`);
  
  // Execute Python script directly with the query parameter
  const pythonPath = path.join(__dirname, 'backend', scriptPath);
  
  // Check if the script file exists
  if (!fs.existsSync(pythonPath)) {
    console.error(`Python script not found at: ${pythonPath}`);
    return res.status(500).json({ message: `Script not found: ${scriptPath}` });
  }
  
  console.log(`Executing Python script: ${pythonPath} with query: "${queryText}"`);
  
  const python = spawn('python', [pythonPath, queryText]);
  
  let dataBuffer = '';
  
  python.stdout.on('data', (data) => {
    dataBuffer += data.toString();
    console.log(`Python stdout chunk: ${data}`);
  });
  
  python.stderr.on('data', (data) => {
    console.error(`Python stderr: ${data}`);
  });
  
  python.on('close', (code) => {
    console.log(`Python process exited with code ${code}`);
    console.log(`Full output: ${dataBuffer}`);
    
    if (code !== 0) {
      return res.status(500).json({ message: 'Processing failed', error: `Exit code: ${code}` });
    }
    
    try {
      // Find the JSON output in the response
      let jsonStart = dataBuffer.indexOf('{');
      let jsonEnd = dataBuffer.lastIndexOf('}') + 1;
      
      if (jsonStart >= 0 && jsonEnd > 0) {
        const jsonData = dataBuffer.substring(jsonStart, jsonEnd);
        console.log(`Extracted JSON data: ${jsonData}`);
        const result = JSON.parse(jsonData);
        
        // Check for error
        if (result.error) {
          return res.status(500).json({ message: result.error });
        }
        
        // Generate a unique process ID
        const processId = Date.now().toString();
        
        // Store process information (without location)
        activeProcesses[processId] = {
          category,
          query: queryText,
          synthesis: result.synthesis,
          questions: result.questions
        };
        
        res.json({
          processId,
          status: 'questions',
          synthesis: result.synthesis,
          questions: result.questions
        });
      } else {
        throw new Error('No valid JSON found in output');
      }
    } catch (error) {
      console.error('Error parsing Python output:', error);
      console.error('Raw output:', dataBuffer);
      res.status(500).json({ message: 'Failed to parse processing results', error: error.message });
    }
  });
});

// Store active Python processes
const activeProcesses = {};

// Submit answers to follow-up questions
app.post('/api/query/submit-answers', (req, res) => {
  const { processId, answers } = req.body;
  
  console.log(`Received answers for process ${processId}:`, answers);
  
  if (!processId || !activeProcesses[processId]) {
    return res.status(400).json({ message: 'Invalid process ID' });
  }
  
  const process = activeProcesses[processId];
  const { category, query, synthesis, questions } = process;
  let scriptPath;
  
  // Normalize category for more reliable comparison
  const categoryLower = category.toLowerCase();
  
  // Map category to the appropriate script with more flexibility
  if (categoryLower.includes('medical')) {
    scriptPath = 'medical_process.py';
  } else if (categoryLower.includes('legal')) {
    scriptPath = 'legal_process.py';
  } else if (categoryLower.includes('cs') || categoryLower.includes('computer') || categoryLower.includes('tech')) {
    scriptPath = 'cs_process.py';
  } else if (categoryLower.includes('seo')) {
    scriptPath = 'seo_process.py';
  } else {
    return res.status(400).json({ message: 'Invalid category' });
  }
  
  // Create a temporary file to store answers
  const answersArray = questions.map(q => answers[q] || '');
  const answersJson = JSON.stringify(answersArray);
  const tempAnswersFile = path.join(__dirname, `temp_answers_${processId}.json`);
  
  console.log(`Processing answers with ${scriptPath}`);
  console.log(`Answers data: ${answersJson}`);
  
  // Write answers to temp file
  fs.writeFileSync(tempAnswersFile, answersJson);
  
  // Execute Python script to get ranked professionals
  const pythonPath = path.join(__dirname, 'backend', scriptPath);
  
  // Check if the script file exists
  if (!fs.existsSync(pythonPath)) {
    console.error(`Python script not found at: ${pythonPath}`);
    return res.status(500).json({ message: `Script not found: ${scriptPath}` });
  }
  
  console.log(`Executing Python script: ${pythonPath} with query: "${query}" and answers file: ${tempAnswersFile}`);
  
  const python = spawn('python', [pythonPath, query, tempAnswersFile]);
  
  let dataBuffer = '';
  
  python.stdout.on('data', (data) => {
    dataBuffer += data.toString();
    console.log(`Python stdout: ${data}`);
  });
  
  python.stderr.on('data', (data) => {
    console.error(`Python stderr: ${data}`);
  });
  
  python.on('close', (code) => {
    console.log(`Python process exited with code ${code}`);
    console.log(`Full output: ${dataBuffer}`);
    
    // Clean up
    if (fs.existsSync(tempAnswersFile)) {
      fs.unlinkSync(tempAnswersFile);
    }
    
    if (code !== 0) {
      delete activeProcesses[processId];
      return res.status(500).json({ 
        message: 'Processing failed', 
        error: `Exit code: ${code}` 
      });
    }
    
    try {
      // Find the JSON output in the response
      let jsonStart = dataBuffer.indexOf('{');
      let jsonEnd = dataBuffer.lastIndexOf('}') + 1;
      
      if (jsonStart >= 0 && jsonEnd > 0) {
        const jsonData = dataBuffer.substring(jsonStart, jsonEnd);
        console.log(`Extracted JSON data: ${jsonData}`);
        const result = JSON.parse(jsonData);
        
        // Check for error
        if (result.error) {
          delete activeProcesses[processId];
          return res.status(500).json({ message: result.error });
        }
        
        // Extract professionals based on category
        let professionals = [];
        if (categoryLower.includes('medical')) {
          professionals = result.doctors || [];
        } else if (categoryLower.includes('legal')) {
          professionals = result.lawyers || [];
        } else if (categoryLower.includes('cs') || categoryLower.includes('computer') || categoryLower.includes('tech')) {
          professionals = result.professionals || [];
        } else if (categoryLower.includes('seo')) {
          professionals = result.services || [];
        }
        
        // If no professionals were found, return an error
        if (!professionals || professionals.length === 0) {
          console.log('No professionals found in the result');
          delete activeProcesses[processId];
          return res.status(404).json({ 
            message: 'No professionals found matching the criteria'
          });
        }
        
        // Clean up the process
        delete activeProcesses[processId];
        
        res.json({
          status: 'results',
          professionals
        });
      } else {
        throw new Error('No valid JSON found in output');
      }
    } catch (error) {
      console.error('Error parsing Python output:', error);
      console.error('Raw output:', dataBuffer);
      delete activeProcesses[processId];
      res.status(500).json({ 
        message: 'Failed to parse professional results', 
        error: error.message 
      });
    }
  });
});

// Ask follow-up questions during the conversation phase
app.post('/api/query/conversation', (req, res) => {
  const { category, query, synthesis, professionals, followUpQA, question } = req.body;
  let scriptPath;
  
  console.log(`Processing conversation in category: "${category}"`);
  
  // Normalize category for more reliable comparison
  const categoryLower = category ? category.toLowerCase() : '';
  
  // Map category to the appropriate script with more flexibility
  if (categoryLower.includes('medical')) {
    scriptPath = 'medical_process.py';
  } else if (categoryLower.includes('legal')) {
    scriptPath = 'legal_process.py';
  } else if (categoryLower.includes('cs') || categoryLower.includes('computer') || categoryLower.includes('tech')) {
    scriptPath = 'cs_process.py';
  } else if (categoryLower.includes('seo')) {
    scriptPath = 'seo_process.py';
  } else {
    return res.status(400).json({ message: 'Invalid category' });
  }
  
  // Check if script exists
  const scriptFullPath = path.join(__dirname, 'backend', scriptPath);
  if (!fs.existsSync(scriptFullPath)) {
    console.error(`Conversation script not found: ${scriptFullPath}`);
    return res.status(500).json({ 
      message: 'Script not found',
      response: "I apologize, but I can't process your question right now due to a technical issue."
    });
  }
  
  // Create a temporary file to store memory data
  const memoryFileName = path.join(__dirname, `temp_memory_${Date.now()}.json`);
  const memoryData = {
    query,
    synthesis_result: synthesis,
    followup_qa: followUpQA
  };
  
  // Add professionals based on category
  if (categoryLower.includes('medical')) {
    memoryData.ranked_doctors = JSON.stringify({ doctors: professionals });
  } else if (categoryLower.includes('legal')) {
    memoryData.ranked_lawyers = JSON.stringify({ lawyers: professionals });
  } else if (categoryLower.includes('cs') || categoryLower.includes('computer') || categoryLower.includes('tech')) {
    memoryData.ranked_professionals = JSON.stringify({ professionals });
  } else if (categoryLower.includes('seo')) {
    memoryData.ranked_services = JSON.stringify({ services: professionals });
  }
  
  fs.writeFileSync(memoryFileName, JSON.stringify(memoryData));
  
  // Create a temporary Python file for conversation
  const tempConversationScriptName = path.join(__dirname, `temp_conversation_${Date.now()}.py`);
  
  const conversationScript = `
import os
import sys
import json

# Add backend directory to path
sys.path.append(os.path.join('${__dirname.replace(/\\/g, "/")}', 'backend'))

# Import the correct module
try:
    from ${scriptPath.replace('.py', '')} import get_conversational_response
    
    # Load memory data
    with open('${memoryFileName.replace(/\\/g, "/")}', "r") as f:
        memory_data = json.loads(f.read())
    
    # Get and print response
    response = get_conversational_response(memory_data, "${question.replace(/"/g, '\\"')}")
    print(response)
except Exception as e:
    print(f"Error in conversation script: {str(e)}", file=sys.stderr)
    print("I apologize, but I'm having trouble processing your question. Can you try asking something else?")
`;
  fs.writeFileSync(tempConversationScriptName, conversationScript);
  
  // Execute the temporary Python file
  const python = spawn('python', [tempConversationScriptName]);
  
  let responseBuffer = '';
  
  python.stdout.on('data', (data) => {
    responseBuffer += data.toString();
  });
  
  python.stderr.on('data', (data) => {
    console.error(`Python stderr: ${data}`);
  });
  
  python.on('close', (code) => {
    // Clean up temporary files
    if (fs.existsSync(memoryFileName)) {
      fs.unlinkSync(memoryFileName);
    }
    if (fs.existsSync(tempConversationScriptName)) {
      fs.unlinkSync(tempConversationScriptName);
    }
    
    if (code !== 0) {
      console.error(`Conversation process exited with code ${code}`);
      return res.status(500).json({ 
        message: 'Conversation processing failed',
        response: "I apologize, but I'm having trouble processing your question. Can you try asking something else?"
      });
    }
    
    res.json({ response: responseBuffer.trim() });
  });
});

// Add this near the top of your routes (after middleware)
app.get('/api/test-endpoint', (req, res) => {
  console.log('Test endpoint hit');
  res.json({ success: true, message: 'API is working' });
});

// Email sending endpoint - commented out for security
/*
app.post('/api/email/send-smtp', (req, res) => {
  console.log('Email endpoint hit with body:', req.body);
  
  // Ensure proper headers
  res.setHeader('Content-Type', 'application/json');
  
  const { userEmail, message, professional, query } = req.body;
  
  if (!userEmail || !message) {
    return res.status(400).json({ success: false, message: 'Email and message are required' });
  }
  
  // Create transporter
  const transporter = nodemailer.createTransport({
    service: 'gmail', // replace with your email service
    auth: {
      user: 'i212654@nu.edu.pk', // replace with your email
      pass: 'sstqrxtleyoysrrb' // replace with your app key/password
    }
  });
  
  // Email options
  const mailOptions = {
    from: 'i212654@nu.edu.pk',
    to: 'i212654@nu.edu.pk',
    cc: userEmail,
    subject: `New Query: ${query || 'General inquiry'}`,
    html: `
      <h2>New message regarding: ${query || 'General inquiry'}</h2>
      <p><strong>From:</strong> ${userEmail}</p>
      <p><strong>For Professional:</strong> ${professional ? (professional['Doctor Name'] || professional.Name || 'Professional') : 'Professional'}</p>
      <hr />
      <p>${message}</p>
    `
  };
  
  // Send email
  transporter.sendMail(mailOptions, (error, info) => {
    if (error) {
      console.error('Email sending error:', error);
      return res.status(500).json({ success: false, message: 'Failed to send email', error: error.message });
    }
    
    console.log('Email sent:', info.response);
    res.json({ success: true, message: 'Email sent successfully' });
  });
});
*/

// Simple test endpoint for emails
app.post('/api/email/simple-send', (req, res) => {
  console.log('Simple email endpoint hit with body:', req.body);
  
  // Just log the email details and return success
  const { userEmail, message, professional, query } = req.body;
  
  console.log('Would send email:');
  console.log('From:', userEmail);
  console.log('To: i212654@nu.edu.pk');
  console.log('Message:', message);
  console.log('Query:', query);
  console.log('Professional:', professional);
  
  // Return a simple success response
  return res.json({ success: true, message: 'Email details logged (not actually sent)' });
});

app.post('/api/simple-test', (req, res) => {
  console.log('Received request:', req.body);
  res.json({ message: 'Test successful', receivedData: req.body });
});

// Start server
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});