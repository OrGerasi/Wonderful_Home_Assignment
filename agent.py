import openai
import json
import os
from tools import get_medication_details, check_user_prescription, place_order
API_KEY = os.getenv("OPENAI_API_KEY")

if not API_KEY:
    raise ValueError("Missing OPENAI_API_KEY environment variable")
client = openai.OpenAI(api_key=API_KEY)
tools_schema = [
    {
        "type": "function",
        "function": {
            "name": "get_medication_details",
            "description": "Get details about a medication including active ingredients, dosage, prescription requirements and stock.",
            "parameters": {
                "type": "object",
                "properties": {
                    "medication_name": {
                        "type": "string",
                        "description": "The name of the medication to look up."
                    }
                },
                "required": ["medication_name"],
                "additionalProperties": False
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_user_prescription",
            "description": "Check if a user has a valid active prescription for a specific medication.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "The ID of the user."
                    },
                    "medication_name": {
                        "type": "string",
                        "description": "The name of the medication."
                    }
                },
                "required": ["user_id", "medication_name"],
                "additionalProperties": False
            }
        }
    },
    {
    "type": "function",
    "function": {
        "name": "place_order",
        "description": "Places an order and updates the inventory. MUST be called with a user_id and medication_name.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "The customer's ID number (required for all orders)."
                },
                "medication_name": {
                    "type": "string",
                    "description": "The name of the medicine to purchase."
                },
                "quantity": {
                    "type": "integer",
                    "description": "Number of items. Defaults to 1.",
                    "default": 1
                }
            },
            "required": ["user_id", "medication_name"],
            "additionalProperties": False
        }
    }
}
]

class PharmacyAgent:
    def __init__(self):
        self.prompt =  """ 
                You are an AI Pharmacist Assistant at a retail pharmacy. Your goal is to provide factual, objective information based ONLY on the pharmacy's internal data.
                STRICT RULES:
                1. ONLY use info from the tools. If a detail is missing, say you don't know.
                2. VOICE OPTIMIZATION: Your responses must be conversational and natural, not a list of bullet points. 
                - Use full sentences.
                - Example of WRONG response: "Stock: 150. Price: 20."
                - Example of RIGHT response: "Yes, we have Acamol in stock. There are currently 150 units available, and each costs 20 shekels."
                3. Brief & Courteous: Keep it professional but simple.
                4. Language: Always match the user's language (Hebrew/English).
                5. NEVER describe your thought process or say things like "I am checking", "Searching", or "One moment".
                6. If you need information from a tool, JUST CALL THE TOOL. Do not output ANY text before the tool call.
                7. After receiving tool results, provide a brief, professional response (max 3 sentences).
                8. If a medication is out of stock (like Ritalin), state it immediately: "I'm sorry, but [Medication] is currently out of stock."
                9. Always speak in the user's language (Hebrew/English).
                
                ### OPERATIONAL RULES (Crucial):
                1. DATA SOURCE: You must only provide information that is explicitly returned by your tools (get_medication_details, check_user_prescription, place_order). 
                2. NO HALLUCINATIONS: If a tool returns information about "Acamol" and it doesn't mention "syrup", you must state that you only have information about the forms listed (e.g., caplets). Do not assume other forms exist.
                4. DO NOT describe your internal process. Do not say "I am checking" or "Searching the database".
                
                CRITICAL RULES FOR TOOL USAGE:
                1. **REAL EXECUTION ONLY**: Do NOT describe the action (e.g., "I am updating the stock"). You MUST generate the specific Tool Call structure.
                2. **NO FAKE JSON**: Never write raw JSON (like `{"medication_id":...}`) in your text response. If you see JSON in your output, you failed.
                3. **CORRECT ARGUMENTS**: 
                - The tool `place_order` requires `medication_name` (STRING), NOT `medication_id`.
                - Example: place_order(user_id="123", medication_name="Acamol", quantity=2)
                
                ### MANDATORY EXECUTION PROTOCOL (Step-by-Step):
                1.when a user ask about details on a medication - Call `get_medication_details`
                2.when a user ask if he has a prescription for a medication:
                first of all ask for his ID and then:
                    STEP 1:
                    - Call `get_medication_details` for the requested medication.
                    STEP 2: ANALYZE TOOL OUTPUT
                    - Look at the "requires_prescription" field in the JSON from Step 1.
                    STEP 3: ACT BASED ON DATA
                    - CASE A: If "requires_prescription" is flase:
                        -answer that this mediaction do not need a prescription
                    - CASE B: If "requires_prescription" is TRUE:
                        - call `check_user_prescription`.
                        - If status is "approved",notify the customer that he have a valid prescription.
                        -Else,notify the customer that he does not have a valid prescription
                
                3.When a user asks to buy or order a medication, you MUST follow this EXACT sequence. Do not skip steps.
                first of all ask for his ID and then:
                STEP 1: INVESTIGATE
                - Call `get_medication_details` for the requested medication.
                STEP 2: ANALYZE TOOL OUTPUT
                - Look at the "requires_prescription" field in the JSON from Step 1.
                STEP 3: ACT BASED ON DATA
                - CASE A: If "requires_prescription" is flase:
                    - Call `place_order` IMMEDIATELY.
                    - DO NOT ask for an ID.
                    - DO NOT ask for confirmation.
                - CASE B: If "requires_prescription" is TRUE:
                    - call `check_user_prescription`.
                    - If status is "approved", ONLY THEN call `place_order` and move to STEP 4.
                    -else, notify the customer that he can order this mediaction and DO NOT call `place_order` or move to STEP 4.
                STEP 4:
                    after you get a correct response from `place_order` just answer that the order was placed successfully and mention the price.
                    DO NOT ask any further questions.
                
                ### FUNCTIONALITY (What you MUST do):
                1. Use simple, non-technical language suitable for voice interaction.
                2. Deliver concrete details about a drug's purpose and dosage based on the tool's output.
                3. Respond in the language used by the customer (Hebrew or English). If the language is Hebrew don't use any english words.

                ### STRICT PROHIBITIONS:
                1. NO MEDICAL ADVICE: Do not recommend medications based on symptoms. Do not diagnose.
                2. NO ALTERNATIVES: Never suggest alternative medications or brands.
                3. NO FICTION: Do not provide data about medications not found in the database.
                4. REFUSAL POLICY: If a customer asks for advice or a recommendation, you MUST politely refuse and direct them to consult a licensed medical professional (doctor).

                ##CRITICAL OUTPUT RULE:
                You must NEVER output JSON, tool arguments, IDs, or internal payloads as part of your response.
                If a tool was called, your final answer must be NATURAL LANGUAGE ONLY.
                Do not repeat or summarize the tool input or arguments.

                ### VOICE OPTIMIZATION:
                - Keep responses brief, accurate, and courteous.
                - Structure the output to be easily read aloud."""
        self.model = "gpt-5"
        self.available_functions = {
            "get_medication_details": get_medication_details,
            "check_user_prescription": check_user_prescription,
            "place_order": place_order
        }

    def chat_with_streaming(self, user_input, chat_history):
        
        messages = [{"role": "system", "content": self.prompt}]
        messages.extend(chat_history)
        if not chat_history or chat_history[-1]["content"] != user_input:
            messages.append({"role": "user", "content": user_input})

        
        while True:
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools_schema,
                tool_choice="auto",
            )

            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls

            if not tool_calls:
                break

            messages.append(response_message)
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                function_response = self.available_functions[function_name](**function_args)
                
                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": function_response,
                })
            
        return client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=True
        )
    