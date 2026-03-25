import json
from services.chat_service import get_chat_service
from models import ChatRequest

def run_test_query(query: str):
    print(f"\n[{'='*40}]")
    print(f"Testing Query: '{query}'")
    request = ChatRequest(
        message=query,
        conversation_history=[]
    )
    service = get_chat_service()
    result = service.process_message(request)
    
    print("\nFINAL RESULT:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # Validation logic
    widget = result.get("widget")
    data = result.get("data", {})
    
    if widget == "poi_cards" and "places" in data:
        items = data["places"]
        print(f"\n✅ Result successfully parsed as POI Cards. Items count: {len(items)}")
        if len(items) < 4:
            print("❌ WARNING: LLM returned less than 4 POI options!")
    elif widget == "train_list" and "trains" in data:
        items = data["trains"]
        print(f"\n✅ Result successfully parsed as Train List. Items count: {len(items)}")
        if len(items) < 4:
            print("❌ WARNING: LLM returned less than 4 Train options!")
    else:
        print(f"\n❌ Result missing valid widget data array! Widget: {widget}")

if __name__ == "__main__":
    # Test 1: Trains
    run_test_query("Find trains from Shenzhen to Beijing on April 5, 2025")
    
    # Test 2: POI
    run_test_query("What are the most popular attractions in Beijing? Don't specify a number of options.")
