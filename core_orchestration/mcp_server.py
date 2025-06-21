from fastapi import FastAPI, Request
from pydantic import BaseModel
import httpx
import os
import openai
import json
from organization_mcp import organization_context
from dotenv import load_dotenv
load_dotenv()

app = FastAPI()

# Load OpenAI API key from environment variable
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai_client = openai.OpenAI(api_key=OPENAI_API_KEY, base_url="https://api.openai.com/v1/")

# Load tool schema for LLM prompt
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "mcp.organization.json")
with open(SCHEMA_PATH, "r") as f:
    tool_schema = json.load(f)

# --- MCP Protocol Endpoint ---
@app.post("/mcp/execute")
async def mcp_execute(request: Request):
    body = await request.json()
    prompt = body.get("prompt") or body.get("query") or ""
    # Use OpenAI to extract parameters
    try:
        system_prompt = (
            "You are an API agent. Given a user query and the following tool schema, extract the correct parameters for the API call. "
            "Return a JSON object with two fields: 'postalCode' (the 5-digit postal code) and 'name' (the profession or organization type). "
            f"Tool schema: {json.dumps(tool_schema['tool'])}"
        )
        user_prompt = f"User query: {prompt}"
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.0,
            max_tokens=256
        )
        llm_content = response.choices[0].message.content
        # Try to parse JSON from LLM output
        try:
            params = json.loads(llm_content)
        except Exception:
            # fallback: try to extract JSON substring
            import re
            match = re.search(r'\{.*\}', llm_content, re.DOTALL)
            params = json.loads(match.group(0)) if match else {}
        postal_code = params.get("postalCode", "")
        name = params.get("name", "")
        if not (postal_code and name):
            return {"error": "Could not extract both postalCode and name from the prompt."}
    except Exception as e:
        return {"error": f"LLM parsing failed: {e}"}
    # Query local API
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # For debugging: log the actual backend call
            debug_curl = (
                f"curl -X GET 'http://localhost:8000/api/organization/search?postalCode={postal_code}&name={name}'"
            )
            print(f"[MCP DEBUG] Would run: {debug_curl}")
            resp = await client.get(
                "http://localhost:8000/api/organization/search",
                params={"postalCode": postal_code, "name": name}
            )
            data = resp.json()
            # FHIR: extract first 3 organizations from 'entry' array
            entries = data.get("entry", [])[:3]
            results = []
            for entry in entries:
                org = entry.get("resource", {})
                results.append({
                    "id": org.get("id"),
                    "name": org.get("name"),
                    "address": org.get("address", [{}])[0] if org.get("address") else None,
                    "type": org.get("type", [{}])[0]["coding"][0]["code"] if org.get("type") and org.get("type")[0].get("coding") else None,
                    "active": org.get("active"),
                    "lastUpdated": org.get("meta", {}).get("lastUpdated")
                })
            return {
                "choices": [
                    {
                        "message": {
                            "content": f"Here are 3 results for '{name}' in {postal_code}: " +
                                       ", ".join([r.get("name", "Unknown") for r in results])
                        },
                        "data": results
                    }
                ]
            }
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        return {"error": f"Backend API call failed: {e}", "traceback": tb}

class QueryRequest(BaseModel):
    query: str

@app.post("/mcp/organization_context")
def mcp_organization_context(req: QueryRequest):
    return {"result": organization_context(req.query)}
