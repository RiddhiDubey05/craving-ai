
# 🍽️ CravingAI

**The smartest way to discover your next meal.**

Have you ever spent 30 minutes scrolling through food delivery apps, overwhelmed by choices, only to end up ordering the same thing you always do? We believe finding great food shouldn't feel like a chore. It should feel like discovering a hidden gem.

CravingAI exists to solve the "what should I eat?" fatigue. We combined the visual inspiration of Pinterest, the seamless discovery of Swiggy/Zomato, and the intelligence of a personal AI concierge into one fluid experience. 

Whether you're craving "something spicy and warm for a rainy day" or looking for the highest-rated vegan spot under $15, CravingAI understands your exact mood, budget, and taste.

---

## 🌟 The Experience

CravingAI isn't just a search bar—it's a personalized food discovery engine. 

### 🧭 Explore What's Good
Drop into our **Explore Feed** to instantly see what's trending globally, uncover highly-rated hidden gems, and find the best meals under budget. No searching required.

### 🤖 Chat with Your Personal Food Concierge
Don't know what you want? Just ask. 
*“I just finished a heavy workout and need high-protein Mediterranean food nearby.”* 
Our AI concierge will instantly analyze your request, chat with you about your preferences, and present curated, real-time dish recommendations alongside the conversation.

### 📸 Search by Vibe (Multimodal AI)
Sometimes you don't have the words for what you want—you just have a craving. Drag and drop a photo of a dish, adjust the slider to balance visual similarity with your text instructions, and let our Multimodal AI find exactly what you're looking for.

### 🛒 Seamless Checkout & Cart
Found something you love? Add it to your cart, adjust quantities, and check out instantly with our beautiful, frictionless slide-over UI.

---

## 🛠️ Built for Scale (The Tech)

While CravingAI feels simple and human on the outside, it is powered by a robust, production-grade AI backend built to handle scale and complexity.

- **The Brain:** Powered by AWS Bedrock (Claude 3.5 Sonnet) for natural language reasoning and Titan Multimodal Embeddings for processing image + text queries.
- **The Engine:** A lightning-fast FAISS vector database enables real-time semantic retrieval of thousands of dishes.
- **The Platform:** A high-performance FastAPI Python backend seamlessly connected to a modern, glassmorphic UI via vanilla JS/HTML/CSS for maximum speed.
- **The Infrastructure:** Fully containerized with Docker, featuring automatic data seeding and local fallbacks for seamless deployment anywhere.

---

## 🚀 Get Started

Want to run CravingAI locally? It takes less than 2 minutes.

### 1. Configure the Environment
Clone the repository and set up your environment variables.
```bash
cp .env.example .env
# Edit .env with your AWS credentials or SMTP settings if you wish to use real emails
```

### 2. Run with Docker (Recommended)
Launch the fully orchestrated environment in one command:
```bash
docker compose up --build
```
*Visit **http://localhost:8000** to experience CravingAI.*

### 3. Run Locally (Manual)
If you prefer to run it outside of Docker:
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Or .\venv\Scripts\activate on Windows

# Install dependencies
pip install -r backend/requirements.txt

# Start the API server
python -m uvicorn backend.main:app --port 8000 --reload
```

---

*Designed and engineered for food lovers who want more than just a list of restaurants.*
