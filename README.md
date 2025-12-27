# Wonderful_Home_Assignment
# AI Pharmacy Agent 

Assistant designed to mimic Pharmacy worker, help customers order medications, check stock levels, and check prescription status.
Based Only on medications in stock for this specific pharmacy, is not allowed to advice or to suggest other mediactions and\or treatments.

## Architecture
The project is built with a **modular architecture** using the following components:
**UI Layer:** Built with **Streamlit**, providing chat interface.
* **Brain:** Powered by **OpenAI's GPT-5**, utilizing **Function Calling** and the **ReAct (Reasoning and Acting) pattern**.
* **Database:** A synthetic database consisting of **JSON files** for medications and users, ensuring data persistence through **Docker Volumes**.
* **Infrastructure:** Fully containerized using **Docker** for easy deployment and environment consistency.

## Features
The agent follows a strict execution protocol:

1.  **Medication Information:** Provides dosage, purpose, and pricing.
2.  **Prescription Validation:** Checks if a drug requires a prescription and verifies the user's records before allowing an order.
3.  **Real-Time Inventory Management:** Automatically updates stock levels in the JSON database upon successful orders.

## How to Run (Docker)

### 1. Prerequisites
* Docker Desktop installed.
* An OpenAI API Key.

### 2. Change file
* open the file **run_bot.ps1**.
* change the env vairable called **OPENAI_API_KEY** to contain your openAI key.
* save the file
## 3.run file
* run the file using Powershell
* at this point the script will automatically build the container and initialize the Streamlit service.
## 4. open URL
* Now, the UI will be accessible at: [http://localhost:8501/](http://localhost:8501/)


