"""Personal chef with OpenAI web search and this repository's .env settings.

Importing this script does not call the API. Run the file to ask the example question.
"""

from langchain.agents import create_agent
from langchain.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver

from lesson_support import make_model

system_prompt = """
You are a personal chef. The user will give you a list of ingredients
they have left over in their house.
Using the web search tool, search the web for recipes that can be made
with the ingredients they have. Cite the sources.
Return recipe suggestions and the recipe instructions if requested.
"""


def make_chef():
    """Create the agent without calling OpenAI; memory lasts for this process."""
    return create_agent(
        model=make_model(use_responses_api=True),
        tools=[{"type": "web_search"}],
        system_prompt=system_prompt,
        checkpointer=InMemorySaver(),
    )


if __name__ == "__main__":
    agent = make_chef()
    response = agent.invoke(
        {"messages": [HumanMessage(content="I have leftover chicken and rice. What can I make? Search the web.")]},
        {"configurable": {"thread_id": "chef-demo"}},
    )
    print(response["messages"][-1].text)
