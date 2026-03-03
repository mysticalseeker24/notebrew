import openai
from typing import Dict, List, Optional
from app.config import settings
import json
import re

class CodeGenerator:
    """Generate PyTorch code from research papers using Gemini 3 Flash Preview or MiniMax M2.5"""
    
    def __init__(self, model: Optional[str] = None):
        self.model = model or settings.PRIMARY_MODEL
        self.client = openai.OpenAI(
            base_url=settings.OPENROUTER_BASE_URL,
            api_key=settings.OPENROUTER_API_KEY,
        )
        
    def _get_model_name(self, model_type: str) -> str:
        """Get the full model name for OpenRouter"""
        if model_type == "gemini-3-flash-preview":
            return settings.GEMINI_3_FLASH_MODEL
        elif model_type == "minimax-m2.5":
            return settings.MINIMAX_M25_MODEL
        return settings.GEMINI_3_FLASH_MODEL
    
    def generate_code_from_section(
        self, 
        section_title: str, 
        section_content: str, 
        equations: List[str],
        paper_context: str
    ) -> Dict[str, any]:
        """Generate PyTorch code for a specific section"""
        
        prompt = self._create_code_generation_prompt(
            section_title, section_content, equations, paper_context
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self._get_model_name(self.model),
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert ML researcher and PyTorch developer. 
                        Your task is to convert research paper descriptions into clean, runnable PyTorch code.
                        
                        Guidelines:
                        - Generate production-quality PyTorch code
                        - Scale down models for CPU execution (smaller dimensions, fewer layers)
                        - Include proper imports and dependencies
                        - Add clear comments explaining the implementation
                        - Implement equations from the paper accurately
                        - Use modern PyTorch conventions (torch.nn.Module, etc.)
                        - Make code self-contained and runnable
                        - Include data generation/loading where needed
                        - Add visualization code where appropriate
                        """
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=4000,
            )
            
            code_content = response.choices[0].message.content
            
            # Extract code blocks
            code_blocks = self._extract_code_blocks(code_content)
            dependencies = self._extract_dependencies(code_content)
            
            return {
                'code_blocks': code_blocks,
                'dependencies': dependencies,
                'explanation': code_content,
                'model_used': self.model
            }
            
        except Exception as e:
            # Fallback to alternative model
            if self.model == settings.PRIMARY_MODEL:
                print(f"Primary model failed, trying fallback: {e}")
                fallback_generator = CodeGenerator(model=settings.FALLBACK_MODEL)
                return fallback_generator.generate_code_from_section(
                    section_title, section_content, equations, paper_context
                )
            raise
    
    def _create_code_generation_prompt(
        self,
        section_title: str,
        section_content: str,
        equations: List[str],
        paper_context: str
    ) -> str:
        """Create a detailed prompt for code generation"""
        
        equations_str = "\n".join([f"- {eq}" for eq in equations]) if equations else "No equations in this section"
        
        prompt = f"""
# Task: Generate PyTorch Implementation

## Paper Section: {section_title}

## Section Content:
{section_content[:3000]}  # Limit content length

## Relevant Equations:
{equations_str}

## Full Paper Context:
{paper_context[:1000]}  # Brief context

## Requirements:
1. Implement the methodology described in this section using PyTorch
2. Scale down model dimensions for CPU execution (e.g., 64 hidden dims instead of 512)
3. Include sample data generation if needed
4. Implement all equations accurately
5. Add visualization code (matplotlib/seaborn) where appropriate
6. Make code executable in a Jupyter notebook environment
7. Include clear comments and docstrings

## Output Format:
Provide:
1. Complete, runnable Python code blocks
2. List of required dependencies
3. Brief explanation of the implementation

Generate the code now:
"""
        return prompt
    
    def _extract_code_blocks(self, content: str) -> List[str]:
        """Extract code blocks from markdown-formatted content"""
        # Pattern for code blocks
        pattern = r'```python\n(.*?)```'
        matches = re.findall(pattern, content, re.DOTALL)
        
        if not matches:
            # Try without language specifier
            pattern = r'```\n(.*?)```'
            matches = re.findall(pattern, content, re.DOTALL)
        
        return [match.strip() for match in matches]
    
    def _extract_dependencies(self, content: str) -> List[str]:
        """Extract Python dependencies from code"""
        dependencies = set([
            'torch',
            'numpy',
            'matplotlib',
            'seaborn',
        ])
        
        # Common imports
        import_patterns = [
            r'import (\w+)',
            r'from (\w+) import',
        ]
        
        for pattern in import_patterns:
            matches = re.findall(pattern, content)
            dependencies.update(matches)
        
        # Remove standard library modules
        stdlib = {'os', 'sys', 'math', 'random', 're', 'json', 'time', 'datetime', 'collections'}
        dependencies = dependencies - stdlib
        
        return sorted(list(dependencies))
    
    def generate_complete_notebook(
        self,
        paper_structure: Dict,
        sections: List[str] = None
    ) -> Dict:
        """Generate complete notebook from paper structure"""
        
        if sections is None:
            sections = ['abstract', 'methodology', 'experiments', 'conclusion']
        
        notebook_data = {
            'metadata': paper_structure.get('metadata', {}),
            'sections': [],
            'all_dependencies': set()
        }
        
        paper_context = f"""
Title: {paper_structure['metadata'].get('title', 'Unknown')}
Abstract: {paper_structure['sections'].get('abstract', '')[:500]}
"""
        
        for section_name in sections:
            if section_name in paper_structure['sections']:
                section_content = paper_structure['sections'][section_name]
                
                # Get relevant equations for this section
                all_equations = paper_structure.get('equations', [])
                
                print(f"Generating code for section: {section_name}")
                
                section_result = self.generate_code_from_section(
                    section_title=section_name.title(),
                    section_content=section_content,
                    equations=all_equations,
                    paper_context=paper_context
                )
                
                notebook_data['sections'].append({
                    'name': section_name,
                    'content': section_content,
                    'code': section_result
                })
                
                notebook_data['all_dependencies'].update(section_result['dependencies'])
        
        notebook_data['all_dependencies'] = sorted(list(notebook_data['all_dependencies']))
        
        return notebook_data
