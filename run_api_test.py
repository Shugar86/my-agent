import asyncio, time, os, json

# Load keys from .env or environment — never hardcode secrets in source.
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from core.llm_gateway import LLMGateway
from core.skill_cache import filter_skills_by_query
from tools.web_tools import web_search

def test_provider(name, model, api_key, base_url, messages, tools=None):
    gw = LLMGateway({'primary': model, 'api_key': api_key, 'base_url': base_url, 'params': {'max_tokens': 50}})
    t0 = time.time()
    try:
        msg = asyncio.run(gw.chat(messages, tools=tools))
        elapsed = time.time() - t0
        return {'ok': True, 'time': elapsed, 'content': getattr(msg, 'content', str(msg))[:80], 'error': None}
    except Exception as e:
        elapsed = time.time() - t0
        return {'ok': False, 'time': elapsed, 'content': '', 'error': str(e)[:200]}

results = {}

# Test 1: NeuroAPI simple
results['neuroapi_simple'] = test_provider('NeuroAPI', 'openai/gpt-5.4-nano', os.environ['NEUROAPI_API_KEY'], 'https://neuroapi.host/v1', [{'role': 'user', 'content': 'say hi in 2 words'}])

# Test 2: NeuroAPI with tools
from core.tool_registry import registry
from tools.web_tools import register_tools
register_tools()
tools = registry.get_schemas()
results['neuroapi_tools'] = test_provider('NeuroAPI+tools', 'openai/gpt-5.4-nano', os.environ['NEUROAPI_API_KEY'], 'https://neuroapi.host/v1', [{'role': 'user', 'content': 'search for AI news'}], tools[:3] if tools else None)

# Test 3: OpenRouter simple
results['openrouter_simple'] = test_provider('OpenRouter', 'openrouter/owl-alpha', os.environ['OPENROUTER_API_KEY'], 'https://openrouter.ai/api/v1', [{'role': 'user', 'content': 'say hi in 2 words'}])

# Test 4: OpenRouter with tools
results['openrouter_tools'] = test_provider('OpenRouter+tools', 'openrouter/owl-alpha', os.environ['OPENROUTER_API_KEY'], 'https://openrouter.ai/api/v1', [{'role': 'user', 'content': 'search for AI news'}], tools[:3] if tools else None)

# Test 5: Tavily search
t0 = time.time()
try:
    r = web_search('AI agents 2026', max_results=3)
    results['tavily'] = {'ok': True, 'time': time.time()-t0, 'results': len(r) if isinstance(r, list) else 0, 'error': None}
except Exception as e:
    results['tavily'] = {'ok': False, 'time': time.time()-t0, 'results': 0, 'error': str(e)[:200]}

# Test 6: Skill cache
r = filter_skills_by_query('search web for news', ['web_search', 'deep_search', 'execute_code', 'file_read', 'send_email', 'create_chart', 'ocr_image', 'browser_navigate'])
results['skill_cache'] = {'ok': True, 'filtered': r, 'count': len(r)}

# Test 7: Fallback mechanism (simulate failure on primary)
gw = LLMGateway({'primary': 'openai/gpt-5.4-nano', 'fallback': 'openrouter/owl-alpha', 'api_key': os.environ['NEUROAPI_API_KEY'], 'base_url': 'https://neuroapi.host/v1', 'fallback_api_key': os.environ['OPENROUTER_API_KEY'], 'fallback_base_url': 'https://openrouter.ai/api/v1', 'params': {'max_tokens': 20}})
t0 = time.time()
msg = asyncio.run(gw.chat([{'role': 'user', 'content': 'hello'}]))
results['fallback'] = {'ok': True, 'time': time.time()-t0, 'content': getattr(msg, 'content', str(msg))[:80]}

with open('results.json', 'w', encoding='utf-8') as f:
    f.write(json.dumps(results, indent=2, ensure_ascii=False))
