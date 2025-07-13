#!/usr/bin/env python3
"""
Quick start script for DocumentAI Backend
"""
import subprocess
import sys
import os

def main():
    print(" Starting DocumentAI Backend...")
    
    # Ensure we're in the right directory
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(backend_dir)
    
    # Import and run the app
    try:
        from main import app
        import uvicorn
        
        print(" Backend ready for document Q&A")
        print(" Frontend can connect to: http://localhost:8000")
        print("CORS configured for ports: 3000, 5173, 8080")
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n Backend stopped")
    except Exception as e:
        print(f" Error starting backend: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
