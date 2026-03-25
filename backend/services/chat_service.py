from typing import List, Dict, Any, Optional
from services.llm_service import get_llm_service
from services.trip_service import get_trip_service
from mcp_manager import get_mcp_manager
from models import ChatRequest, ChatMessage, POICard, TrainInfo, POICardsResponse, TrainListResponse, ChatResponseSchema

class ChatService:
    def __init__(self):
        self.llm_service = get_llm_service()
        self.trip_service = get_trip_service()
        self.mcp_manager = get_mcp_manager()

    def _extract_json(self, text: str) -> str:
        if not text:
            return ""
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return text.strip()

    def build_system_prompt(self) -> str:
        trip = self.trip_service.get_trip_details()
        if not trip:
            return "You are a helpful travel assistant."
        
        cities_str = ", ".join([c["name"] for c in trip["cities"]])
        days_str = trip["total_days"]
        start_date = trip["start_date"]
        
        return f"""You are a travel assistant helping plan a trip to China.

Trip Details:
- Cities: {cities_str}
- Total Days: {days_str}
- Start Date: {start_date}

You have access to tools for searching places, getting train information, and calculating distances.

CRITICAL: You MUST ALWAYS respond with a JSON object with this exact structure:

{{
  "text": "Your message to the user",
  "widget": "poi_cards" or "train_list" or null,
  "data": {{
    "places": [...] for poi_cards,
    "trains": [...] for train_list
  }}
}}

EXAMPLE 1 - Train Search:
{{
  "text": "I found 5 trains from Beijing to Shanghai:",
  "widget": "train_list",
  "data": {{
    "trains": [
      {{
        "id": "G547",
        "train_number": "G547",
        "departure_date": "2026-03-25",
        "departure_time": "06:18",
        "arrival_time": "12:11",
        "departure_station": "Beijing South",
        "arrival_station": "Shanghai Hongqiao",
        "duration": "05:53",
        "seat_options": [
          {{"type": "Business Class", "price": "1873 RMB"}},
          {{"type": "First Class", "price": "930 RMB"}},
          {{"type": "Second Class", "price": "553 RMB"}}
        ]
      }}
    ]
  }}
}}

EXAMPLE 2 - POI Search:
{{
  "text": "Here are popular attractions in Beijing:",
  "widget": "poi_cards",
  "data": {{
    "places": [
      {{
        "id": "B000A8UIN8",
        "name": "The Palace Museum",
        "rating": 4.9,
        "address": "4 Jingshan Front St, Dongcheng, Beijing",
        "description": "The imperial palace of Ming and Qing dynasties",
        "price": "60 CNY",
        "opening_hours": "08:30-17:00",
        "coordinates": {{
          "lat": 39.918058,
          "lng": 116.397026
        }},
        "category": "Historical Site",
        "tags": ["Imperial", "Architecture", "Must-visit"]
      }}
    ]
  }}
}}

EXAMPLE 3 - General Chat:
{{
  "text": "Hello! How can I help you with your trip?",
  "widget": null,
  "data": null
}}

Rules:
- ALWAYS return a JSON object, never a list or plain text
- The top-level object MUST have "text", "widget", and "data" keys
- STRICT RULE: You MUST return AT LEAST 4 options inside "data.places" or "data.trains" unless the user explicitly asks for fewer. If less than 4 exist, return as many as possible. Do not just return 1 or 2 options.
- For train results, put them in "data.trains" array
- For POI results, put them in "data.places" array
- Each train must have: id, train_number, departure_date, departure_time, arrival_time, departure_station, arrival_station, duration, seat_options
- Each POI must have: id, name, rating, address, description, price, opening_hours, coordinates, category, tags
- STRICT RULE: If the user asks for trains but does not specify a departure city or origin station, strictly assume the departure city is "Shenzhen".
- STRICT RULE: ALWAYS use "YYYY-MM-DD" format for all dates.
"""

    def process_message_stream(self, request: ChatRequest):
        import json
        system_prompt = self.build_system_prompt()
        messages = [{"role": "system", "content": system_prompt}]
        
        for msg in request.conversation_history:
            messages.append({"role": msg.role, "content": msg.content})
        
        messages.append({"role": "user", "content": request.message})
        
        yield f"data: {json.dumps({'type': 'status', 'message': 'Analyzing request...'})}\n\n"
        
        tools = self.mcp_manager.get_all_tools()
        openai_tools = [
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t["description"],
                    "parameters": t["inputSchema"]
                }
            }
            for t in tools
        ]
        
        response = self.llm_service.chat_completion(
            messages=messages,
            tools=openai_tools,
            response_format={"type": "json_object"}
        )
        
        if response.tool_calls:
            yield from self._handle_tool_calls_stream(response, messages, openai_tools)
            return
        
        try:
            json_str = self._extract_json(response.content)
            result = json.loads(json_str)
            final_res = self._parse_structured_response(result)
            yield f"data: {json.dumps({'type': 'result', 'data': final_res})}\n\n"
        except json.JSONDecodeError:
            final_res = {
                "text": response.content,
                "widget": None,
                "data": None
            }
            yield f"data: {json.dumps({'type': 'result', 'data': final_res})}\n\n"

    def _handle_tool_calls_stream(
        self,
        response,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]]
    ):
        import json
        messages.append(response)
        
        for tool_call in response.tool_calls:
            function_name = tool_call.function.name
            arguments = tool_call.function.arguments
            
            yield f"data: {json.dumps({'type': 'status', 'message': f'Calling tool: {function_name}...'})}\n\n"
            
            try:
                args = json.loads(arguments) if arguments else {}
                result = self.mcp_manager.call_tool(function_name, args)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(result)
                })
            except Exception as e:
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": f"Error: {str(e)}"
                })
        
        messages.append({
            "role": "user",
            "content": "Please format the results as a JSON object with 'text', 'widget', and 'data' keys. Put the train/POI results in the 'data' field."
        })
        
        max_iterations = 5
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            final_response = self.llm_service.chat_completion(
                messages=messages,
                tools=tools,
                response_format={"type": "json_object"}
            )
            
            if not final_response.tool_calls:
                break
            
            messages.append(final_response)
            
            for tool_call in final_response.tool_calls:
                function_name = tool_call.function.name
                arguments = tool_call.function.arguments
                
                yield f"data: {json.dumps({'type': 'status', 'message': f'Calling tool: {function_name}...'})}\n\n"
                
                try:
                    args = json.loads(arguments) if arguments else {}
                    result = self.mcp_manager.call_tool(function_name, args)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": str(result)
                    })
                except Exception as e:
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": f"Error: {str(e)}"
                    })
        
        if not final_response.content:
            fallback_res = {'type': 'result', 'data': {'text': "I apologize, but I couldn't process your request.", 'widget': None, 'data': None}}
            yield f"data: {json.dumps(fallback_res)}\n\n"
            return
        
        try:
            json_str = self._extract_json(final_response.content)
            result = json.loads(json_str)
            final_res = self._parse_structured_response(result)
            yield f"data: {json.dumps({'type': 'result', 'data': final_res})}\n\n"
        except json.JSONDecodeError:
            final_res = {
                "text": final_response.content,
                "widget": None,
                "data": None
            }
            yield f"data: {json.dumps({'type': 'result', 'data': final_res})}\n\n"

    def search_image(self, place_name: str, category: str) -> Optional[str]:
        """Search for an image of a place using Tavily."""
        try:
            query = f"{place_name} {category} photo image"
            print(f"[IMAGE DEBUG] Searching for: {query}")
            result = self.mcp_manager.call_tool("tavily_tavily-search", {
                "query": query,
                "max_results": 1,
                "include_images": True
            })
            
            # Print a bit more of the result for debugging
            print(f"[IMAGE DEBUG] Raw response (first 300 chars): {result[:300]}")
            
            import json
            # Use extract_json to handle cases where LLM/Tool might wrap JSON in text or markdown
            json_str = self._extract_json(result)
            data = json.loads(json_str)
            
            img_url = None
            if isinstance(data, dict) and "images" in data and data["images"]:
                img_url = data["images"][0]
            elif isinstance(data, list) and len(data) > 0:
                img_url = data[0]
            elif isinstance(data, dict) and "results" in data and data["results"]:
                # Some versions of Tavily tool return structured results
                first_res = data["results"][0]
                if isinstance(first_res, dict) and "image" in first_res:
                    img_url = first_res["image"]
                elif isinstance(first_res, dict) and "url" in first_res:
                    # If it's a search result, maybe we can use it? risky.
                    pass
                    
            if img_url:
                print(f"[IMAGE DEBUG] Found image: {img_url}")
                return img_url
            
            print(f"[IMAGE DEBUG] No images found in results or unexpected structure. Using category fallback.")
            return self._get_category_fallback(category)
        except Exception as e:
            print(f"[IMAGE ERROR] search_image failed: {e}")
            return self._get_category_fallback(category)

    def _get_category_fallback(self, category: str) -> str:
        """Provide a high-quality Unsplash fallback based on category."""
        fallbacks = {
            "attraction": "https://images.unsplash.com/photo-1508804185872-d7badad00f7d?q=80&w=1000&auto=format&fit=crop",
            "restaurant": "https://images.unsplash.com/photo-1512152272829-e3139592d56f?q=80&w=1000&auto=format&fit=crop",
            "hotel": "https://images.unsplash.com/photo-1566073771259-6a8506099945?q=80&w=1000&auto=format&fit=crop",
            "shopping": "https://images.unsplash.com/photo-1441986300917-64674bd600d8?q=80&w=1000&auto=format&fit=crop"
        }
        return fallbacks.get(category.lower(), fallbacks["attraction"])

    def _parse_structured_response(self, result: Any) -> Dict[str, Any]:
        if isinstance(result, list):
            print(f"Error: LLM returned a list instead of dict: {result}")
            return {
                "text": "I apologize, but I encountered an error processing your request.",
                "widget": None,
                "data": None
            }
        
        # Auto-correct common LLM mistakes
        if isinstance(result, dict):
            widget = result.get("widget")
            data = result.get("data")
            
            # Fix widget name
            if widget == "poi":
                result["widget"] = "poi_cards"
            elif widget == "train":
                result["widget"] = "train_list"
                
            # Fix data format if it's a list instead of {"places": [...]} or {"trains": [...]}
            if isinstance(data, list):
                if result.get("widget") == "poi_cards":
                    result["data"] = {"places": data}
                elif result.get("widget") == "train_list":
                    result["data"] = {"trains": data}
            
            # Fix coordinates if they are string "lat,lng"
            if isinstance(result.get("data"), dict) and "places" in result.get("data", {}):
                for place in result["data"]["places"]:
                    if not place.get("image_url") or place.get("image_url") == "":
                        image_url = self.search_image(place.get("name", ""), place.get("category", "attraction"))
                        if image_url:
                            place["image_url"] = image_url

                    if isinstance(place.get("coordinates"), str):
                        try:
                            # Try splitting by comma
                            parts = place["coordinates"].split(",")
                            if len(parts) == 2:
                                place["coordinates"] = {
                                    "lat": float(parts[1].strip() if '.' in parts[1] else parts[0].strip()),
                                    "lng": float(parts[0].strip() if '.' in parts[1] else parts[1].strip())
                                }
                        except:
                            pass
        
        try:
            validated = ChatResponseSchema(**result)
            
            # Convert Pydantic models back to dict for API response
            data_dict = None
            if validated.data:
                data_dict = validated.data.model_dump()
                
            return {
                "text": validated.text,
                "widget": validated.widget,
                "data": data_dict
            }
        except Exception as e:
            print(f"Error validating ChatResponseSchema: {e}")
            return {
                "text": result.get("text", "") if isinstance(result, dict) else "I apologize, but I encountered an error processing your request.",
                "widget": result.get("widget") if isinstance(result, dict) else None,
                "data": result.get("data") if isinstance(result, dict) else None
            }

_chat_service: Optional[ChatService] = None

def get_chat_service() -> ChatService:
    global _chat_service
    if _chat_service is None:
        _chat_service = ChatService()
    return _chat_service
