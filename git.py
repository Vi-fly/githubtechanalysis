import requests
import os
import streamlit as st
from phi.agent import Agent
from phi.model.groq import Groq
from dotenv import load_dotenv
import re

# Load environment variables from .env file
load_dotenv('py.env')

# GitHub API base URL
GITHUB_API_URL = "https://api.github.com/users/"

# Initialize the Groq model with API key
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("Missing GROQ API Key. Please set it in the .env file.")

# Initialize the Groq model
groq_model = Groq(id="mixtral-8x7b-32768", api_key=GROQ_API_KEY)

# Function to fetch GitHub user details
def fetch_github_user_details(username: str):
    user_url = f"{GITHUB_API_URL}{username}"
    user_response = requests.get(user_url)
    if user_response.status_code != 200:
        raise ValueError(f"Failed to fetch user details: {user_response.status_code} - {user_response.text}")
    user_data = user_response.json()

    # Fetch user repositories
    repos_url = user_data["repos_url"]
    repos_response = requests.get(repos_url)
    if repos_response.status_code != 200:
        raise ValueError(f"Failed to fetch repositories: {repos_response.status_code} - {repos_response.text}")
    repos_data = repos_response.json()

    return {"user_profile": user_data, "repositories": repos_data}

class GitHubAssessmentAgent(Agent):
    """
    AI Agent for assessing technical skills based on a GitHub profile.
    """
    def __init__(self):
        super().__init__(
            name="GitHub Assessment Agent",
            model=groq_model,
            instructions=["Provide a detailed analysis of the user’s technical expertise, strengths, and areas for improvement."],
            show_tool_calls=True,
            markdown=True
        )

    def generate_skill_assessment(self, username: str):
        """
        Generates a technical skill assessment for a GitHub user.
        """
        github_data = fetch_github_user_details(username)

        user_profile = github_data["user_profile"]
        repositories = github_data["repositories"]

        # Extract meaningful information for assessment
        repo_summaries = []
        for repo in repositories:
            repo_summaries.append(f"- **{repo['name']}**: {repo.get('description', 'No description')} (Language: {repo.get('language', 'Unknown')})")

        # Create the assessment prompt
        prompt = f"""
        Based on the following GitHub profile, assess the user's technical skills:

        ### User Information:
        - **Name**: {user_profile.get('name', 'N/A')}
        - **Bio**: {user_profile.get('bio', 'N/A')}
        - **Public Repositories**: {user_profile['public_repos']}

        ### Repositories:
        {chr(10).join(repo_summaries)}

        ### Analysis Instructions:
        Provide a detailed analysis of the user’s technical expertise, strengths, and areas for improvement. Use markdown format for clarity.
        """

        # Use the Agent to generate the assessment
        response = self.run(prompt)
        return response

# Streamlit frontend
def main():
    st.title("GitHub Technical Skill Assessment")
    
    # Input: GitHub Username
    username = st.text_input("Enter GitHub username", "")

    if username:
        agent = GitHubAssessmentAgent()
        
        try:
            # Get assessment result as a string
            assessment = agent.generate_skill_assessment(username)
            assessment_str = str(assessment)
            if assessment_str.startswith("content="):
                assessment_str = assessment_str.replace("content=", "", 1)
            
            # Clean up and decode the assessment string for display
            assessment_str = re.sub(r'name=None.*', '', assessment_str, flags=re.DOTALL)
            assessment_str = assessment_str.encode('utf-8').decode('unicode-escape')  # This will print the returned string assessment
            
            # Display assessment
            st.subheader("Technical Skill Assessment")
            st.markdown(assessment_str)
        
        except Exception as e:
            st.error(f"Error: {e}")

# Run the Streamlit app
if __name__ == "__main__":
    main()
