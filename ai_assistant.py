"""
AI Assistant for Online Voting System
Using LangChain for advanced conversational AI capabilities
"""

import os
from typing import Dict, List, Optional
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain.schema import HumanMessage, SystemMessage
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.text_splitter import CharacterTextSplitter

class VotingAIAssistant:
    def __init__(self, openai_api_key: Optional[str] = None):
        """
        Initialize the AI Assistant for the voting system
        
        Args:
            openai_api_key: OpenAI API key (optional, can be set via environment)
        """
        self.api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.llm = None
        self.memory = ConversationBufferMemory()
        self.conversation_chain = None
        self.vector_store = None
        
        print(f"Initializing AI Assistant...")
        print(f"API Key available: {'Yes' if self.api_key else 'No'}")
        
        if self.api_key:
            try:
                self._initialize_langchain()
                print("AI Assistant initialized successfully with LangChain")
            except Exception as e:
                print(f"Error initializing LangChain: {e}")
                print("Falling back to basic responses")
        else:
            print("Warning: OpenAI API key not found. Using fallback responses.")
            print("Please create a .env file with your OPENAI_API_KEY")
    
    def _initialize_langchain(self):
        """Initialize LangChain components"""
        try:
            # Initialize the language model
            self.llm = ChatOpenAI(
                temperature=0.7,
                model="gpt-4o-mini",
                openai_api_key=self.api_key
            )
            
            # Create conversation chain
            self.conversation_chain = ConversationChain(
                llm=self.llm,
                memory=self.memory,
                verbose=False
            )
            
            # Initialize vector store with voting system knowledge
            self._setup_knowledge_base()
            
        except Exception as e:
            print(f"Error initializing LangChain: {e}")
    
    def _setup_knowledge_base(self):
        """Setup knowledge base for voting system information"""
        voting_knowledge = """
        Online Voting System Features:
        1. User Registration: Users can register with email, username, and password
        2. Secure Authentication: Advanced encryption and secure login
        3. Election Management: Admins can create and manage elections
        4. Candidate Management: Add and manage election candidates
        5. Real-time Voting: Live vote casting with immediate updates
        6. Result Tracking: Real-time election results and statistics
        7. Security Features: Encrypted votes, anonymous voting, audit trails
        8. Admin Dashboard: Comprehensive admin interface for system management
        
        Voting Process:
        1. User registers/logs in
        2. Browse active elections
        3. Select an election
        4. View candidates and descriptions
        5. Cast vote for preferred candidate
        6. Confirm vote (cannot be changed)
        7. View real-time results
        
        Security Measures:
        - Advanced encryption for all votes
        - Anonymous voting (no personal data linked to votes)
        - Blockchain-like verification
        - Audit trails for transparency
        - No vote modification after submission
        - Secure authentication and session management
        
        Common Questions:
        - How to register: Click Register button, enter email and create password
        - How to vote: Login, browse elections, select candidate, confirm vote
        - Can I change my vote: No, votes cannot be modified after submission
        - Is voting secure: Yes, uses advanced encryption and anonymous voting
        - How long do elections last: Varies from 24 hours to 10 days
        - Can I see results: Yes, real-time results are available on election pages
        """
        
        try:
            # Split text into chunks
            text_splitter = CharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )
            texts = text_splitter.split_text(voting_knowledge)
            
            # Create embeddings and vector store
            embeddings = OpenAIEmbeddings(openai_api_key=self.api_key)
            self.vector_store = Chroma.from_texts(
                texts=texts,
                embedding=embeddings,
                collection_name="voting_system_knowledge"
            )
        except Exception as e:
            print(f"Error setting up knowledge base: {e}")
    
    def get_response(self, user_message: str, context: Optional[Dict] = None) -> str:
        """
        Get AI response for user message
        
        Args:
            user_message: User's input message
            context: Optional context (election data, user info, etc.)
        
        Returns:
            AI response string
        """
        if not self.llm:
            return self._get_fallback_response(user_message)
        
        try:
            # Create system prompt with context
            system_prompt = self._create_system_prompt(context)
            
            # Get response from LangChain
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_message)
            ]
            
            response = self.llm(messages)
            return response.content
            
        except Exception as e:
            print(f"Error getting AI response: {e}")
            return self._get_fallback_response(user_message)
    
    def _create_system_prompt(self, context: Optional[Dict] = None) -> str:
        """Create system prompt with context"""
        base_prompt = """You are an AI Assistant for an Online Voting System called NeuroVote. Your role is to help users with:

🎯 Voting Assistant: Help with registration, login, and vote-casting
💬 FAQ Responder: Answer common questions about the voting process
🧠 Interactive Help: Provide step-by-step guidance
🛡️ Security Advisor: Explain security features and privacy
📈 Election Summary: Provide election information and statistics
🗣️ General Conversation: Be friendly and conversational, not just functional
👨‍💼 Admin Support: Provide special assistance for administrators

IMPORTANT GUIDELINES:
- Be friendly, warm, and conversational - not just robotic
- Use emojis and clear formatting to make responses engaging
- If someone asks about non-voting topics, be helpful but gently guide them back to voting-related assistance
- For admins, provide more detailed technical and administrative support
- Keep responses concise but comprehensive
- Always maintain a helpful and positive tone
- If you don't understand something, ask for clarification or redirect to voting topics
- Be patient and understanding with users"""

        if context:
            context_str = f"\n\nCurrent Context:\n"
            for key, value in context.items():
                context_str += f"- {key}: {value}\n"
            base_prompt += context_str
        
        return base_prompt
    
    def _get_fallback_response(self, user_message: str) -> str:
        """Fallback responses when LangChain is not available"""
        message = user_message.lower()
        
        # Voting Assistant responses
        if any(word in message for word in ["register", "sign up", "create account"]):
            return "To register: 1) Click 'Register' in top navigation 2) Enter email 3) Create username/password 4) Verify email 5) Start voting! Need help with any step?"
        
        if any(word in message for word in ["vote", "cast vote", "election"]):
            return "Voting Process: 1) Login 2) Browse active elections 3) Select election 4) View candidates 5) Click 'Vote for [Candidate]' 6) Confirm choice. Your vote is encrypted and secure!"
        
        if any(word in message for word in ["login", "sign in"]):
            return "To login: 1) Click 'Login' 2) Enter username/email 3) Enter password 4) Click 'Login'. Forgot password? Contact support."
        
        # FAQ responses
        if any(word in message for word in ["change vote", "modify vote"]):
            return "Votes cannot be changed once submitted to maintain election integrity. Please review carefully before confirming."
        
        if any(word in message for word in ["how long", "duration", "time"]):
            return "Election duration varies: Student Council (7-10 days), Department polls (3-5 days), Quick surveys (24-48 hours)."
        
        # Security responses
        if any(word in message for word in ["secure", "safe", "privacy", "encryption"]):
            return "Security Features: 🔐 Advanced encryption, 🔒 Anonymous voting, 🛡️ Blockchain verification, 🔍 Audit trails, 🚫 No vote modification. Your vote is completely secure!"
        
        # Help responses
        if any(word in message for word in ["help", "support", "assist","hlp","Help",]):
            return "I'm your AI voting assistant! I can help with: Registration, Voting process, Security, Election info, Technical support. What do you need help with?"
        
        # General greetings and casual conversation
        if any(word in message for word in ["hello", "hi", "hey", "good morning", "good afternoon", "good evening", "how are you"]):
            return "Hello! 👋 I'm your AI assistant for NeuroVote. How can I help you today? I can assist with voting, registration, or just chat about anything!"
        
        # Thank you responses
        if any(word in message for word in ["thank you", "thanks", "appreciate", "grateful"]):
            return "You're very welcome! 😊 I'm happy to help. Is there anything else you'd like to know about voting or the system?"
        
        # Questions about the AI itself
        if any(word in message for word in ["who are you", "what are you", "your name", "ai", "artificial intelligence", "bot"]):
            return "I'm an AI assistant designed specifically for NeuroVote! 🤖 I help users with voting, registration, security questions, and general support. I'm here to make your voting experience smooth and enjoyable."
        
        # Default response - more conversational
        return "That's interesting! 🤔 I'm primarily here to help with voting, but I'm happy to chat. Is there anything about the voting system you'd like to know, or do you have other questions?"

# Global instance
ai_assistant = VotingAIAssistant()

def get_ai_response(user_message: str, context: Optional[Dict] = None) -> str:
    """Global function to get AI response"""

    return ai_assistant.get_response(user_message, context) 
