import os
import asyncio
from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

class MCPAdapter:
    """Manages the lifecycle of an MCP STDIO server and exposes its tools to LangChain/LangGraph."""
    
    def __init__(self):
        self.github_token = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN", "")
        # Copy env to ensure npx/node can be found
        env = os.environ.copy()
        env["GITHUB_PERSONAL_ACCESS_TOKEN"] = self.github_token
        
        self.server_params = StdioServerParameters(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-github"],
            env=env
        )

    async def run_tool(self, tool_name: str, arguments: dict) -> str:
        """Helper to invoke a single tool via a new session."""
        try:
            async with stdio_client(self.server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.call_tool(tool_name, arguments)
                    
                    # Assuming text content response for these tools
                    if result.content and len(result.content) > 0:
                        return result.content[0].text
                    return "Success (No output)"
        except Exception as e:
            return f"Error executing {tool_name}: {e}"

# --- Explicit Pydantic Schemas for the key GitHub tools needed for context ---

class GetFileContentsInput(BaseModel):
    owner: str = Field(description="Repository owner (username or organization)")
    repo: str = Field(description="Repository name")
    path: str = Field(description="Path to the file or directory")
    branch: str = Field(None, description="Optional branch or commit SHA")

class GetPullRequestInput(BaseModel):
    owner: str = Field(description="Repository owner")
    repo: str = Field(description="Repository name")
    pullNumber: int = Field(description="Pull request number")
    method: str = Field(
        default="get_diff", 
        description="Must be 'get_diff' or 'get_files' or 'get_comments'"
    )

class ListCommitsInput(BaseModel):
    owner: str = Field(description="Repository owner")
    repo: str = Field(description="Repository name")
    sha: str = Field(None, description="Branch name or commit SHA to list from")

class ListIssuesInput(BaseModel):
    owner: str = Field(description="Repository owner")
    repo: str = Field(description="Repository name")
    
# --- LangChain Tool Constructors ---

def get_mcp_tools() -> list[StructuredTool]:
    """Returns a list of explicitly typed LangChain tools wrapping the Github MCP."""
    adapter = MCPAdapter()
    
    async def get_file_contents_func(owner: str, repo: str, path: str, branch: str = None) -> str:
        args = {"owner": owner, "repo": repo, "path": path}
        if branch:
            args["ref"] = branch
        return await adapter.run_tool("get_file_contents", args)
        
    async def get_pr_func(owner: str, repo: str, pullNumber: int, method: str = "get_diff") -> str:
        args = {"owner": owner, "repo": repo, "pullNumber": pullNumber, "method": method}
        return await adapter.run_tool("pull_request_read", args)
        
    async def list_commits_func(owner: str, repo: str, sha: str = None) -> str:
        args = {"owner": owner, "repo": repo}
        if sha:
            args["sha"] = sha
        return await adapter.run_tool("list_commits", args)

    async def list_issues_func(owner: str, repo: str) -> str:
        args = {"owner": owner, "repo": repo}
        return await adapter.run_tool("list_issues", args)

    return [
        StructuredTool.from_function(
            coroutine=get_file_contents_func,
            name="github_get_file_contents",
            description="Fetch file contents from a remote GitHub repository.",
            args_schema=GetFileContentsInput
        ),
        StructuredTool.from_function(
            coroutine=get_pr_func,
            name="github_read_pull_request",
            description="Read a pull request diff, files, or comments from a remote GitHub repository.",
            args_schema=GetPullRequestInput
        ),
        StructuredTool.from_function(
            coroutine=list_commits_func,
            name="github_list_commits",
            description="List recent commits for a GitHub repository.",
            args_schema=ListCommitsInput
        ),
        StructuredTool.from_function(
            coroutine=list_issues_func,
            name="github_list_issues",
            description="List active issues in a remote GitHub repository.",
            args_schema=ListIssuesInput
        )
    ]
