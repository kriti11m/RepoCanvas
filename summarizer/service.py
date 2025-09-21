import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from prompts import SYSTEM_PROMPT, USER_PROMPT
from schema import SummaryResponse

# Load .env from current directory (summarizer/)
load_dotenv()

# Debug: Print if API key is loaded
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("ERROR: OPENAI_API_KEY not found in environment variables")
    print("Make sure you have a .env file with OPENAI_API_KEY=your_key")
else:
    print(f"✅ API key loaded successfully (starts with: {api_key[:10]}...)")

client = OpenAI(api_key=api_key)

def format_snippets(snippets):
    formatted = []
    for i, s in enumerate(snippets, 1):
        code_preview = "\n".join(s["code"].splitlines()[:12])
        formatted.append(f"{i}) {s['node_id']}:\n{code_preview}")
    return "\n\n".join(formatted)

def extract_function_info(code):
    """Extract basic info from code for fallback summary"""
    lines = code.strip().split('\n')
    function_name = "unknown"
    
    # Find function name
    for line in lines:
        if line.strip().startswith('def '):
            function_name = line.split('def ')[1].split('(')[0]
            break
    
    # Look for key operations with more specific analysis
    operations = []
    code_lower = code.lower()
    
    if 'database' in code_lower or 'find_user' in code_lower or 'query' in code_lower:
        operations.append("database lookup")
    if 'validate' in code_lower or 'check' in code_lower or 'verify' in code_lower:
        operations.append("validation")
    if 'password' in code_lower and 'hash' in code_lower:
        operations.append("password verification")
    if 'create' in code_lower or 'generate' in code_lower:
        operations.append("creation/generation")
    if 'token' in code_lower or 'session' in code_lower:
        operations.append("token/session handling")
    if 'api' in code_lower or 'request' in code_lower:
        operations.append("API call")
    if 'return' in code_lower and operations:
        operations.append("return result")
    
    return function_name, operations

def local_fallback_summary(question: str, snippets: list) -> SummaryResponse:
    """Generate summary without external API calls"""
    if not snippets:
        return SummaryResponse(
            one_liner="No code snippets provided",
            steps=[],
            inputs_outputs=[],
            caveats=[],
            node_refs=[]
        )
    
    # Analyze the first snippet
    snippet = snippets[0]
    func_name, operations = extract_function_info(snippet['code'])
    
    # Generate context-aware summary
    if 'auth' in question.lower() or 'login' in question.lower() or 'credential' in question.lower():
        one_liner = f"Authentication function '{func_name}' verifies user credentials and manages access"
    elif 'payment' in question.lower() or 'charge' in question.lower():
        one_liner = f"Payment processing function '{func_name}' handles transaction processing"
    else:
        one_liner = f"Function '{func_name}' processes {question.lower().replace('how does ', '').replace('?', '')}"
    
    # Generate steps based on detected operations
    steps = []
    operation_map = {
        "database lookup": "Queries database for user/data",
        "validation": "Validates input parameters", 
        "password verification": "Verifies password credentials",
        "creation/generation": "Creates or generates required objects",
        "token/session handling": "Manages authentication tokens/sessions",
        "API call": "Makes external service calls",
        "return result": "Returns processed result"
    }
    
    for op in operations:
        if op in operation_map:
            steps.append(operation_map[op])
    
    if not steps:
        steps = ["Processes input data", "Performs business logic", "Returns result"]
    
    return SummaryResponse(
        one_liner=one_liner,
        steps=steps[:4],  # Limit to 4 steps max
        inputs_outputs=[
            f"Input: function parameters from {snippet['node_id']}",
            "Output: processed result or status"
        ],
        caveats=["Summary generated locally - limited analysis"],
        node_refs=[{
            "node_id": snippet['node_id'],
            "excerpt_line": "see full function code"
        }]
    )

def summarize(question: str, snippets: list) -> SummaryResponse:
    prompt = USER_PROMPT.format(question=question, snippets=format_snippets(snippets))
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            max_tokens=400,
            temperature=0.1  # Lower temperature for more consistent JSON
        )
        content = response.choices[0].message.content.strip()
        
        # Log the raw response for debugging
        print(f"Raw AI response: {content}")
        
        # Try to clean up common JSON issues
        content = content.strip()
        if content.startswith('```json'):
            content = content[7:]
        if content.endswith('```'):
            content = content[:-3]
        content = content.strip()
        
        # Parse the JSON response
        summary_data = json.loads(content)
        return SummaryResponse(**summary_data)
        
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        print(f"Problematic content: '{content}'")
        print("Falling back to local summary...")
        return local_fallback_summary(question, snippets)
        
    except Exception as e:
        print(f"API call error: {e}")
        print("Falling back to local summary...")
        return local_fallback_summary(question, snippets)