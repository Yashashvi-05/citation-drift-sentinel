import os
import subprocess
import sys

def check_preflight():
    print("Checking pre-flight requirements...")
    has_env_file = os.path.exists('.env')
    has_env_var = 'GROQ_API_KEY' in os.environ
    
    if not has_env_file and not has_env_var:
        print("❌ Error: GROQ_API_KEY not found.")
        print("   Please create a .env file or set the GROQ_API_KEY environment variable.")
        print("   See REPRODUCTION.md for setup instructions.")
        sys.exit(1)
    print("✅ Environment variables verified.")

def clean_environment():
    print("Sweeping previous run data to ensure a clean, live execution...")
    files_to_remove = ['sentinel_cache.db', 'evaluation_results.jsonl']
    for file in files_to_remove:
        try:
            os.remove(file)
            print(f"  🗑️ Deleted {file}")
        except FileNotFoundError:
            pass
    print("✅ Environment reset.")

def run_step(script_path):
    print(f"\n{'='*50}\n🚀 Running {script_path}...\n{'='*50}")
    result = subprocess.run([sys.executable, script_path])
    if result.returncode != 0:
        print(f"❌ Error: {script_path} failed. Halting execution.")
        sys.exit(result.returncode)
    print(f"✅ {script_path} completed successfully.")

def main():
    print("Starting Citation Drift Sentinel Bootstrap...\n")
    
    check_preflight()
    print("")
    clean_environment()
    
    scripts = [
        "run_evaluation.py",
        os.path.join("src", "generate_report.py"),
        os.path.join("src", "visualize_diff.py")
    ]
    
    for script in scripts:
        if not os.path.exists(script):
            print(f"❌ Error: Cannot find {script}")
            sys.exit(1)
        run_step(script)
        
    print("\n🎉 Pipeline complete! Review BENCHMARK_REPORT.md and the drift_visualization HTML files.")

if __name__ == '__main__':
    main()
