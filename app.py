import os
import gradio as gr
import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from models import Argument
from pipeline import run_pipeline

load_dotenv()

DEFAULT_CLAIM = "Anticoagulation should be initiated in this patient despite her recent gastrointestinal bleed."
DEFAULT_GROUNDS = (
    "76F. Diagnosed with non-valvular atrial fibrillation 3 weeks ago. "
    "CHA\u2082DS\u2082-VASc score 5 (age, sex, hypertension, diabetes, prior TIA). "
    "HAS-BLED score 4. GI bleed 8 weeks ago requiring 2-unit transfusion \u2014 "
    "source identified and endoscopically treated; hemoglobin now stable at 11.8\u202fg/dL "
    "with no recurrent bleeding. History of one prior GI bleed 3 years ago, managed conservatively. "
    "eGFR 58\u202fmL/min/1.73m\u00b2. Current medications: metformin, lisinopril, amlodipine. "
    "No prior anticoagulation. "
    "Cardiologist recommending DOAC initiation; gastroenterologist advising 3-month deferral."
)


def submit(claim: str, grounds: str, warrant: str, backing: str) -> tuple[dict, dict]:
    if not claim.strip() or not grounds.strip():
        raise gr.Error("Claim and Grounds are required.")
    argument = Argument(
        claim=claim,
        grounds=grounds,
        warrant=warrant if warrant.strip() else None,
        backing=backing if backing.strip() else None,
    )
    result = run_pipeline(argument)
    return result["claim"], result["contraclaim"]


with gr.Blocks(theme=gr.themes.Default()) as demo:
    gr.Markdown("# Clinical Gauntlet — Educational Demo")
    with gr.Row():
        with gr.Column():
            claim = gr.Textbox(label="Claim *", lines=3, value=DEFAULT_CLAIM)
            grounds = gr.Textbox(label="Grounds *", lines=5, value=DEFAULT_GROUNDS)
            warrant = gr.Textbox(label="Warrant (Optional - Gauntlet will build this for you)", lines=2)
            backing = gr.Textbox(label="Backing (Optional - Gauntlet will build this for you)", lines=2)
            submit_btn = gr.Button("Submit", variant="primary")
        with gr.Column():
            gr.Markdown(
                "> *The contraclaim is as important as the claim. A strong argument is judged not just by how well it supports its own claim, but by how well it addresses the strongest plausible opposing conclusion.*"
            )
            with gr.Row():
                claim_output = gr.JSON(label="Claim Argument")
                contra_output = gr.JSON(label="Contraclaim Argument")

    submit_btn.click(
        fn=submit,
        inputs=[claim, grounds, warrant, backing],
        outputs=[claim_output, contra_output],
    )

app = FastAPI()

@app.get("/health")
def health():
    return JSONResponse({"status": "ok"})

app = gr.mount_gradio_app(app, demo, path="/")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 7860)))
