# Core Concepts

The CogniAgents framework is built on a few fundamental concepts that work together to create powerful, configuration-driven AI systems. Understanding these concepts is key to using the framework effectively.

---

## 1. The Configuration File

The heart of any CogniAgents project is the central YAML configuration file (e.g., `config.yaml`). This file declaratively defines all the components of your system. It acts as the single source of truth for your agents and workflows.

A typical configuration file has the following top-level sections:

- `global_llm_settings`: Default values for the LLM that can be inherited by agents.
- `prompt_components`: Reusable snippets of text that can be included in agent prompts.
- `custom_schemas`: Pointers to custom Pydantic models for structured agent outputs.
- `agents`: A list of all the individual AI agents you want to define.
- `workflows`: A list of multi-step processes that orchestrate one or more agents.
- `templates`: A dictionary of Jinja2 templates for formatting workflow outputs.

## 2. Agents

An **Agent** is the basic building block of the framework. It is a specialized AI entity designed to perform a single, well-defined task. For example, you might have an agent that summarizes text, another that analyzes sentiment, and a third that categorizes customer support tickets.

Under the hood, a `CogniAgent` is a wrapper around a `PydanticAIAgent`. It is defined in the `agents` section of your `config.yaml`.

### Example Agent Definition:

```
agents:                                                                                                                                              

 • name: sentiment_analyzer                                                                                                                          
   description: "Analyzes the sentiment of a customer review."                                                                                       
   llm:                                                                                                                                              
   temperature: 0.0                                                                                                                                  
   prompt: |                                                                                                                                         
   Analyze the sentiment of the following text.                                                                                                      
   Classify it as 'positive', 'negative', or 'neutral'.                                                                                              
   Provide a brief justification for your classification.                                                                                            
   Text: {text_to_analyze}                                                                                                                           
   output_schema: "sentiment" # References a built-in or custom schema                                                                               
```
                                                                                                                                                     
                                                                                                                                                     
                                                                                                                                                     
Key properties:                                                                                                                                      
                                                                                                                                                     
- `name`: A unique identifier for the agent.                                                                                                         
                                                                                                                                                     
- `prompt`: The instructions for the agent, including placeholders for input.                                                                        
                                                                                                                                                     
- `output_schema`: The name of the schema that defines the agent's output structure. This is crucial for getting reliable, structured data back from 
the LLM.                                                                                                                                             
                                                                                                                                                     
                                                                                                                                                     
                                                                                                                                                     
## 3. Workflows                                                                                                                                      
                                                                                                                                                     
                                                                                                                                                     
                                                                                                                                                     
A **Workflow** orchestrates one or more agents to accomplish a more complex task. It defines a sequence of steps, where the output of one step can be
used as the input for a subsequent step.                                                                                                             
                                                                                                                                                     
                                                                                                                                                     
                                                                                                                                                     
Workflows are defined in the `workflows` section of your `config.yaml`.                                                                              
                                                                                                                                                     
                                                                                                                                                     
                                                                                                                                                     
### Example Workflow Definition:                                                                                                                     
                                                                                                                                                     
```
workflows:                                                                                                                                           

 • name: review_analysis_workflow                                                                                                                    
   description: "Runs a full analysis on a customer review."                                                                                         
   steps:                                                                                                                                            
    • agent: text_summarizer                                                                                                                         
      input:                                                                                                                                         
      customer_review: "{{ payload.customer_review }}"                                                                                               
      output_to: summary_result                                                                                                                      
    • agent: sentiment_analyzer                                                                                                                      
      input:                                                                                                                                         
      text_to_analyze: "{{ payload.customer_review }}"                                                                                               
      output_to: sentiment_analysis                                                                                                                  

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ The template is defined at the root level, keyed by the workflow name.                                                                            ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

templates:                                                                                                                                           

review_analysis_workflow: |                                                                                                                          

                                                                                                                                                     
Analysis Complete:                                                                                                                                   
                                                                                                                                                     
Summary: {{ context.summary_result.summary }}                                                                                                        
                                                                                                                                                     
Sentiment: {{ context.sentiment_analysis.sentiment }}                                                                                                
                                                                                                                                                     
Justification: {{ context.sentiment_analysis.rationale }}                                                                                            
                                                                                                                                                     
---                                                                                                                                                  
                                                                                                                                                     
Positive Points:                                                                                                                                     
                                                                                                                                                     
{% for point in context.summary_result.positive_aspects %}                                                                                           
                                                                                                                                                     
- {{ point }}                                                                                                                                        
                                                                                                                                                     
{% endfor %}                                                                                                                                          
```

                                                                                                                                                     
                                                                                                                                                     
                                                                                                                                                     
Key concepts:                                                                                                                                        
                                                                                                                                                     
- `steps`: A list of tasks to execute in order. Each step typically calls an agent.                                                                  
                                                                                                                                                     
- `input`: Maps data into the agent's input. You can use data from the initial `payload` or the `context`.                                           
                                                                                                                                                     
- `context`: A shared dictionary that accumulates the outputs of each step. The `output_to` defines the key under which a step's result is stored in 
the `context`.                                                                                                                                       
                                                                                                                                                     
- `templates`: A root-level dictionary where keys match workflow names and values are Jinja2 templates used to format the final output.              

## 4. Schemas                                                                                                                                        

A **Schema** defines the structure of an agent's output. By enforcing a schema, you ensure that the LLM's response is predictable, structured, and   
easy to work with in your application. Schemas are defined using Pydantic models.

The framework includes several built-in schemas (like `SummaryOutput` and `SentimentOutput`), but you can easily define your own.                    

### Custom Schema Definition:

To use a custom schema, you define it in a Python file and reference it from your `config.yaml`.                                                     

**`custom_schemas.py`:**                                                                                                                             
                                                                                                                                                     
```
from pydantic import BaseModel, Field                                                                                                                

class SupportRouteOutput(BaseModel):                                                                                                                 

                                                                                                                                                     
department: str = Field(description="The department to route to (e.g., 'Billing', 'Technical Support', 'Sales').")                                   
                                                                                                                                                     
urgency: int = Field(description="An urgency score from 1 to 5.")                                                                                    
```                                                                                                                                                     

                                                                                                                                                     
                                                                                                                                                     
                                                                                                                                                     
**`config.yaml`:**                                                                                                                                   
                                                                                                                                                     
```
custom_schemas:                                                                                                                                      
   support_router_schema: "path.to.your.schemas:SupportRouteOutput"                                                                                     

agents:
   name: support_router                                                                                                                              
   output_schema: support_router_schema # Use the custom schema                                                                                      
```
## 5. Prompt Components                                                                                                                              

**Prompt Components** are reusable pieces of text that help you keep your prompts DRY (Don't Repeat Yourself). You can define a component once and   
reference it in multiple agent prompts.

### Example Prompt Component:
**`config.yaml`:**                                                                                                                                   
                                                                                                                                                     
```
prompt_components:                                                                                                                                   

politeness_clause: "Be polite and professional in your response."                                                                                    

agents:                                                                                                                                              
   name: sentiment_analyzer                                                                                                                          
   prompt: |                                                                                                                                         
   Analyze the sentiment of the following text.                                                                                                      
   {{ prompt_components.politeness_clause }}                                                                                                         
```
                                                                                                                                                     
                                                                                                                                                     
                                                                                                                                                     
This modular approach makes it easy to build, maintain, and extend complex AI systems with clear and readable configurations.                        
                                                                                                                                                     


