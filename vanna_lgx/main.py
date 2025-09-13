# vanna_lgx/main.py - S2 VERSION

from vanna_lgx.core.graph import build_s2_graph

def main():
    print("Vanna-LGX (Stage S2): Few-shot Example Aware Agent")
    print("--------------------------------------------------")
    
    # Build the LangGraph agent for S2
    app = build_s2_graph()
    
    # Interactive loop
    while True:
        question = input("Ask a question about the database (or type 'exit' to quit): ")
        if question.lower() == 'exit':
            break
        
        # The input to the graph must be a dictionary with keys matching the state
        inputs = {"question": question}
        
        # The second argument is a configuration dictionary.
        # It can be used to configure execution, like specifying which nodes to run.
        final_state = app.invoke(inputs)
        
        print("\n--- Final Result ---")
        print(final_state.get("summary", "No summary was generated."))
        print("--------------------\n")

if __name__ == "__main__":
    main()