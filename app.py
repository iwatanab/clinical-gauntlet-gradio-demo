import os
import gradio as gr
import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from models import Argument
from pipeline import run_pipeline
from examples.af_ich import CLAIM as DEFAULT_CLAIM, GOAL as DEFAULT_GOAL, GROUNDS as DEFAULT_GROUNDS

load_dotenv()


def submit(claim: str, goal: str, grounds: str, warrant: str, backing: str) -> tuple[str, str, str, list, dict]:
    if not claim.strip() or not goal.strip() or not grounds.strip():
        raise gr.Error("Claim, Goal, and Grounds are required.")
    argument = Argument(
        claim=claim,
        goal=goal,
        grounds=grounds,
        warrant=warrant if warrant.strip() else None,
        backing=backing if backing.strip() else None,
    )
    result = run_pipeline(argument)
    return result["verdict"], result["justification"], result["recommendation"], result["references"], result["tree"]


with gr.Blocks(theme=gr.themes.Default()) as demo:
    gr.Markdown("# Clinical Gauntlet — Educational Demo")
    gr.Markdown(
        "> **Disclaimer:** This tool is for educational purposes only — outputs are AI-generated, may be inaccurate, and must not be used as a substitute for professional judgement in healthcare or any other domain."
    )
    with gr.Row():
        with gr.Column(scale=1):
            with gr.Group():
                claim = gr.Textbox(label="Claim *", lines=3, value=DEFAULT_CLAIM,
                    info="The specific action or decision being argued for. "
                         "Like a verdict: narrow, falsifiable, one thing. "
                         "e.g. 'This patient should receive a blood thinner.'")
                goal = gr.Textbox(label="Goal *", lines=2, value=DEFAULT_GOAL,
                    info="The outcome you are trying to achieve — the 'why bother' behind the claim. "
                         "Like a judge asking 'what are you trying to accomplish?' "
                         "e.g. 'Prevent a stroke.'")
                grounds = gr.Textbox(label="Grounds *", lines=5, value=DEFAULT_GROUNDS,
                    info="The specific facts of this case from which the claim is drawn, independent of whether the warrant is accepted — "
                         "e.g. irregular heartbeat, prior stroke, clotting risk score of 6.")
                warrant = gr.Textbox(label="Warrant (Optional)", lines=2,
                    info="A general authorisation that bridges patient facts to claim — "
                         "e.g. 'Patients with an irregular heartbeat and a clotting risk score ≥2 should receive a blood thinner.' "
                         "Gauntlet will derive this from guidelines if left blank.")
                backing = gr.Textbox(label="Backing (Optional)", lines=2,
                    info="The body of established evidence that certifies the warrant is sound — "
                         "e.g. ACC/AHA atrial fibrillation guidelines, ARISTOTLE trial. "
                         "Gauntlet will retrieve this from authoritative sources if left blank.")
        with gr.Column(scale=2):
            submit_btn = gr.Button("Submit", variant="primary")
            verdict_output = gr.Textbox(label="Verdict", lines=1, interactive=False)
            justification_output = gr.Textbox(label="Justification", lines=4, interactive=False)
            recommendation_output = gr.Textbox(label="Recommendation", lines=6, interactive=False)
            references_output = gr.JSON(label="References")
            tree_output = gr.JSON(label="Argument Tree")

    submit_btn.click(
        fn=submit,
        inputs=[claim, goal, grounds, warrant, backing],
        outputs=[verdict_output, justification_output, recommendation_output, references_output, tree_output],
    )

app = FastAPI()

@app.get("/health")
def health():
    return JSONResponse({"status": "ok"})

app = gr.mount_gradio_app(app, demo, path="/")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 7860)))
