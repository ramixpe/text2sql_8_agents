# vanna_lgx/main.py - S5 FINAL VERSION

import json
from vanna_lgx.core.graph import build_s5_graph

def main():
    print("Vanna-LGX (Stage S5): The Complete Agent")
    print("-----------------------------------------")
    
    app = build_s5_graph()
    
    while True:
        question = input("Ask a question about the database (or type 'exit' to quit): ")
        if question.lower() == 'exit': break
        
        inputs = {
            "question": question,
            "repair_attempts": 0
        }
        
        final_state = app.invoke(inputs)
        
        print("\n--- Final Result ---")
        print(final_state.get("summary", "No summary was generated."))
        
        # S5 CHANGE: Check for and print the visualization spec
        if vis_spec := final_state.get("visualization_spec"):
            print("\n--- Visualization Spec (Vega-Lite JSON) ---")
            print(json.dumps(vis_spec, indent=2))
            print("-------------------------------------------\n")
        else:
            print("--------------------\n")

if __name__ == "__main__":
    main()