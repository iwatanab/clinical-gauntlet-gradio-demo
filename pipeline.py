from models import Argument


def run_pipeline(argument: Argument) -> dict:
    # TODO: Agent 1 - Researcher (OpenRouter LLM + Tavily web search)
    # TODO: Agent 2 - Analyst
    # TODO: Agent 3 - Synthesizer
    return argument.model_dump()
