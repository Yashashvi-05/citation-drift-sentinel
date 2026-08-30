import dotenv
from groq import Groq

dotenv.load_dotenv()

def main():
    try:
        client = Groq()
        models = client.models.list()
        
        print("Available Groq Models:")
        print("-" * 30)
        for model in models.data:
            print(model.id)
            
    except Exception as e:
        print(f"Error fetching models: {e}")

if __name__ == "__main__":
    main()
