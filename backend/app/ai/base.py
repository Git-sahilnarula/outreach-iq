from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from app.schemas.job_analysis import JobAnalysisCreate
from app.schemas.proposal import ProposalGenerated

class AIProvider(ABC):
    """Abstract base class for AI providers"""
    
    @abstractmethod
    async def analyze_opportunity(
        self,
        job_description: str,
        startup_profile: Dict[str, Any],
        portfolio_projects: List[Dict[str, Any]]
    ) -> JobAnalysisCreate:
        """
        Analyze a job opportunity against the startup profile.
        
        Args:
            job_description: The job description text
            startup_profile: Dictionary containing startup profile data
            portfolio_projects: List of portfolio project dictionaries
            
        Returns:
            JobAnalysisCreate: Structured analysis result
        """
        pass

    @abstractmethod
    async def generate_proposal(
        self,
        job_details: Dict[str, Any],
        startup_profile: Dict[str, Any],
        portfolio_projects: List[Dict[str, Any]],
        tone: str = "professional",
        custom_instructions: Optional[str] = None
    ) -> ProposalGenerated:
        """
        Generate a client proposal and cover letter pitch for an opportunity.
        
        Args:
            job_details: Dict of job info (title, company, description, budget, etc.)
            startup_profile: Dictionary containing startup profile data
            portfolio_projects: List of portfolio project dictionaries
            tone: Desired voice/tone (e.g. professional, consultative, conversational, bold, technical)
            custom_instructions: Optional user instructions
            
        Returns:
            ProposalGenerated: Structured proposal result
        """
        pass
    
    @abstractmethod
    async def generate_linkedin_messages(
        self,
        job_details: Dict[str, Any],
        startup_profile: Dict[str, Any],
        portfolio_projects: List[Dict[str, Any]],
        recipient_name: Optional[str] = None,
        recipient_role: Optional[str] = None,
        tone: str = "value_first",
        custom_instructions: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Generate LinkedIn connection request note (strictly <= 300 chars) and InMail pitch.
        
        Args:
            job_details: Dict of job info (title, company, description, etc.)
            startup_profile: Dictionary containing startup profile data
            portfolio_projects: List of portfolio project dictionaries
            recipient_name: Target person name (e.g. hiring manager, CTO)
            recipient_role: Target person role/title
            tone: Desired tone (e.g. value_first, direct, networking, thought_leadership)
            custom_instructions: Optional user instructions
            
        Returns:
            Dict[str, str] with keys: connection_note, inmail_subject, inmail_body
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the AI provider is available and healthy"""
        pass

