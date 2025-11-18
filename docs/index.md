# Welcome to the CogniAgents Framework                                                                                                               
                                                                                                                                                     
                                                                                                                                                     
                                                                                                                                                     
**CogniAgents** is a flexible and extensible framework for defining, orchestrating, and executing AI agents and workflows using simple YAML          
configurations.                                                                                                                                      
                                                                                                                                                     
                                                                                                                                                     
                                                                                                                                                     
It is designed to be:                                                                                                                                
                                                                                                                                                     
- **Declarative:** Define complex agentic behavior in easy-to-read YAML files.                                                                       
                                                                                                                                                     
- **Extensible:** Bring your own Pydantic schemas and prompt components to customize agent outputs and behavior.                                     
                                                                                                                                                     
- **Maintainable:** Build reusable components to keep your agent and workflow definitions DRY (Don't Repeat Yourself).                               
                                                                                                                                                     
                                                                                                                                                     
                                                                                                                                                     
---                                                                                                                                                  
                                                                                                                                                     
                                                                                                                                                     
                                                                                                                                                     
## Getting Started                                                                                                                                   
                                                                                                                                                     
                                                                                                                                                     
                                                                                                                                                     
### 1. Installation                                                                                                                                  
                                                                                                                                                     
                                                                                                                                                     
                                                                                                                                                     
Clone the repository and install the framework in editable mode. This also installs the development dependencies needed for documentation.           
                                                                                                                                                     
```
git clone https://github.com/your-username/CogniAgents.git                                                                                           

cd CogniAgents                                                                                                                                       

pip install -e ".[dev]"                                                                                                                              
```
                                                                                                                                                     
                                                                                                                                                     
                                                                                                                                                     
### 2. Configure Environment                                                                                                                         
                                                                                                                                                     
                                                                                                                                                     
                                                                                                                                                     
Create a `.env` file in the project root by copying the example. This file will store your LLM API credentials.                                      
                                                                                                                                                     

`cp .env.example .env`                                                                                                                               

                                                                                                                                                     
Now, edit the `.env` file with your LLM service URL and API key.                                                                                     
                                                                                                                                                     
                                                                                                                                                     
                                                                                                                                                     
### 3. Run an Example                                                                                                                                
                                                                                                                                                     
                                                                                                                                                     
                                                                                                                                                     
Run the customer support router example directly using Python. The script will automatically load its `config.yaml`.                                 

`python examples/customer_support_router/run_router.py`
                                                                                                                                                     
Ready to dive deeper? Check out the **[Core Concepts](core_concepts.md)**.