"""
Summarizer proxy for calling AI Summarizer service
"""

import asyncio
import aiohttp
import json
import logging
from typing import List, Dict, Any, Optional
import time

from schemas import CodeSnippet, Summary, NodeReference
from config import settings

logger = logging.getLogger(__name__)

class SummarizerProxy:
    """Proxy service for AI summarization"""
    
    def __init__(self):
        self.summarizer_url = settings.SUMMARIZER_URL
        self.timeout = settings.SUMMARIZER_TIMEOUT
        self.max_retries = 3
        self.fallback_enabled = True
        
    async def summarize(self, snippets: List[CodeSnippet], question: str) -> Summary:
        """
        Generate summary for code snippets
        
        Args:
            snippets: List of code snippets
            question: User's question
            
        Returns:
            Generated summary
        """
        try:
            # First try external summarizer service
            if self.summarizer_url:
                summary = await self._call_external_summarizer(snippets, question)
                if summary:
                    return summary
            
            # Fallback to local summarization
            return await self._fallback_summarize(snippets, question)
            
        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            return await self._fallback_summarize(snippets, question)
    
    async def _call_external_summarizer(self, snippets: List[CodeSnippet], question: str) -> Optional[Summary]:
        """Call external AI summarizer service"""
        try:
            payload = {
                "snippets": [
                    {
                        "node_id": snippet.node_id,
                        "code": snippet.code,
                        "file": snippet.file,
                        "start_line": snippet.start_line,
                        "end_line": snippet.end_line,
                        "doc": snippet.doc
                    } for snippet in snippets
                ],
                "question": question,
                "max_tokens": 400
            }
            
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                for attempt in range(self.max_retries):
                    try:
                        async with session.post(
                            f"{self.summarizer_url}/summarize",
                            json=payload,
                            headers={"Content-Type": "application/json"}
                        ) as response:
                            
                            if response.status == 200:
                                result = await response.json()
                                return self._parse_summary_response(result)
                            else:
                                logger.warning(f"Summarizer returned status {response.status}")
                                
                    except asyncio.TimeoutError:
                        logger.warning(f"Summarizer timeout (attempt {attempt + 1})")
                        if attempt < self.max_retries - 1:
                            await asyncio.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    except Exception as e:
                        logger.warning(f"Summarizer request failed (attempt {attempt + 1}): {e}")
                        if attempt < self.max_retries - 1:
                            await asyncio.sleep(2 ** attempt)
                        continue
            
            return None
            
        except Exception as e:
            logger.error(f"External summarizer call failed: {e}")
            return None
    
    def _parse_summary_response(self, response: Dict[str, Any]) -> Summary:
        """Parse response from external summarizer"""
        summary_data = response.get("summary", {})
        
        return Summary(
            one_liner=summary_data.get("one_liner", "Code analysis summary"),
            steps=summary_data.get("steps", []),
            inputs_outputs=summary_data.get("inputs_outputs", []),
            caveats=summary_data.get("caveats", []),
            node_refs=[
                NodeReference(**ref) for ref in summary_data.get("node_refs", [])
            ]
        )
    
    async def _fallback_summarize(self, snippets: List[CodeSnippet], question: str) -> Summary:
        """Fallback summarization using simple heuristics"""
        try:
            # Generate basic summary components
            one_liner = self._generate_oneliner(snippets, question)
            steps = self._generate_steps(snippets)
            inputs_outputs = self._analyze_inputs_outputs(snippets)
            caveats = self._generate_caveats(snippets)
            node_refs = self._create_node_references(snippets)
            
            return Summary(
                one_liner=one_liner,
                steps=steps,
                inputs_outputs=inputs_outputs,
                caveats=caveats,
                node_refs=node_refs
            )
            
        except Exception as e:
            logger.error(f"Fallback summarization failed: {e}")
            return self._create_minimal_summary(snippets)
    
    def _generate_oneliner(self, snippets: List[CodeSnippet], question: str) -> str:
        """Generate a one-line summary"""
        if not snippets:
            return "No relevant code found for the query."
        
        # Extract function/class names
        names = []
        files = set()
        
        for snippet in snippets:
            # Simple extraction of function/class names from node_id
            parts = snippet.node_id.split(':')
            if len(parts) >= 2:
                name_part = parts[0].split('.')[-1]  # Get last part after dot
                names.append(name_part)
            files.add(snippet.file)
        
        if len(names) == 1:
            return f"The query relates to {names[0]} in {list(files)[0]}"
        elif len(names) <= 3:
            return f"The query involves {', '.join(names)} across {len(files)} file(s)"
        else:
            return f"The query spans {len(names)} functions/classes across {len(files)} files"
    
    def _generate_steps(self, snippets: List[CodeSnippet]) -> List[str]:
        """Generate step-by-step breakdown"""
        steps = []
        
        for i, snippet in enumerate(snippets[:5], 1):  # Limit to 5 steps
            # Extract function name from node_id
            parts = snippet.node_id.split(':')
            name = parts[0].split('.')[-1] if parts else f"Function {i}"
            
            # Simple step description
            if snippet.doc:
                # Use first line of docstring
                doc_first_line = snippet.doc.split('\n')[0].strip().strip('"""').strip("'''").strip()
                steps.append(f"{i}. {name}: {doc_first_line}")
            else:
                # Use function signature or first line
                first_line = snippet.code.split('\n')[0].strip()
                if first_line.startswith(('def ', 'class ', 'async def ')):
                    steps.append(f"{i}. {name}: {first_line}")
                else:
                    steps.append(f"{i}. {name}: Executes core logic")
        
        return steps
    
    def _analyze_inputs_outputs(self, snippets: List[CodeSnippet]) -> List[str]:
        """Analyze inputs and outputs"""
        inputs_outputs = []
        
        for snippet in snippets[:3]:  # Analyze first 3 snippets
            # Simple pattern matching for common I/O patterns
            code_lower = snippet.code.lower()
            
            if 'return' in code_lower:
                inputs_outputs.append(f"{snippet.node_id.split(':')[0]}: Returns processed data")
            
            if any(pattern in code_lower for pattern in ['request', 'input', 'param']):
                inputs_outputs.append(f"{snippet.node_id.split(':')[0]}: Accepts input parameters")
            
            if any(pattern in code_lower for pattern in ['response', 'output', 'result']):
                inputs_outputs.append(f"{snippet.node_id.split(':')[0]}: Produces output")
        
        return list(set(inputs_outputs))  # Remove duplicates
    
    def _generate_caveats(self, snippets: List[CodeSnippet]) -> List[str]:
        """Generate caveats and warnings"""
        caveats = []
        
        # Check for common patterns that might need attention
        for snippet in snippets:
            code_lower = snippet.code.lower()
            
            if any(pattern in code_lower for pattern in ['todo', 'fixme', 'hack']):
                caveats.append("Some code contains TODO or FIXME comments")
            
            if any(pattern in code_lower for pattern in ['exception', 'error', 'raise']):
                caveats.append("Error handling present - check exception flows")
            
            if any(pattern in code_lower for pattern in ['async', 'await']):
                caveats.append("Contains asynchronous code - consider execution context")
            
            if 'deprecated' in code_lower:
                caveats.append("Some functions may be deprecated")
        
        return list(set(caveats))[:3]  # Limit to 3 unique caveats
    
    def _create_node_references(self, snippets: List[CodeSnippet]) -> List[NodeReference]:
        """Create node references"""
        refs = []
        
        for snippet in snippets[:5]:  # Limit to 5 references
            # Extract key line (function signature or first meaningful line)
            lines = snippet.code.split('\n')
            key_line = ""
            
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#') and not line.startswith('"""'):
                    key_line = line
                    break
            
            if not key_line and lines:
                key_line = lines[0].strip()
            
            refs.append(NodeReference(
                node_id=snippet.node_id,
                excerpt_line=key_line[:100]  # Limit length
            ))
        
        return refs
    
    def _create_minimal_summary(self, snippets: List[CodeSnippet]) -> Summary:
        """Create minimal summary when everything else fails"""
        return Summary(
            one_liner=f"Analysis of {len(snippets)} code snippet(s)",
            steps=[f"Step {i+1}: Processing {snippet.node_id.split(':')[0]}" 
                   for i, snippet in enumerate(snippets[:3])],
            inputs_outputs=["Function inputs and outputs need manual review"],
            caveats=["Automated analysis unavailable"],
            node_refs=[NodeReference(
                node_id=snippet.node_id,
                excerpt_line="Manual review required"
            ) for snippet in snippets[:3]]
        )
    
    async def health_check(self) -> Dict[str, Any]:
        """Check if summarizer service is healthy"""
        if not self.summarizer_url:
            return {
                "status": "fallback_only",
                "message": "No external summarizer configured"
            }
        
        try:
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(f"{self.summarizer_url}/health") as response:
                    if response.status == 200:
                        return {
                            "status": "healthy",
                            "message": "External summarizer available"
                        }
                    else:
                        return {
                            "status": "unhealthy",
                            "message": f"Summarizer returned status {response.status}"
                        }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Summarizer health check failed: {str(e)}"
            }