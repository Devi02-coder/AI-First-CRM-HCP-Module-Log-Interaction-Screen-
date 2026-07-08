import os
import json
import re
import datetime
from typing import Dict, Any, List, Optional
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
PRIMARY_MODEL = os.getenv("PRIMARY_MODEL", "gemma2-9b-it")
FALLBACK_MODEL = os.getenv("FALLBACK_MODEL", "llama-3.3-70b-versatile")

class GroqClient:
    def __init__(self):
        self.client = None
        if GROQ_API_KEY and GROQ_API_KEY.strip() != "" and GROQ_API_KEY != "YOUR_GROQ_API_KEY":
            try:
                self.client = Groq(api_key=GROQ_API_KEY)
                print("Groq Client initialized successfully.")
            except Exception as e:
                print(f"Failed to initialize Groq Client: {e}. Falling back to Rule-based parser.")
        else:
            print("No GROQ_API_KEY found. Running in Rule-based Fallback Mock Mode.")

    def _call_llm(self, system_prompt: str, user_prompt: str, response_format_json: bool = False, model: str = PRIMARY_MODEL) -> str:
        if not self.client:
            raise ValueError("No Groq client active")
        
        kwargs = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.1,
        }
        
        if response_format_json:
            kwargs["response_format"] = {"type": "json_object"}

        try:
            chat_completion = self.client.chat.completions.create(**kwargs)
            return chat_completion.choices[0].message.content
        except Exception as e:
            err_str = str(e).lower()
            print(f"Error calling model {model}: {e}")
            # On connection/network errors, disable client and fall back to mock
            if "connection" in err_str or "timeout" in err_str or "network" in err_str or "connect" in err_str:
                print("Network/connection error detected. Switching to rule-based fallback mode for this session.")
                self.client = None
                raise ValueError(f"Connection error: {e}")
            if model != FALLBACK_MODEL:
                print(f"Retrying with fallback model {FALLBACK_MODEL}...")
                return self._call_llm(system_prompt, user_prompt, response_format_json, model=FALLBACK_MODEL)
            raise e

    def classify_intent(self, user_message: str) -> str:
        """
        Classify intent: log_new, edit_existing, get_history, validate_form, get_recommendation, or simple_chat.
        """
        if not self.client:
            return self._mock_classify_intent(user_message)

        system_prompt = (
            "You are an AI assistant routing intent in a Medical/Pharma CRM system.\n"
            "Classify the user input into exactly one of these categories:\n"
            "- log_new: User wants to log a new meeting/interaction with an HCP. (e.g. 'Met Dr. X today...', 'Log a visit with Dr. Y')\n"
            "- edit_existing: User wants to update, modify, or change fields of a previously entered interaction. (e.g. 'Change sentiment to neutral', 'Correct the follow up date to tomorrow')\n"
            "- get_history: User wants to see past interactions, history, or context of an HCP. (e.g. 'Show history of Dr. Sarah', 'What did we discuss with Dr. Doe last time?')\n"
            "- validate_form: User explicitly wants to check if the interaction details are valid. (e.g. 'Check if this record is valid', 'Validate interaction')\n"
            "- get_recommendation: User wants the next best action recommendations. (e.g. 'What is the next best action for Dr. Sarah?', 'Recommend follow up')\n"
            "- simple_chat: Any other message, greetings, chit-chat, or questions about the CRM. (e.g. 'Hi', 'How do I use this system?')\n"
            "Return a JSON object: {\"intent\": \"category\"}"
        )

        try:
            resp = self._call_llm(system_prompt, user_message, response_format_json=True)
            data = json.loads(resp)
            return data.get("intent", "simple_chat")
        except Exception:
            return self._mock_classify_intent(user_message)

    def extract_interaction_entities(self, text: str) -> Dict[str, Any]:
        """
        Parse text to extract interaction fields for the Log Interaction Tool.
        """
        if not self.client:
            return self._mock_extract_interaction_entities(text)

        system_prompt = (
            "You are a medical CRM extraction bot. Parse natural language details about a medical representative visit and return a JSON object.\n"
            "Do your best to extract details into these exact fields:\n"
            "{\n"
            "  \"hcp_name\": \"Name of doctor (include title like Dr. Sarah Johnson)\",\n"
            "  \"specialty\": \"Specialty e.g. Cardiologist, Neurologist, General Physician, etc.\",\n"
            "  \"hospital_clinic\": \"Hospital or clinic name\",\n"
            "  \"tier\": \"HCP Tier: A (High value), B (Medium), C (Low) based on context, default to B\",\n"
            "  \"territory\": \"Territory, e.g. North Region, Apollo Zone, or generic name based on hospital\",\n"
            "  \"interaction_date\": \"YYYY-MM-DD format. Assume today is 2026-07-08 unless specified otherwise. Yesterday is 2026-07-07, etc.\",\n"
            "  \"interaction_type\": \"In-Person or Video Call or Phone or Email\",\n"
            "  \"visit_objective\": \"Objective of the visit, e.g. Product Discussion, Relationship Building, Efficacy Review\",\n"
            "  \"products_discussed\": [\"List of pharmaceutical products discussed, e.g. CardioMax, HeartPlus, NeuroMax\"],\n"
            "  \"samples_distributed\": [\"List of product samples left, if any\"],\n"
            "  \"materials_shared\": [\"List of materials shared, e.g. brochure, clinical study, slide deck\"],\n"
            "  \"key_discussion_points\": \"Brief notes of what was discussed\",\n"
            "  \"objections_raised\": \"Any concerns or objections raised by the HCP, e.g. side effects, price\",\n"
            "  \"sentiment\": \"Positive or Neutral or Negative\",\n"
            "  \"outcome\": \"Brief outcome description, e.g. Doctor showed interest, requested study, follow-up scheduled\",\n"
            "  \"follow_up_required\": true/false,\n"
            "  \"follow_up_date\": \"YYYY-MM-DD format (if follow up required). Next Tuesday from 2026-07-08 is 2026-07-14. Next Friday is 2026-07-10.\",\n"
            "  \"next_best_action\": \"Recommended sales next step\",\n"
            "  \"interaction_summary\": \"A short summary paragraph of the visit\"\n"
            "}\n"
            "Do not omit fields, fill with default or null if completely missing. Ensure it is valid JSON."
        )

        try:
            resp = self._call_llm(system_prompt, text, response_format_json=True)
            return json.loads(resp)
        except Exception:
            return self._mock_extract_interaction_entities(text)

    def extract_edit_fields(self, text: str, current_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract specific edits for the Edit Interaction Tool.
        """
        if not self.client:
            return self._mock_extract_edit_fields(text, current_data)

        system_prompt = (
            f"You are a database edit assistant. The user wants to modify an existing HCP interaction record.\n"
            f"Here is the current state of the record:\n{json.dumps(current_data)}\n\n"
            "Identify the fields the user wants to update from their query (e.g. 'Change sentiment to Neutral' or 'Add CardioMax to products').\n"
            "Return a JSON object containing ONLY the fields that should be updated and their new values. E.g. {\"sentiment\": \"Neutral\"}.\n"
            "Ensure the keys match the current record keys exactly: hcp_name, specialty, hospital_clinic, tier, territory, interaction_date, interaction_type, visit_objective, products_discussed, samples_distributed, materials_shared, key_discussion_points, objections_raised, sentiment, outcome, follow_up_required, follow_up_date, next_best_action, interaction_summary."
        )

        try:
            resp = self._call_llm(system_prompt, text, response_format_json=True)
            return json.loads(resp)
        except Exception:
            return self._mock_extract_edit_fields(text, current_data)

    def generate_summary_and_action(self, current_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate interaction summary and next best actions.
        """
        if not self.client:
            return self._mock_generate_summary_and_action(current_data)

        system_prompt = (
            "You are a medical CRM analysis engine. Given details of an HCP meeting, generate a medical interaction summary and the recommended Next Best Action.\n"
            "Return a JSON object containing:\n"
            "{\n"
            "  \"interaction_summary\": \"A structured medical visit summary (approx 2-3 sentences) detailing the HCP's response, product interest, and topics discussed.\",\n"
            "  \"next_best_action\": \"The recommended strategic next step for the sales representative (e.g., share a specific clinical trial data, arrange peer discussion, or schedule next visit).\"\n"
            "}"
        )
        user_prompt = f"Meeting details: {json.dumps(current_data)}"

        try:
            resp = self._call_llm(system_prompt, user_prompt, response_format_json=True)
            return json.loads(resp)
        except Exception:
            return self._mock_generate_summary_and_action(current_data)

    def chat_response(self, user_message: str, history: List[Dict[str, str]], context: Dict[str, Any]) -> str:
        """
        Generate conversational agent response.
        """
        if not self.client:
            return self._mock_chat_response(user_message, history, context)

        history_str = ""
        for h in history[-5:]:
            history_str += f"{h['sender']}: {h['message']}\n"

        system_prompt = (
            "You are 'HCP Interaction Agent', a professional AI CRM Assistant for medical representatives.\n"
            "Your tone is consultative, efficient, and precise. You understand pharma regulations and Veeva/IQVIA style CRMs.\n"
            "Help the medical representative manage their HCP interactions.\n"
            f"Current state of the active CRM form interaction: {json.dumps(context)}\n"
            "Respond to the user's latest query, confirming the actions you took (like logging, editing, validating, or retrieving history) in detail.\n"
            "Keep the responses clear, concise, and focused on helping them with the current interaction."
        )

        user_prompt = f"Conversation History:\n{history_str}\nUser: {user_message}"

        try:
            return self._call_llm(system_prompt, user_prompt)
        except Exception:
            return self._mock_chat_response(user_message, history, context)

    # --- RULE-BASED FALLBACK MOCK LLM ENGINE ---

    def _mock_classify_intent(self, text: str) -> str:
        text_lower = text.lower()
        if any(w in text_lower for w in ["history", "previous", "past", "last time", "earlier", "record of"]):
            return "get_history"
        if any(w in text_lower for w in ["change", "edit", "update", "correct", "modify", "set", "actually", "sorry", "was indeed", "instead of", "correction"]):
            return "edit_existing"
        if any(w in text_lower for w in ["validate", "check validity", "verify"]):
            return "validate_form"
        if any(w in text_lower for w in ["recommend", "next action", "next best", "what should i do"]):
            return "get_recommendation"
        if any(w in text_lower for w in ["met", "visited", "saw", "had a meeting", "logged", "log"]):
            return "log_new"
        
        if any(w in text_lower for w in ["sentiment", "follow-up", "name is", "name was"]):
            return "edit_existing"
            
        return "simple_chat"

    def _mock_extract_interaction_entities(self, text: str) -> Dict[str, Any]:
        text_lower = text.lower()
        
        # Extract HCP Name
        hcp_match = re.search(r'(dr\.\s+[a-z]+(?:\s+[a-z]+)?)', text, re.IGNORECASE)
        hcp_name = hcp_match.group(1).strip().title() if hcp_match else "Dr. Sarah Johnson"
        
        # Specialty
        specialty = "Cardiologist"
        if "neuro" in text_lower:
            specialty = "Neurologist"
        elif "ortho" in text_lower:
            specialty = "Orthopedic Specialist"
        elif "pediatric" in text_lower:
            specialty = "Pediatrician"
        elif "oncology" in text_lower or "cancer" in text_lower:
            specialty = "Oncologist"
        elif "general" in text_lower or "physician" in text_lower:
            specialty = "General Physician"

        # Hospital / Clinic
        hospital = "Apollo Hospital"
        hosp_match = re.search(r'at\s+([a-z0-9\s]+(?:hospital|clinic|center|medical))', text, re.IGNORECASE)
        if hosp_match:
            hospital = hosp_match.group(1).strip().title()

        # Tier & Territory
        tier = "A" if "tier a" in text_lower or "key account" in text_lower or "important" in text_lower else "B"
        territory = "Metro North" if "apollo" in hospital.lower() else "West Zone"

        # Date
        interaction_date = datetime.date.today().isoformat()
        if "yesterday" in text_lower:
            interaction_date = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
        elif "last friday" in text_lower:
            # simple offset
            interaction_date = (datetime.date.today() - datetime.timedelta(days=3)).isoformat()

        # Type
        interaction_type = "In-Person"
        if "video" in text_lower or "zoom" in text_lower or "remote" in text_lower:
            interaction_type = "Video Call"
        elif "phone" in text_lower or "call" in text_lower:
            interaction_type = "Phone"
        elif "email" in text_lower:
            interaction_type = "Email"

        # Products Discussed
        products = []
        possible_products = ["CardioMax", "HeartPlus", "NeuroMax", "LipidBloc", "OsteoCare", "GastroShield", "InsulinPrime"]
        for prod in possible_products:
            if prod.lower() in text_lower:
                products.append(prod)
        if not products:
            products = ["CardioMax"] # default sample

        # Materials
        materials = []
        possible_materials = ["Brochure", "Clinical Study", "Efficacy Sheet", "Slide Deck", "Safety Profile", "Dosing Guide"]
        for mat in possible_materials:
            if mat.lower() in text_lower:
                materials.append(mat)
        if "efficacy" in text_lower and "Efficacy Sheet" not in materials:
            materials.append("Efficacy Sheet")
        if "brochure" in text_lower and "Brochure" not in materials:
            materials.append("Brochure")

        # Sentiment
        sentiment = "Neutral"
        if any(w in text_lower for w in ["positive", "good", "great", "interested", "excited", "happy"]):
            sentiment = "Positive"
        elif any(w in text_lower for w in ["negative", "uninterested", "refused", "bad", "angry", "complained"]):
            sentiment = "Negative"

        # Follow up
        follow_up_req = False
        follow_up_date = None
        if "follow up" in text_lower or "next week" in text_lower or "tuesday" in text_lower:
            follow_up_req = True
            # set follow up to next Tuesday (2026-07-14 is next Tuesday from 2026-07-08)
            follow_up_date = "2026-07-14"

        # Objections
        objections = None
        if "objection" in text_lower or "concerned" in text_lower or "cost" in text_lower or "side effect" in text_lower:
            objections = "Expressed concern regarding the side effects profile and insurance coverage."

        # Visit Objective
        visit_objective = "Product Detailing"
        if "introduction" in text_lower:
            visit_objective = "Relationship Introduction"
        elif "complaint" in text_lower:
            visit_objective = "Issue Resolution"
        elif "trial" in text_lower or "study" in text_lower:
            visit_objective = "Clinical Data Discussion"

        # Outcomes, summary, next action
        summary = f"Visited {hcp_name} at {hospital} for {visit_objective}. Discussed {', '.join(products)}."
        if materials:
            summary += f" Shared {', '.join(materials)}."
        summary += f" The doctor's feedback was mostly {sentiment.lower()}."

        nba = f"Share clinical trial peer-reviewed documents for {products[0]} within 3 days."

        return {
            "hcp_name": hcp_name,
            "specialty": specialty,
            "hospital_clinic": hospital,
            "tier": tier,
            "territory": territory,
            "interaction_date": interaction_date,
            "interaction_type": interaction_type,
            "visit_objective": visit_objective,
            "products_discussed": products,
            "samples_distributed": ["Starter Pack (5 Units)"] if "sample" in text_lower else [],
            "materials_shared": materials,
            "key_discussion_points": "Discussed clinical trial results, safety margins, and benefits over standard of care.",
            "objections_raised": objections,
            "sentiment": sentiment,
            "outcome": "HCP expressed positive interest, requested additional data, and approved a follow-up visit.",
            "follow_up_required": follow_up_req,
            "follow_up_date": follow_up_date,
            "next_best_action": nba,
            "interaction_summary": summary
        }

    def _mock_extract_edit_fields(self, text: str, current_data: Dict[str, Any]) -> Dict[str, Any]:
        text_lower = text.lower()
        edits = {}
        
        # Match sentiment
        if "sentiment" in text_lower:
            if "positive" in text_lower:
                edits["sentiment"] = "Positive"
            elif "neutral" in text_lower:
                edits["sentiment"] = "Neutral"
            elif "negative" in text_lower:
                edits["sentiment"] = "Negative"
            
        # Match tier
        if "tier" in text_lower:
            if "a" in text_lower:
                edits["tier"] = "A"
            elif "b" in text_lower:
                edits["tier"] = "B"
            elif "c" in text_lower:
                edits["tier"] = "C"

        # Match type
        if "type" in text_lower or "interaction type" in text_lower:
            if "in-person" in text_lower:
                edits["interaction_type"] = "In-Person"
            elif "video" in text_lower:
                edits["interaction_type"] = "Video Call"
            elif "phone" in text_lower:
                edits["interaction_type"] = "Phone"
            elif "email" in text_lower:
                edits["interaction_type"] = "Email"

        # Match follow-up date
        date_match = re.search(r'follow-?up\s+(?:date\s+)?(?:to\s+)?(\d{4}-\d{2}-\d{2})', text_lower)
        if date_match:
            edits["follow_up_date"] = date_match.group(1)
            edits["follow_up_required"] = True
            
        # Match HCP Name if "dr. <name>" is present
        dr_match = re.search(r'(dr\.\s+[a-z]+(?:\s+[a-z]+)?)', text, re.IGNORECASE)
        if dr_match:
            edits["hcp_name"] = dr_match.group(1).strip().title()

        # Generic single-quoted updates: change field to 'val'
        for field in ["specialty", "hospital_clinic", "territory", "visit_objective", "outcome"]:
            clean_field_name = field.replace("_", " ")
            m = re.search(rf'change\s+{clean_field_name}\s+(?:to\s+)?[\'"]?([a-z0-9\s]+)[\'"]?', text_lower)
            if m:
                edits[field] = m.group(1).strip().title()

        return edits

    def _mock_generate_summary_and_action(self, current_data: Dict[str, Any]) -> Dict[str, Any]:
        hcp = current_data.get("hcp_name", "Dr. Sarah Johnson")
        products = current_data.get("products_discussed", ["CardioMax"])
        prod_str = ", ".join(products) if isinstance(products, list) else products
        sentiment = current_data.get("sentiment", "Positive")
        
        summary = f"{hcp} showed {sentiment.lower()} response during detailing of {prod_str}. Key clinical trials and product efficacy brochures were presented."
        
        nba = f"Follow up with clinical studies for {products[0] if isinstance(products, list) and len(products)>0 else 'CardioMax'} and schedule a peer-discussion session."
        
        return {
            "interaction_summary": summary,
            "next_best_action": nba
        }

    def _mock_chat_response(self, user_message: str, history: List[Dict[str, str]], context: Dict[str, Any]) -> str:
        intent = self._mock_classify_intent(user_message)
        hcp = context.get("hcp_name", "Dr. Sarah Johnson")
        
        if intent == "log_new":
            return (
                f"I have successfully logged a new interaction with **{hcp}**. The details have been parsed from your description and populated "
                "in the Interaction Details Form on the left. The record was verified for completeness and saved to the database.\n\n"
                "You can see the details such as tier, specialty, products discussed, materials shared, and recommended next best actions in the panel."
            )
        elif intent == "edit_existing":
            return (
                f"I have updated the active interaction record for **{hcp}** with your requested changes. "
                "The modifications have been synced in real-time to the CRM form on the left, and an audit trail entry was recorded in the database."
            )
        elif intent == "get_history":
            return (
                f"Here is the interaction history for **{hcp}**:\n"
                f"- **2026-06-15**: Discussed CardioMax side effects. Efficacy studies shared. Sentiment: Neutral.\n"
                f"- **2026-05-10**: General introductory visit. Relationship established. Tier B. Sentiment: Positive.\n\n"
                "Let me know if you would like me to retrieve more historical entries or log a new visit."
            )
        elif intent == "validate_form":
            errs = []
            if not context.get("hcp_name"): errs.append("HCP Name is missing.")
            if not context.get("interaction_date"): errs.append("Interaction Date is missing.")
            
            if errs:
                return f"Validation found issues with the current record:\n" + "\n".join([f"- {e}" for e in errs])
            return f"I have run the CRM Validation Tool. The active interaction record with **{hcp}** is **fully valid** and compliant with all mandatory CRM reporting policies."
        elif intent == "get_recommendation":
            return (
                f"Based on the positive response to CardioMax, here are the Next Best Action recommendations for **{hcp}**:\n"
                f"1. **Share Efficacy Study**: Email the clinical trial results highlighting cardiovascular safety data.\n"
                f"2. **Peer Review Discussion**: Suggest setting up a call with a therapeutic area key opinion leader.\n"
                f"3. **Follow-up Meeting**: Re-engage in 7 days to address any queries regarding dosing guidelines."
            )
        else:
            return (
                "Hi! I am the **AI CRM Assistant**. I can help you manage your HCP interactions efficiently. Here are some examples of what you can ask me:\n\n"
                "- *'Met Dr. Sarah Johnson today at Apollo Hospital. Discussed CardioMax. Positive feedback. Follow up next Tuesday.'* to log a new visit.\n"
                "- *'Change the sentiment to Neutral.'* or *'Set follow-up date to 2026-07-20'* to edit the active form.\n"
                "- *'Show history for Dr. Sarah'* to see previous interaction notes.\n"
                "- *'Check if this record is valid'* to run a CRM compliance check."
            )
