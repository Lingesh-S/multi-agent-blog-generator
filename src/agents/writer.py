"""
Writer Agent

Responsible for drafting blog posts based on research data.
"""

from typing import Dict, Any
from src.agents.base import BaseAgent
from src.state.schema import AgentState
from src.tools.llm import LLMProvider
from src.config import get_settings


class WriterAgent(BaseAgent):
    """
    Agent that writes blog posts based on research data.
    
    Responsibilities:
    - Generate blog post from research data
    - Follow user requirements and tone
    - Meet word count targets
    - Create engaging titles
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(name="Writer", config=config)
        
        settings = get_settings()
        self.llm = LLMProvider()
        self.min_words = settings.writer_min_words
        
    def execute(self, state: AgentState) -> Dict[str, Any]:
        """
        Write a blog post based on research data.
        
        Args:
            state: Current state with research_data
            
        Returns:
            Dictionary with blog_post and blog_title
        """
        # Validate input
        is_valid, error = self.validate_input(state, ["topic", "research_data"])
        if not is_valid:
            raise ValueError(error)
        
        topic = state["topic"]
        research_data = state["research_data"]
        
        # Get writing parameters from state
        target_audience = state.get("target_audience", "general")
        tone = state.get("tone", "professional")
        word_count = state.get("word_count", 500)
        user_requirements = state.get("user_requirements", "")
        
        self.logger.info(f"Writing blog post about: {topic}")
        
        # Build prompt
        prompt = self._build_writing_prompt(
            topic=topic,
            research_data=research_data,
            target_audience=target_audience,
            tone=tone,
            word_count=word_count,
            user_requirements=user_requirements
        )
        
        # Generate blog post
        blog_post = self.llm.generate(prompt)
        
        # Generate title
        title = self._generate_title(topic, blog_post)
        
        # Extract metadata
        metadata = self._extract_metadata(blog_post)
        
        # Calculate actual word count
        actual_word_count = len(blog_post.split())
        
        self.logger.info(f"Blog post generated: {actual_word_count} words")
        
        # Log metrics
        self.log_metric("blog_word_count", actual_word_count)
        self.log_metric("word_count_accuracy", actual_word_count / word_count if word_count > 0 else 0)
        
        # Increment draft iterations
        draft_iterations = state.get("draft_iterations", 0) + 1
        
        return {
            "blog_post": blog_post,
            "blog_title": title,
            "blog_metadata": metadata,
            "draft_iterations": draft_iterations
        }
    
    def _build_writing_prompt(
        self,
        topic: str,
        research_data: list,
        target_audience: str,
        tone: str,
        word_count: int,
        user_requirements: str
    ) -> str:
        """
        Build comprehensive prompt for blog writing.
        
        Returns:
            Formatted prompt string
        """
        # Combine research data
        research_text = "\n\n".join(research_data)
        
        prompt = f"""You are a professional blog writer. Write a comprehensive blog post about "{topic}".

RESEARCH DATA:
{research_text}

REQUIREMENTS:
- Target Audience: {target_audience}
- Tone: {tone}
- Target Word Count: {word_count} words
- Writing Style: Clear, engaging, and informative
{f"- Additional Requirements: {user_requirements}" if user_requirements else ""}

INSTRUCTIONS:
1. Write ONLY based on the research data provided above
2. Create an engaging introduction that hooks the reader
3. Organize content with clear sections and logical flow
4. Use specific facts, statistics, and examples from the research
5. Write in {tone} tone appropriate for {target_audience} audience
6. Aim for approximately {word_count} words
7. End with a strong conclusion that summarizes key points
8. Do NOT include a title (title will be generated separately)
9. Do NOT include citations or footnotes in the text

Write the blog post now:"""
        
        return prompt
    
    def _generate_title(self, topic: str, blog_post: str) -> str:
        """
        Generate an engaging title for the blog post.
        
        Args:
            topic: Original topic
            blog_post: Generated blog content
            
        Returns:
            Blog title string
        """
        # Extract first paragraph for context
        first_para = blog_post.split("\n\n")[0] if "\n\n" in blog_post else blog_post[:300]
        
        prompt = f"""Generate an engaging, click-worthy title for this blog post about "{topic}".

First paragraph of the blog:
{first_para}

Requirements:
- 6-12 words long
- Clear and descriptive
- Engaging and interesting
- No clickbait
- Professional tone

Generate ONLY the title, nothing else:"""
        
        title = self.llm.generate(prompt, temperature=0.8, max_tokens=50)
        
        # Clean up the title
        title = title.strip().strip('"').strip("'")
        
        # Fallback if generation fails
        if not title or len(title) < 10:
            title = f"{topic}: A Comprehensive Guide"
        
        return title
    
    def _extract_metadata(self, blog_post: str) -> Dict[str, Any]:
        """
        Extract metadata from the blog post.
        
        Args:
            blog_post: Generated blog content
            
        Returns:
            Metadata dictionary
        """
        word_count = len(blog_post.split())
        char_count = len(blog_post)
        paragraph_count = len([p for p in blog_post.split("\n\n") if p.strip()])
        
        # Estimate reading time (average reading speed: 200 words/minute)
        reading_time_minutes = max(1, round(word_count / 200))
        
        return {
            "word_count": word_count,
            "character_count": char_count,
            "paragraph_count": paragraph_count,
            "estimated_reading_time": reading_time_minutes
        }


class WriterAgentWithRevision(WriterAgent):
    """
    Extended writer agent that can revise based on feedback.
    """
    
    def revise(self, state: AgentState) -> Dict[str, Any]:
        """
        Revise the blog post based on editor feedback.
        
        Args:
            state: State containing blog_post and editor_feedback
            
        Returns:
            Dictionary with revised blog_post
        """
        blog_post = state.get("blog_post", "")
        feedback = state.get("editor_feedback", "")
        
        if not feedback:
            self.logger.warning("No feedback provided for revision")
            return {}
        
        self.logger.info("Revising blog post based on feedback")
        
        prompt = f"""You are revising a blog post based on editor feedback.

ORIGINAL BLOG POST:
{blog_post}

EDITOR FEEDBACK:
{feedback}

INSTRUCTIONS:
Revise the blog post addressing all the feedback points. Keep what works well and improve what needs work.

Write the revised blog post:"""
        
        revised_post = self.llm.generate(prompt)
        
        return {
            "blog_post": revised_post,
            "draft_iterations": state.get("draft_iterations", 0) + 1
        }
