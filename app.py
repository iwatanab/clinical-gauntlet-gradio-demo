import os
import gradio as gr
import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from models import Argument
from pipeline import run_pipeline
from examples.af_ich import CLAIM as DEFAULT_CLAIM, GOAL as DEFAULT_GOAL, PATIENT_FACTS as DEFAULT_PATIENT_FACTS

load_dotenv()


def submit(claim: str, goal: str, patient_facts: str, warrant: str, backing: str) -> tuple[dict, str, list]:
    if not claim.strip() or not goal.strip() or not patient_facts.strip():
        raise gr.Error("Claim, Goal, and Patient Facts are required.")
    argument = Argument(
        claim=claim,
        goal=goal,
        patient_facts=patient_facts,
        warrant=warrant if warrant.strip() else None,
        backing=backing if backing.strip() else None,
    )
    result = run_pipeline(argument)
    return result["tree"], result["recommendation"], result["references"]


with gr.Blocks(theme=gr.themes.Default()) as demo:
    gr.Markdown("# Clinical Gauntlet — Educational Demo")
    gr.Markdown(
        "> **Disclaimer:** This tool is for educational purposes only — outputs are AI-generated, may be inaccurate, and must not be used as a substitute for professional judgement in healthcare or any other domain."
    )
    with gr.Row():
        with gr.Column(scale=1):
            with gr.Group():
                claim = gr.Textbox(label="Claim *", lines=3, value=DEFAULT_CLAIM)
                goal = gr.Textbox(label="Goal *", lines=2, value=DEFAULT_GOAL)
                patient_facts = gr.Textbox(label="Patient Facts * ('Grounds' in Argumentation Theory)", lines=5, value=DEFAULT_PATIENT_FACTS)
                warrant = gr.Textbox(label="Warrant (Optional - Gauntlet will build this for you)", lines=2)
                backing = gr.Textbox(label="Backing (Optional - Gauntlet will build this for you)", lines=2)
        with gr.Column(scale=2):
            submit_btn = gr.Button("Submit", variant="primary")
            recommendation_output = gr.Textbox(label="Recommendation", lines=6, interactive=False)
            references_output = gr.JSON(label="References")
            tree_output = gr.JSON(label="Argument Tree")

    submit_btn.click(
        fn=submit,
        inputs=[claim, goal, patient_facts, warrant, backing],
        outputs=[tree_output, recommendation_output, references_output],
    )

app = FastAPI()

@app.get("/health")
def health():
    return JSONResponse({"status": "ok"})

app = gr.mount_gradio_app(app, demo, path="/")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 7860)))
