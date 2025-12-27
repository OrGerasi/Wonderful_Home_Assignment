import json
import os



MEDICATIONS_PATH = os.path.join("data", "medications.json")
USERS_PATH = os.path.join("data", "users.json")
# --- 1. Database Loading ---
def load_data() -> tuple[list[dict], list[dict]]:
    """
    Loads the synthetic database from JSON files.
    Returns:
        tuple: (medications_list, users_list) or ([], []) if an error occurs.
    """
    try:
        with open(MEDICATIONS_PATH, 'r', encoding='utf-8') as f:
            meds = json.load(f)
        with open(USERS_PATH, 'r', encoding='utf-8') as f:
            users = json.load(f)
        return meds, users
    except FileNotFoundError as e:
        print(f"Error loading database: {e}")
        return [], []



# --- 2. Helper Functions ---
def _find_medication(name: str, medications_db: list[dict]) -> dict | None:
    """
    Searches for a medication in the database by its name or aliases.
    Args:
        name (str): The search term (Hebrew or English).
        medications_db (list): The list of medication dictionaries.
    Returns:
        dict: The medication object if found, else None.
    """
    search_term = name.lower().strip()
    for med in medications_db:
        # בדיקה אם השם שהוזן נמצא ברשימת השמות לחיפוש
        if search_term in [n.lower() for n in med.get('search_names', [])]:
            return med
        # ליתר ביטחון, בדיקה גם מול השם הראשי
        if search_term == med['name'].lower():
            return med
    return None

def _find_user(user_id: str, user_db: list[dict]) -> dict | None:
    """
    Locates a user in the database by their ID.
    Args:
        user_id (str): The unique user identification string.
        user_db (list): The list of user dictionaries.
    Returns:
        dict: The user object if found, else None.
    """
    for user in user_db:
        if user['id'] == user_id:
            return user
    return None

# --- 3. The Tools (Exposed to the Agent) ---

def get_medication_details(medication_name: str) -> str:
    """
    Retrieves comprehensive details about a specific medication.
    Args:
        medication_name (str): The name of the medication to look up.
    Returns:
        str: A JSON-formatted string containing medication details or an error message.
    """
    meds_db, users_db = load_data()
    med = _find_medication(medication_name,meds_db)
    
    if not med:
        return json.dumps({"error": f"Medication '{medication_name}' not found."})
    
    # Return all relevant details as a JSON string
    return json.dumps(med)

def check_user_prescription(user_id: str, medication_name: str) -> str:
    """
    Verifies if a user has a valid prescription for a medication or if it's OTC.
    Args:
        user_id (str): The ID of the user requesting the medication.
        medication_name (str): The name of the medication to check.
    Returns:
        str: A JSON string with status (approved/denied) and the reasoning.
    """
    meds_db,users_db = load_data()
    user = _find_user(user_id,users_db)
    if not user:
        return json.dumps({"error": "User not found."})

    med = _find_medication(medication_name,meds_db)
    if not med:
        return json.dumps({"error": f"Medication '{medication_name}' not found."})

    # If the medication does not require a prescription, return true immediately
    if not med.get('requires_prescription', False):
        return json.dumps({
            "status": "approved", 
            "reason": "Medication is Over-The-Counter (OTC), no prescription needed."
        })

    # Check if the medication ID is in the user's active prescriptions
    if med['id'] in user.get('active_prescriptions', []):
        return json.dumps({
            "status": "approved", 
            "reason": "Valid prescription found."
        })
    else:
        return json.dumps({
            "status": "denied", 
            "reason": "No active prescription found for this medication."
        })

def place_order(user_id: str, medication_name: str, quantity: int = 1) -> str:
    """
    Processes a medication order, validates stock, and updates the database.
    Args:
        user_id (str): The ID of the ordering user.
        medication_name (str): The name of the medication to order.
        quantity (int): The number of units to order (default is 1).
    Returns:
        str: A JSON string indicating success with new stock levels or a failure message.
    """
    meds_db, users_db = load_data()
    med = _find_medication(medication_name, meds_db)
    user = _find_user(user_id, users_db)

    if not user or not med:
        return json.dumps({"status": "failed", "error": "User or Medication not found"})

    if med['stock_quantity'] < quantity:
        return json.dumps({"status": "failed", "error": "Out of stock"})

    med['stock_quantity'] -= quantity

    try:
        with open(MEDICATIONS_PATH, 'w', encoding='utf-8') as f:
            json.dump(meds_db, f, indent=2, ensure_ascii=False)
        return json.dumps({"status": "success", "new_stock": med['stock_quantity']})
    except Exception as e:
        return json.dumps({"status": "failed", "error": str(e)})
