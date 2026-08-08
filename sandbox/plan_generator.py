import json
import re
from chat.llm_wrapper import get_llm

PLAN_GENERATION_PROMPT = """You are O.R.C.A.'s build engine. Given a user request, generate a JSON plan to build the software.

The JSON must have this exact structure:
{
    "project_name": "name_of_project",
    "files": [
        {"path": "relative/path/to/file.ext", "content": "full file content here"},
        {"path": "relative/path/to/another/file.ext", "content": "full file content here"}
    ],
    "commands": [
        "command1 to run",
        "command2 to run"
    ]
}

RULES:
1. If the user mentions "Laravel" or "PHP", generate a Laravel project with composer.json, routes/web.php, controllers, and Blade views.
2. If the user mentions "Spring Boot" or "Java", generate a Spring Boot project with pom.xml, Application.java, application.properties, and REST controllers.
3. If the user mentions "Django" or "Python" or nothing specific, generate a Django project with requirements.txt, settings.py, urls.py, and models.py.
4. Include ALL necessary commands to install dependencies and run the server.
5. Output ONLY valid JSON. No explanations, no markdown, no extra text."""

def generate_plan(user_description: str) -> dict:
    llm = get_llm()
    if llm is None:
        return {"error": "LLM not loaded. Please restart the server."}
    
    full_prompt = f"{PLAN_GENERATION_PROMPT}\n\nUser request: {user_description}\n\nJSON plan:"
    
    try:
        response = llm.create_completion(
            prompt=full_prompt,
            max_tokens=4096,
            temperature=0.2,
            stop=["```", "\n\n\n"],
            echo=False
        )
        
        raw_output = response['choices'][0]['text'].strip()
        json_match = re.search(r'\{.*\}', raw_output, re.DOTALL)
        if not json_match:
            return {"error": "Failed to parse JSON from LLM response."}
        
        plan = json.loads(json_match.group())
        
        required_fields = ['project_name', 'files', 'commands']
        for field in required_fields:
            if field not in plan:
                return {"error": f"Missing required field: {field}"}
        
        return plan
        
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON from LLM: {str(e)}"}
    except Exception as e:
        return {"error": f"Plan generation failed: {str(e)}"}