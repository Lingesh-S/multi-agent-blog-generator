"""
Editor Agent

Responsible for reviewing and providing feedback on blog posts.
"""

from typing import Dict, Any
from src.agents.base import ConditionalAgent
from src.state.schema import AgentState
from src.tools.llm import LLMProvider


class EditorAgent(ConditionalAgent):
    """
    Agent that reviews blog posts and provides quality feedback.
    
    Responsibilities:
    - Review blog post quality
    - Check adherence to requirements
    - Provide constructive feedback
    - Assign quality score
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(name="Editor", config=config)
        self.llm = LLMProvider()
        
        # Quality thresholds
        self.min_quality_score = self.get_config("min_quality_score", 0.7)
    
    def should_execute(self, state: AgentState) -> bool:
        """Editor only executes if blog post exists"""
        return bool(state.get("blog_post"))
    
    def execute(self, state: AgentState) -> Dict[str, Any]:
        """
        Review the blog post and provide feedback.
        
        Args:
            state: Current state with blog_post
            
        Returns:
            Dictionary with editor_feedback, quality_score, and needs_revision
        """
        # Validate input
        is_valid, error = self.validate_input(state, ["blog_post", "topic"])
        if not is_valid:
            raise ValueError(error)
        
        blog_post = state["blog_post"]
        topic = state["topic"]
        user_requirements = state.get("user_requirements", "")
        target_audience = state.get("target_audience", "general")
        tone = state.get("tone", "professional")
        word_count_target = state.get("word_count", 500)
        
        self.logger.info("Reviewing blog post")
        
        # Generate review
        feedback, quality_score = self._review_post(
            blog_post=blog_post,
            topic=topic,
            user_requirements=user_requirements,
            target_audience=target_audience,
            tone=tone,
            word_count_target=word_count_target
        )
        
        # Determine if revision is needed
        needs_revision = quality_score < self.min_quality_score
        
        self.logger.info(
            f"Review complete. Quality: {quality_score:.2f}, "
            f"Needs revision: {needs_revision}"
        )
        
        # Log metrics
        self.log_metric("quality_score", quality_score)
        self.log_metric("needs_revision", 1.0 if needs_revision else 0.0)
        
        return {
            "editor_feedback": feedback,
            "quality_score": quality_score,
            "needs_revision": needs_revision
        }
    
    def _review_post(
        self,
        blog_post: str,
        topic: str,
        user_requirements: str,
        target_audience: str,
        tone: str,
        word_count_target: int
    ) -> tuple[str, float]:
        """
        Generate detailed review and quality score.
        
        Returns:
            Tuple of (feedback_text, quality_score)
        """
        # Build review prompt
        prompt = self._build_review_prompt(
            blog_post=blog_post,
            topic=topic,
            user_requirements=user_requirements,
            target_audience=target_audience,
            tone=tone,
            word_count_target=word_count_target
        )
        
        # Get LLM review
        review_text = self.llm.generate(prompt, temperature=0.3)
        
        # Extract quality score from review
        quality_score = self._extract_quality_score(review_text, blog_post, word_count_target)
        
        return review_text, quality_score
    
    def _build_review_prompt(
        self,
        blog_post: str,
        topic: str,
        user_requirements: str,
        target_audience: str,
        tone: str,
        word_count_target: int
    ) -> str:
        """Build comprehensive review prompt"""
        
        prompt = f"""You are a professional blog editor. Review the following blog post.

TOPIC: {topic}
TARGET AUDIENCE: {target_audience}
DESIRED TONE: {tone}
TARGET WORD COUNT: {word_count_target}
{f"ADDITIONAL REQUIREMENTS: {user_requirements}" if user_requirements else ""}

BLOG POST TO REVIEW:
{blog_post}

REVIEW CRITERIA:
1. Content Quality: Is the information accurate, relevant, and valuable?
2. Structure: Is the post well-organized with clear flow?
3. Tone & Style: Does it match the {tone} tone for {target_audience} audience?
4. Engagement: Is it interesting and easy to read?
5. Length: Is the word count appropriate?
6. Grammar & Clarity: Is the writing clear and error-free?

Provide a constructive review covering:
- What works well (2-3 points)
- What needs improvement (2-3 specific actionable points)
- Overall assessment

Write your review:"""
        
        return prompt
    
    def _extract_quality_score(
        self,
        review_text: str,
        blog_post: str,
        word_count_target: int
    ) -> float:
        """
        Calculate quality score based on review and metrics.
        
        Returns:
            Quality score between 0.0 and 1.0
        """
        score = 0.0
        
        # Word count accuracy (20% of score)
        actual_words = len(blog_post.split())
        word_count_ratio = min(actual_words / word_count_target, word_count_target / actual_words)
        score += 0.2 * word_count_ratio
        
        # Content length check (20% of score)
        if actual_words >= 200:
            score += 0.2
        elif actual_words >= 100:
            score += 0.1
        
        # Structure check - has paragraphs (20% of score)
        paragraphs = [p for p in blog_post.split("\n\n") if p.strip()]
        if len(paragraphs) >= 3:
            score += 0.2
        elif len(paragraphs) >= 2:
            score += 0.1
        
        # Review sentiment analysis (40% of score)
        # Simple heuristic: count positive vs negative indicators
        review_lower = review_text.lower()
        
        positive_indicators = [
            "good", "excellent", "well", "clear", "strong",
            "effective", "engaging", "works well"
        ]
        negative_indicators = [
            "weak", "poor", "lacks", "missing", "confusing",
            "needs improvement", "unclear", "too short", "too long"
        ]
        
        positive_count = sum(1 for word in positive_indicators if word in review_lower)
        negative_count = sum(1 for word in negative_indicators if word in review_lower)
        
        if positive_count + negative_count > 0:
            sentiment_score = positive_count / (positive_count + negative_count)
            score += 0.4 * sentiment_score
        else:
            score += 0.2  # Neutral if no clear indicators
        
        # Ensure score is in valid range
        return max(0.0, min(1.0, score))


class SimpleEditorAgent(ConditionalAgent):
    """
    Simplified editor that uses rule-based checks only (no LLM).
    
    Useful for faster feedback or when LLM calls should be minimized.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(name="SimpleEditor", config=config)
    
    def should_execute(self, state: AgentState) -> bool:
        """Execute if blog post exists"""
        return bool(state.get("blog_post"))
    
    def execute(self, state: AgentState) -> Dict[str, Any]:
        """
        Perform rule-based quality checks.
        
        Args:
            state: Current state
            
        Returns:
            Dictionary with quality assessment
        """
        blog_post = state.get("blog_post", "")
        word_count_target = state.get("word_count", 500)
        
        # Calculate metrics
        actual_words = len(blog_post.split())
        paragraphs = len([p for p in blog_post.split("\n\n") if p.strip()])
        
        feedback_points = []
        score = 1.0
        
        # Check word count
        word_diff_ratio = abs(actual_words - word_count_target) / word_count_target
        if word_diff_ratio > 0.3:
            feedback_points.append(
                f"Word count is {actual_words} (target: {word_count_target}). "
                "Consider adjusting length."
            )
            score -= 0.2
        
        # Check structure
        if paragraphs < 3:
            feedback_points.append("Add more paragraphs for better structure.")
            score -= 0.2
        
        # Check minimum length
        if actual_words < 100:
            feedback_points.append("Content is too short. Add more detail.")
            score -= 0.3
        
        # Generate feedback
        if feedback_points:
            feedback = "Issues found:\n" + "\n".join(f"- {p}" for p in feedback_points)
        else:
            feedback = "Blog post meets basic quality standards."
        
        quality_score = max(0.0, score)
        needs_revision = quality_score < 0.7
        
        self.logger.info(f"Simple review complete. Score: {quality_score:.2f}")
        
        return {
            "editor_feedback": feedback,
            "quality_score": quality_score,
            "needs_revision": needs_revision
        }
